import logging
from typing import Optional, Union

import libcst as cst

from docugen.tracker import BaseProgressTracker, ProgressTracker


class DocTransformer(cst.CSTTransformer):
    def __init__(
        self,
        generator,
        parser,
        logger: logging.Logger = None,
        overwrite=True,
        progress_tracker: Optional[BaseProgressTracker] = None,
    ):
        super().__init__()
        self.parser = parser
        self.generator = generator
        self.current_class: Optional[str] = None
        self.logger = logger or logging.getLogger('docugen')
        self.overwrite = overwrite
        self.progress_tracker = progress_tracker or ProgressTracker(self.logger)

    def visit_ClassDef(self, node: cst.ClassDef) -> None:
        self.current_class = node.name.value
        self.progress_tracker.track_object('current_file', node, 'pending')

    def visit_FunctionDef(self, node: cst.FunctionDef) -> None:
        self.progress_tracker.track_object('current_file', node, 'pending')

    def _process_node(self, original_node: Union[cst.FunctionDef, cst.ClassDef], updated_node: Union[cst.FunctionDef, cst.ClassDef]) -> Union[cst.FunctionDef, cst.ClassDef]:
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
                docstring = self.parser(llm_response)
                updated_node = self.insert_docstring(updated_node, docstring)
            except Exception as e:
                self.logger.error('%s documentation failed: %s', type(updated_node).__name__, str(e))
                self.progress_tracker.track_object(
                    'current_file', updated_node, 'failed'
                )
                return original_node

        self.progress_tracker.track_object('current_file', updated_node, 'processed')
        return updated_node

    def leave_FunctionDef(
        self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> cst.FunctionDef:
        return self._process_node(original_node, updated_node)

    def leave_ClassDef(
        self, original_node: cst.ClassDef, updated_node: cst.ClassDef
    ) -> cst.ClassDef:
        return self._process_node(original_node, updated_node)

    def _node_has_docstring(self, node: Union[cst.FunctionDef, cst.ClassDef]) -> bool:
        """Check if node (function/class) already has a docstring"""
        return any(
            isinstance(stmt, cst.SimpleStatementLine)
            and any(
                isinstance(expr, cst.Expr) and isinstance(expr.value, cst.SimpleString)
                for expr in stmt.body
            )
            for stmt in node.body.body
        )

    def needs_docstring(self, node: Union[cst.FunctionDef, cst.ClassDef]) -> bool:
        """Determine if node needs docstring"""
        has_docstring = self._node_has_docstring(node)
        return self.overwrite if has_docstring else True

    def generate_docstring(self, node: Union[cst.FunctionDef, cst.ClassDef]) -> str:
        source = cst.Module([]).code_for_node(node)
        context = f'Class: {self.current_class}' if self.current_class else None
        return self.generator.generate(source=source, additional_context=context)

    def match_existing_quotes_style(
        self, node: Union[cst.FunctionDef, cst.ClassDef]
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

    def format_docstring(
        self,
        docstring: str,
        node: Optional[Union[cst.FunctionDef, cst.ClassDef]] = None,
    ) -> str:
        """Format docstring with proper quote style and indentation.

        Args:
            docstring: The docstring content to format
            node: The node being documented, used for quote style matching when overwriting

        Returns:
            The formatted docstring with proper quote style and indentation
        """
        docstring = self.indent_text(docstring, 4)
        quote_style = (
            self.match_existing_quotes_style(node) if self.overwrite else '"""'
        )
        return f'{quote_style}\n{docstring}\n{quote_style}'

    def insert_docstring(
        self,
        node: Union[cst.FunctionDef, cst.ClassDef],
        docstring: str,
    ) -> Union[cst.FunctionDef, cst.ClassDef]:
        """Insert or replace docstring in a function/class definition with proper indentation"""

        # If not overwriting and docstring exists, return unchanged
        if not self.overwrite and self._node_has_docstring(node):
            return node

        # Process the docstring
        docstring = self.format_docstring(docstring, node)

        # Create the docstring node with proper formatting
        doc_node = cst.SimpleStatementLine(
            body=[cst.Expr(value=cst.SimpleString(docstring))]
        )

        # Filter out existing docstring if overwriting
        filtered_body = (
            [
                stmt
                for stmt in node.body.body
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
            else list(node.body.body)
        )

        # Add docstring at the beginning
        new_body = [doc_node] + filtered_body
        return node.with_changes(body=node.body.with_changes(body=new_body))

    def indent_text(self, text: str, spaces: int = 4, ignore_first_line=True) -> str:
        """Indent each line of the given text by specified number of spaces.

        Args:
            text: The text to indent
            spaces: Number of spaces to indent by

        Returns:
            The indented text with each line indented by specified spaces
        """
        # Split into lines, preserve empty lines
        lines = text.splitlines()

        # Create indent string
        indent = ' ' * spaces

        # Indent each line, preserving empty lines
        indented_lines = []
        for i, line in enumerate(lines):
            if ignore_first_line and i == 0:
                indented_lines.append(line)
            else:
                indented_lines.append(indent + line if line.strip() else line)

        # Join back together
        return '\n'.join(indented_lines)
