from typing import Type, Any, Generator, Mapping

from typeit import TypeConstructor
from typeit.tokenizer import iter_tokens, Token


translate_begin_type = lambda x: f'{x.python_name} {{'
translate_begin_type_inner = lambda x: '{'
translate_end_type = lambda x: '}'
translate_begin_attribute = lambda x: f'{x.wire_name}'
translate_end_attribute = lambda x: ' '


translation_map: Mapping[Token, str] = {
    Token.BeginType: translate_begin_type,
    Token.EndType: translate_end_type,
    Token.BeginAttribute: translate_begin_attribute,
    Token.EndAttribute: translate_end_attribute,
}


def translate_tokens_to_graphql(typ: Type[Any]) -> Generator[str, None, None]:
    """ for graphql queries BeginType should be translated only once - for the topmost type
    """
    query_type_began = False
    for token in iter_tokens(typ, typer=TypeConstructor):
        for token_type, do_translate in translation_map.items():
            if isinstance(token, token_type):
                if token_type is Token.BeginType:
                    if query_type_began:
                        yield translate_begin_type_inner(token)
                    else:
                        query_type_began = True
                        yield do_translate(token)
                else:
                    yield do_translate(token)
                break
        else:
            raise ValueError(f'Unhandled token: {token}')


def translate(typ: Type[Any]) -> str:
    return ''.join(translate_tokens_to_graphql(typ))
