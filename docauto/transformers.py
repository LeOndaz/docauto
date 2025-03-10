import logging
from abc import abstractmethod
from typing import Generic, Optional, TypeVar, Union

import libcst as cst

from docauto.generator import BaseDocsGenerator, GenerationError
from docauto.models import LLMDocstringResponse
from docauto.parsers import LLMResponseParser
from docauto.tracker import BaseProgressTracker, ProgressTracker

T = TypeVar('T')
Node = Union[cst.FunctionDef, cst.ClassDef]


class BaseDocTransformer(cst.CSTTransformer, Generic[T]):
    """Abstract base class for document transformation.

    Defines the interface for transforming Python source code to add or update docstrings.
    Implementations should handle the generation and insertion of docstrings for classes
    and functions while maintaining proper formatting and tracking progress.
    """

    def __init__(
        self,
        generator: BaseDocsGenerator,
        parser: LLMResponseParser[T],
        logger: Optional[logging.Logger] = None,
        overwrite: Optional[bool] = True,
        progress_tracker: Optional[BaseProgressTracker] = None,
    ):
        """Initialize the transformer with required components.

        Args:
            generator: Component that generates docstring content
            parser: Component that parses LLM responses into docstrings
            logger: Logger for tracking transformation progress
            overwrite: Whether to overwrite existing docstrings
            progress_tracker: Component for tracking transformation progress

        Raises:
            TypeError: If any parameter has an invalid type
        """
        if not isinstance(generator, BaseDocsGenerator):
            raise TypeError(
                f'generator must be a BaseDocsGenerator instance, got {type(generator).__name__}'
            )
        if not isinstance(parser, LLMResponseParser):
            raise TypeError(
                f'parser must be a LLMResponseParser instance, got {type(parser).__name__}'
            )
        if logger is not None and not isinstance(logger, logging.Logger):
            raise TypeError(
                f'logger must be a Logger instance or None, got {type(logger).__name__}'
            )
        if not isinstance(overwrite, bool):
            raise TypeError(
                f'overwrite must be a boolean, got {type(overwrite).__name__}'
            )
        if progress_tracker is not None and not isinstance(
            progress_tracker, BaseProgressTracker
        ):
            raise TypeError(
                f'progress_tracker must be a BaseProgressTracker instance or None, got {type(progress_tracker).__name__}'
            )

        self.parser = parser
        self.generator = generator
        self.logger = logger or logging.getLogger('docauto')
        self.overwrite = overwrite
        self.progress_tracker = progress_tracker or ProgressTracker(self.logger)
        super().__init__()

    def visit_ClassDef(self, node: cst.ClassDef) -> None:
        """Visit a class definition node during traversal."""
        self.progress_tracker.track_object('current_file', node, 'pending')

    def leave_ClassDef(
        self, original_node: cst.ClassDef, updated_node: cst.ClassDef
    ) -> cst.ClassDef:
        return self._process_node(original_node, updated_node)

    def visit_FunctionDef(self, node: cst.FunctionDef) -> None:
        """Visit a function definition node during traversal."""
        self.progress_tracker.track_object('current_file', node, 'pending')

    def leave_FunctionDef(
        self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> cst.FunctionDef:
        return self._process_node(original_node, updated_node)

    def _process_node(
        self,
        original_node: Node,
        updated_node: Node,
    ) -> Node:
        """Process a node (function/class) to add or update its docstring.

        Args:
            original_node: The original node before processing
            updated_node: The node to be updated with docstring

        Returns:
            The processed node with updated docstring
        """
        if self.needs_docstring(updated_node):
            try:
                llm_response = self.generate_docstring(updated_node)
                updated_node = self.insert_docstring(
                    original_node, updated_node, llm_response
                )
            except GenerationError as e:
                self.logger.error(
                    f'documentation failed: is the API reacheable?{e}',
                    exc_info=True,
                )
                self.progress_tracker.track_object(
                    'current_file', updated_node, 'failed'
                )
                return original_node
            except Exception as e:
                self.logger.error(
                    '%s documentation failed: %s',
                    type(updated_node).__name__,
                    str(e),
                    exc_info=True,
                )
                self.progress_tracker.track_object(
                    'current_file', updated_node, 'failed'
                )
                return original_node

        self.progress_tracker.track_object('current_file', updated_node, 'processed')
        return updated_node

    def _node_has_docstring(self, node: Node) -> bool:
        """Check if node (function/class) already has a docstring"""
        return any(
            isinstance(stmt, cst.SimpleStatementLine)
            and any(
                isinstance(expr, cst.Expr) and isinstance(expr.value, cst.SimpleString)
                for expr in stmt.body
            )
            for stmt in node.body.body
        )

    def needs_docstring(self, node: Node) -> bool:
        """Determine if node needs docstring"""
        has_docstring = self._node_has_docstring(node)
        return self.overwrite if has_docstring else True

    def generate_docstring(self, node: Node = None, context: str = None) -> str:
        """Generate a docstring for the given node."""

        # TODO remove the original docstring
        source = cst.Module([]).code_for_node(node)
        return self.generator.generate(source=source, context=context)

    def match_existing_quotes_style(
        self,
        node: Node,
    ) -> str:
        """Determine the quote style used in the existing docstring"""
        for stmt in node.body.body:
            if isinstance(stmt, cst.SimpleStatementLine):
                for expr in stmt.body:
                    if isinstance(expr, cst.Expr) and isinstance(
                        expr.value, cst.SimpleString
                    ):
                        # Extract the quote style from the existing docstring
                        docstring = expr.value.value
                        if docstring.startswith('"""'):
                            return '"""'
                        elif docstring.startswith("'''"):
                            return "'''"
        # Default to triple double quotes if no existing docstring
        return '"""'

    def get_default_indent_chars(self):
        return '\t'

    def get_default_quotes(self):
        """
        This will come in handy if you have a formatter, this is where you
        read the formatter configuration and match its styling.
        """
        return '"""'

    @abstractmethod
    def format_docstring(
        self,
        llm_response: T,
        original_node: Node = None,
        updated_node: Node = None,
    ) -> str:
        """Format docstring with proper quote style and indentation.

        Args:
            docstring: The docstring content to format
            node: The node being documented, used for quote style matching when overwriting

        Returns:
            The formatted docstring with proper quote style and indentation
        """
        raise NotImplementedError

    def indent_text(self, text: str, spaces: int = 4, ignore_first_line=True) -> str:
        """Indent each line of the given text by specified number of spaces.

        Args:
            text: The text to indent
            spaces: Number of spaces to indent by
            ignore_first_line: Whether to skip indenting the first line

        Returns:
            The indented text with each line indented by specified spaces
        """
        if spaces < 0:
            raise ValueError('indent spacing must be a positive integer')

        if spaces == 0:
            return text

        lines = text.splitlines(keepends=True)
        indent = ' ' * spaces

        # Process each line while preserving empty lines and existing indentation
        indented_lines = []
        for i, line in enumerate(lines):
            if ignore_first_line and i == 0:
                indented_lines.append(line)
            else:
                indented_lines.append(indent + line if line.strip() else line)

        return ''.join(indented_lines)

    @abstractmethod
    def insert_docstring(
        self,
        original_node: Node,
        updated_node: Node,
        llm_response: T,
    ) -> Node:
        """Insert or replace a docstring in a node."""


class DocTransformer(BaseDocTransformer[LLMDocstringResponse]):
    def insert_docstring(
        self,
        original_node: Node,
        updated_node: Node,
        llm_response,
    ) -> Node:
        """Insert or replace docstring in a function/class definition with proper indentation"""
        if not updated_node:
            updated_node = original_node

        # If not overwriting and docstring exists, return unchanged
        if not self.overwrite and self._node_has_docstring(updated_node):
            return updated_node

        llm_response = self.parser.parse(llm_response)

        if len(llm_response.responses) == 0:
            self.logger.error(f'No response found for {updated_node}')
            return

        docstring = self.format_docstring(llm_response, updated_node)

        # Create the docstring node with proper formatting
        doc_node = cst.SimpleStatementLine(
            body=[cst.Expr(value=cst.SimpleString(docstring))]
        )

        # Filter out existing docstring if overwriting
        filtered_body = (
            [
                stmt
                for stmt in updated_node.body.body
                if not (
                    isinstance(stmt, cst.SimpleStatementLine)
                    and any(
                        isinstance(expr, cst.Expr)
                        and isinstance(expr.value, cst.SimpleString)
                        for expr in stmt.body
                    )
                )
            ]
            if self.overwrite
            else list(updated_node.body.body)
        )

        # Add docstring at the beginning
        new_body = [doc_node] + filtered_body
        return updated_node.with_changes(
            body=updated_node.body.with_changes(body=new_body)
        )

    def format_docstring(
        self,
        llm_response,
        original_node=None,
        updated_node=None,
    ) -> str:
        """Format docstring with proper quote style and indentation.

        Args:
            docstring: The docstring content to format
            node: The node being documented, used for quote style matching when overwriting

        Returns:
            The formatted docstring with proper quote style and indentation
        """

        if self.logger.level == logging.DEBUG:
            response_json = llm_response.model_dump_json(indent=4)
            self.logger.debug(response_json)

        response = llm_response.responses[0]
        docstring = response.content
        should_indent_first_line = response.should_indent_first_line
        should_indent = response.should_indent

        if should_indent:
            docstring = self.indent_text(
                docstring,
                4,
                not should_indent_first_line,
            )

        quote_style = (
            self.match_existing_quotes_style(original_node)
            if self.overwrite
            else self.get_default_quotes()
        )

        should_add_newline_at_the_end = response.should_add_newline_at_the_end
        newline_at_the_end = '\n\t' if should_add_newline_at_the_end else ''

        return f'{quote_style}{docstring}{newline_at_the_end}{quote_style}'
