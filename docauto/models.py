from typing import List

from pydantic import BaseModel, Field


class LLMDocstringSingleResponse(BaseModel):
    """Structured output model for a single LLM-generated docstring"""

    content: str = Field(description='The generated docstring content')
    format: str = Field(
        default='sphinx',
        description='The format of the docstring (e.g. sphinx, google)',
    )
    should_indent: bool = Field(
        default=False,
        description=(
            'This is True if the parser should indent the whole text, False otherwise. '
            'this is False if the assistant added the spacing'
        ),
    )
    should_indent_first_line: bool = Field(
        default=False,
        description=(
            'This is True if the parser should indent the first line, False otherwise '
            'this is False if the assistant added the spacing'
        ),
    )
    should_add_newline_at_the_end: bool = Field(
        default=False,
        description=(
            'This is true if the parser should add a new line at the end of the text, before the quotes, false otherwise.'
            'this is False if the assistant added the spacing'
            "New lines need only to be added if the response doesn't span a full line. "
            'Oneliners less than 88 characters or single sentences should not end with a newline.'
        ),
    )

    # # for debbuging
    # why_should_indent: str = Field(
    #     description=(
    #         "Why should I indent explain with example on the data you've received"
    #     ),
    # )
    # why_should_add_newline_at_the_end: str = Field(
    #     description=(
    #         'Why should I add a newline? '
    #         "explain with example on the data you've received"
    #     ),
    # )


class LLMDocstringResponse(BaseModel):
    """Container model for multiple LLM-generated docstrings"""

    responses: List[LLMDocstringSingleResponse] = Field(
        description='List of generated docstring responses'
    )
