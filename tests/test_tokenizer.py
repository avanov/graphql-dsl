from dataclasses import dataclass
from enum import Enum

import requests
import vcr
from typing import NamedTuple, Sequence

from graphql_dsl import *
from tests.paths import VCR_FIXTURES_PATH


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


    mk_countries_query, dict_countries_query = GQL.typer ^ CountriesQuery

    q = QUERY | CountriesQuery

    graphql_query = GQL(q)
    expected = 'query CountriesQuery{countries{code name languages{code name}}}'
    assert graphql_query.query == expected

    with vcr.use_cassette(str(VCR_FIXTURES_PATH / 'countries.yaml')):
        response = requests.post(
            url='https://countries.trevorblades.com/',
            json={
                "operationName": f"{CountriesQuery.__name__}",
                "variables": {},
                "query": graphql_query.query,
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


def test_example_syntax_input_data():
    """ https://graphql.org/learn/schema/#the-query-and-mutation-types
    """
    q_str = """
        query {
            hero {
                name
            }
            droid(id: "2000") {
                name
            }
        }
    """
    class Hero(NamedTuple):
        name: str

    class Droid(NamedTuple):
        name: str

    class HeroAndDroid(NamedTuple):
        hero: Hero
        droid: Droid

    class Input(NamedTuple):
        droid_id: ID

    q = GQL(
        QUERY | HeroAndDroid |
        WITH  | Input        |
        PASS  | Input.droid_id * TO * HeroAndDroid.droid * AS * 'id'
    )
    expected = 'query HeroAndDroid($droidId:ID!){hero{name}droid(id:$droidId){name}}'
    assert q.query == expected


def test_with_dataclasses():
    @dataclass
    class Hero:
        name: str

    @dataclass
    class Droid:
        name: str

    @dataclass
    class HeroAndDroid:
        hero: Hero
        droid: Droid

    @dataclass
    class Input:
        droid_id: ID

    q = GQL( QUERY | HeroAndDroid
           | WITH  | Input
           | PASS  | (Input, 'droid_id') * TO * (HeroAndDroid, 'droid') * AS * 'id'
           )
    expected = 'query HeroAndDroid($droidId:ID!){hero{name}droid(id:$droidId){name}}'
    assert q.query == expected


def test_query_with_variable():
    q_str = """
        query DroidById($id: ID!) {
            droid(id: $id) {
                name
            }
        }
    """
    class Droid(NamedTuple):
        name: str

    class Input(NamedTuple):
        droid_id: ID

    class DroidById(NamedTuple):
        droid: Droid

    q2 = GQL( QUERY | DroidById
            | WITH  | Input
            | PASS  | Input.droid_id * TO * DroidById.droid * AS * 'id' )
    expected = 'query DroidById($droidId:ID!){droid(id:$droidId){name}}'
    assert q2.query == expected


def test_mutation():
    q_str = """
        mutation CreateReviewForEpisode($ep: Episode!, $review: Review!) {
            createReview(episode: $ep, review: $review) {
                stars
                commentary
            }
    }
    """
    class Review(NamedTuple):
        stars: int
        commentary: str

    class Episode(Enum):
        ONE = 'one'

    class Input3(NamedTuple):
        episode: Episode
        review: Review

    class CreateReviewForEpisode(NamedTuple):
        create_review: Review

    q = GQL(MUTATION | CreateReviewForEpisode
           |    WITH | Input3
           |    PASS | Input3.episode * TO * CreateReviewForEpisode.create_review
                     & Input3.review  * TO * CreateReviewForEpisode.create_review
           )
    expected = 'mutation CreateReviewForEpisode($episode:Episode!,$review:Review!){createReview(episode:$episode,review:$review){stars commentary}}'
    assert q.query == expected
