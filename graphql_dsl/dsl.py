from collections import defaultdict
from enum import Enum
from typing import NamedTuple, Type, Any, Union, Callable, Mapping, Tuple, get_type_hints, Iterable, Optional

import inflection
from pyrsistent import pmap, pvector
from pyrsistent.typing import PMap, PVector
from typeit.combinator.constructor import _TypeConstructor, TypeConstructor, flags

from infix import or_infix as infix
from infix import mul_infix

from typeit.parser import inner_type_boundaries
from typeit.utils import get_global_name_overrider
from .translator import *
from .types import NewIDType


__all__ = (
    'QUERY',
    'WITH',
    'PASS',
    'TO',
    'AS',
    'MUTATION',
    'GQL',
)


class _NamedTupleType(NamedTuple):
    property_field: Any


PropertyField = type(_NamedTupleType.property_field)


GQL_SCALARS: Mapping[Type[Any], str] = {
    str: 'String',
    int: 'Int',
    float: 'Float',
    bool: 'Boolean',
}


_DefaultTyper = TypeConstructor & NewIDType & flags.GlobalNameOverride(
    lambda x: inflection.camelize(x, uppercase_first_letter=False)
)


# NamedTuples allow natural field referencing via its field getters,
# whereas dataclasses lack this ability, but we provide
# a conventional pair of (DataClassType, filed_name) for the same purpose.
FieldReference = Union[property, Tuple[Type[Any], str]]


class Binding(NamedTuple):
    input_field: FieldReference
    expr_field: FieldReference
    variable_alias: Optional[str] = None

    def __and__(self, other: 'Binding') -> 'BindComb':
        return BindComb(pvector([self, other]))


class BindComb(NamedTuple):
    """ Binding combinator
    """
    bindings: PVector[Binding] = pvector()


class Unit(NamedTuple):
    pass


class QueryType(Enum):
    QUERY = 'query'
    MUTATION = 'mutation'


class Expr(NamedTuple):
    """ Expression combinator
    """
    type: QueryType = QueryType.QUERY
    input: Type[Any] = Unit
    query: Type[Any] = Unit
    bindings: PVector[Binding] = pvector()


class ResolvedBinding(NamedTuple):
    input_attr_name: str
    attr_name: str
    type_name: str
    is_optional: bool


class GraphQLQuery(NamedTuple):
    query: str
    get_input_vars: Callable[..., Mapping[str, Any]]


class GraphQLQueryConstructor(NamedTuple):
    query_types: PMap[Type[Any], Any] = pmap()
    typer: _TypeConstructor = _DefaultTyper

    def __call__(self, expr: 'Expr') -> GraphQLQuery:
        mk_input_vars, dict_input_vars = self.typer ^ expr.input
        bindings = self.prepare_bindings(expr)
        query_decl = expr.type.value
        query_body = translate(expr.query, bindings, self.typer)
        return GraphQLQuery(
            query=f'{query_decl} {query_body}',
            get_input_vars=dict_input_vars,
        )

    def prepare_bindings(self, expr: Expr) -> Mapping[str, Iterable[ResolvedBinding]]:
        rv = defaultdict(list)
        for binding in expr.bindings:
            resolved_input = self.resolve_binding(expr.input, binding.input_field, binding.variable_alias)
            resolved_expr  = self.resolve_binding(expr.query, binding.expr_field, binding.variable_alias)
            rv[resolved_expr.attr_name].append(resolved_input)
        return rv

    def resolve_binding(self, typ: Type[Any], field: FieldReference, alias: Optional[str]) -> ResolvedBinding:
        if isinstance(field, PropertyField):
            # NamedTuple
            for field_name, field_type in get_type_hints(typ).items():
                if getattr(typ, field_name) is field:
                    name = field_name
                    variable_python_type = field_type
                    break
            else:
                raise TypeError(f"Couldn't find a field of alias \"{alias}\" in {typ}")

        elif isinstance(field, tuple):
            # dataclass
            if typ is not field[0]:
                raise TypeError(f'Field {field[0]} should be an attribute of {typ}')
            name = field[1]
            variable_python_type = get_type_hints(field[0])[name]
        else:
            raise NotImplementedError(f'Unknown field type for {field}: {type(field)}')
        overrider = get_global_name_overrider(self.typer.overrides)
        attr_name = overrider(name)
        is_optional = type(None) in inner_type_boundaries(variable_python_type)
        type_name = GQL_SCALARS.get(variable_python_type, variable_python_type.__name__)
        return ResolvedBinding(attr_name=overrider(name),
                               input_attr_name=alias if alias else attr_name,
                               type_name=type_name,
                               is_optional=is_optional)



class Query(NamedTuple):
    """ This is a helper combinator that only has an infix form and makes sure
    that the result of its application is ``Expr``.
    """
    type: QueryType

    def __or__(self, other: Union[Type[Any], Expr]) -> Expr:
        if isinstance(other, Expr):
            return other._replace(type=self.type)
        return Expr(type=self.type, query=other)


QUERY = Query(QueryType.QUERY)
MUTATION = Query(QueryType.MUTATION)


@infix
def WITH(a: Expr, b: Type[Any]) -> Expr:
    """ a | WITH | b
    """
    return a._replace(input=b)


@infix
def PASS(a: Expr, b: Union[BindComb, Binding]) -> Expr:
    if isinstance(b, Binding):
        return a._replace(bindings=a.bindings.append(b))
    return a._replace(bindings=a.bindings.extend(b.bindings))

@mul_infix
def TO(a: property, b: property) -> Binding:
    """ Input.field * TO * Query.field
    """
    return Binding(input_field=a, expr_field=b)

@mul_infix
def AS(a: Binding, b: str) -> Binding:
    """ Defines the input attribute name of the binding.

    ``a * AS * b`` means ``attribute (b: $a) { ... }``
    """
    return a._replace(variable_alias=b)


GQL = GraphQLQueryConstructor()