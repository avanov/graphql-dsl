from itertools import chain
from typing import Type, Any, Generator, Mapping, Callable

from typeit.combinator.constructor import _TypeConstructor
from typeit.tokenizer import iter_tokens, Token, BeginType, EndType, BeginAttribute, EndAttribute

__all__ = (
    'translate',
)


def translate_begin_type(x: Token, bindings: Mapping[Any, Any]) -> str:
    if bindings:
        all_bindings = chain.from_iterable(bindings.values())
        vars = ','.join(f'${x.attr_name}:{x.type_name}{"" if x.is_optional else "!"}' for x in all_bindings)
        vars = f'({vars})'
    else:
        vars = ''
    return f'{x.python_name}{vars}{{'


def translate_begin_type_inner(x: Token, bindings: Mapping[Any, Any]) -> str:
    return '{'


def translate_end_type(x: Token, bindings: Mapping[Any, Any]) -> str:
    return '}'


def translate_begin_attribute(x: Token, bindings: Mapping[Any, Any]) -> str:
    try:
        vars = bindings[x.wire_name]
    except KeyError:
        vars = ()

    expr = ','.join(f'{v.input_attr_name}:${v.attr_name}' for v in vars)
    if expr:
        expr = f'({expr})'

    return f'{x.wire_name}{expr}'


def translate_end_attribute(x: Token, bindings: Mapping[Any, Any]) -> str:
    return ''


def translate_toplevel_declaration(x: BeginType, bindings: Mapping[Any, Any]) -> str:
    return '{'


translation_map: Mapping[Token, Callable[[Token, Mapping[Any, Any]], str]] = {
    BeginType: translate_begin_type,
    EndType: translate_end_type,
    BeginAttribute: translate_begin_attribute,
    EndAttribute: translate_end_attribute,
}


def translate_tokens_to_graphql(
    typ: Type[Any],
    bindings: Mapping[Any, Any],
    typer: _TypeConstructor,
) -> Generator[str, None, None]:
    """ for graphql queries BeginType should be translated only once - for the topmost type
    """
    query_type_began = False
    previous_token_pair = (None, None)
    for token in iter_tokens(typ, typer=typer):
        for token_type, do_translate in translation_map.items():
            if isinstance(token, token_type):
                if token_type is BeginType:
                    if query_type_began:
                        yield translate_begin_type_inner(token, bindings)
                    else:
                        query_type_began = True
                        yield do_translate(token, bindings)
                elif token_type is BeginAttribute:
                    # A simple tracking of whether space is necessary between
                    # this attribute and the previous token.
                    # (EndAttribute, BeginAttribute) indicates two subsequent attributes
                    # that require space between them, whereas
                    # (EndAttribute, EndType) indicates a case of "previous_attribute}current_attribute{"
                    # where space is not required as there's a curly brace separator
                    if previous_token_pair == (EndAttribute, BeginAttribute):
                        yield ' '
                    yield do_translate(token, bindings)
                else:
                    yield do_translate(token, bindings)

                previous_token_pair = (type(token), previous_token_pair[0])
                break
        else:
            raise ValueError(f'Unhandled token: {token}')


def translate(typ: Type[Any], bindings: Mapping[Any, Any], typer: _TypeConstructor) -> str:
    return ''.join(translate_tokens_to_graphql(typ, bindings, typer))
