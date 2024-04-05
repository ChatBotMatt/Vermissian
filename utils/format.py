from typing import Union

def strikethrough(value: Union[int, str]) -> str:
    return f'~~{value}~~'

def bold(value: Union[int, str]) -> str:
    return f'**{value}**'

def underline(value: Union[int, str]) -> str:
    return f'__{value}__'

def code(value: Union[int, str]) -> str:
    return f'`{value}`'

def multiline_code(value: Union[int, str]) -> str:
    return f'```{value}```'

def italics(value: Union[int, str]) -> str:
    return f'*{value}*'

def quote(value: Union[int, str]) -> str:
    return f'> {value}'

def bullet(value: Union[int, str]) -> str:
    return f'* {value}'