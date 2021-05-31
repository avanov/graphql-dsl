from collections import defaultdict
from enum import Enum
from typing import NamedTuple, Type, Any, Union, Callable, Mapping, Tuple, get_type_hints, Iterable, Optional, TypeVar

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
    'MUTATE',
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

    def __and__(self, other: Union['Binding', 'BindComb']) -> 'BindComb':
        if isinstance(other, BindComb):
            return BindComb(pvector([self]).extend(other.bindings))
        elif isinstance(other, Binding):
            return BindComb(pvector([self, other]))
        raise NotImplementedError('Binding???')


class BindComb(NamedTuple):
    """ Binding combinator
    """
    bindings: PVector[Binding] = pvector()

    def __and__(self, other: Union['Binding', 'BindComb']) -> 'BindComb':
        if isinstance(other, BindComb):
            return self._replace(bindings=self.bindings.extend(other.bindings))
        elif isinstance(other, Binding):
            return self._replace(bindings=self.bindings.append(other))
        raise NotImplementedError('BindComb???')


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


T = TypeVar('T')


class GraphQLQuery(NamedTuple):
    query: str
    name: str
    get_input_vars: Callable[[T], Mapping[str, Any]]
    get_result: Callable[[Mapping[str, Any]], Any]

    def request_payload(self, query_input: Optional[T] = None) -> Mapping[str, Any]:
        in_ = self.get_input_vars(query_input) if query_input else {}
        return { "operationName": self.name
               , "variables":     in_
               , "query":         self.query
               }


class GraphQLQueryConstructor(NamedTuple):
    query_types: PMap[Type[Any], Any] = pmap()
    typer: _TypeConstructor = _DefaultTyper

    def __call__(self, expr: 'Expr') -> GraphQLQuery:
        mk_input_vars, dict_input_vars = self.typer ^ expr.input
        mk_result, dict_result = self.typer ^ expr.query
        bindings = self.prepare_bindings(expr)
        query_decl = expr.type.value
        query_body = translate(expr.query, bindings, self.typer)
        return GraphQLQuery(
            name=expr.query.__name__,
            query=f'{query_decl} {query_body}',
            get_input_vars=dict_input_vars,
            get_result=lambda x: mk_result(x['data']),
        )

    def prepare_bindings(self, expr: Expr) -> Mapping[str, Iterable[ResolvedBinding]]:
        rv = defaultdict(list)
        for binding in expr.bindings:
            resolved_input = self.resolve_binding(expr.input, binding.input_field, binding.variable_alias)
            try:
                resolved_expr  = self.resolve_binding(expr.query, binding.expr_field, binding.variable_alias)
            except AttrNotFound:
                for typ in self.typer.memo.keys():
                    try:
                        resolved_expr  = self.resolve_binding(typ, binding.expr_field, binding.variable_alias)
                    except (AttributeError, TypeError, AttrNotFound):
                        continue
                    else:
                        break
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
                raise AttrNotFound(f"Couldn't find a field of alias \"{alias}\" in {typ}")

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
        try:
            type_name = GQL_SCALARS.get(variable_python_type, variable_python_type.__name__)
        except AttributeError:
            type_name = ''
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


QUERY  = Query(QueryType.QUERY)
MUTATE = Query(QueryType.MUTATION)


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


class AttrNotFound(TypeError):
    pass