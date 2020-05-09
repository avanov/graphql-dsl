import requests
import vcr
from typing import NamedTuple, Sequence, Mapping, Generator, Type, Any

from graphql_dsl.translator import translate
from tests.paths import VCR_FIXTURES_PATH
from typeit import TypeConstructor
from typeit.tokenizer import iter_tokens, Token


def test_tokenizer():

    class Language(NamedTuple):
        code: str
        name: str

    class Country(NamedTuple):
        code: str
        name: str
        languages: Sequence[Language]

    class CountriesQuery(NamedTuple):
        countries: Sequence[Country]


    mk_countries_query, dict_countries_query = TypeConstructor  ^ CountriesQuery

    graphql_query = translate(CountriesQuery)
    assert graphql_query
    graphql_query = f'query {graphql_query}'

    with vcr.use_cassette(str(VCR_FIXTURES_PATH / 'countries.yaml')):
        response = requests.post(
            url='https://countries.trevorblades.com/',
            json={
                "operationName": f"{CountriesQuery.__name__}",
                "variables": {},
                "query": graphql_query,
            },
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Origin': 'https://countries.trevorblades.com',
            }
        )
    response.raise_for_status()
    data = response.json()['data']
    assert data
    typed_data = mk_countries_query(data)
    assert isinstance(typed_data, CountriesQuery)

