.. graphql-dsl documentation master file, created by
   sphinx-quickstart on Sun May 10 13:29:16 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

===========
graphql-dsl
===========

.. contents::
   :local:

Quick intro
===========

Let's take a manually written `GraphQL query <https://graphql.org/learn/schema/#the-query-and-mutation-types>`_:

.. code-block::

    query {
        hero {
            name
        }
        droid(id: "2000") {
            name
        }
    }


With ``graphql-dsl`` you can construct a similar query with the following Python snippet:

.. code-block:: python

    from typing import NamedTuple
    from graphql_dsl import *

    class Hero(NamedTuple):
        name: str

    class Droid(NamedTuple):
        name: str

    class HeroAndDroid(NamedTuple):
        hero: Hero
        droid: Droid

    class Input(NamedTuple):
        droid_id: ID

    q = GQL( QUERY | HeroAndDroid
           | WITH  | Input
           | PASS  | Input.droid_id * TO * HeroAndDroid.droid * AS * 'id'
           )

    print(q.query)

and the output will be::

    query HeroAndDroid($droidId:ID!){hero{name}droid(id:$droidId){name}}

The query builder supports both ``NamedTuple`` and ``@dataclass`` types, yet the latter has a slightly different
field reference syntax (because dataclasses don't define class-level field getters):

.. code-block:: python

    from dataclasses import dataclass
    from graphql_dsl import *

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

Simple queries
--------------

Let's use `Countries API <https://countries.trevorblades.com/>`_ and prepare the simplest query for it.

We want to fetch a list of all country codes

.. code-block:: python

    from typing import Sequence, NamedTuple

    class Country(NamedTuple):
        code: str

    class Query(NamedTuple):
        countries: Sequence[Country]

We can start composing our query with:

.. code-block:: python

    from graphql_dsl import QUERY

    countries_query = QUERY | Query


If we don't need to provide input parameters to the query, we can immediately compile it:

.. code-block:: python

    from graphql_dsl import GQL

    compiled_query = GQL(countries_query)


Now we are able to call the service and receive the typed result from it:

.. code-block:: python

    import requests

    response = requests.post(
        url="https://countries.trevorblades.com/",
        json={
            "operationName": compiled_query.name,
            "query": compiled_query.query,
        }
    )

    data = compiled_query.get_result(response)
    assert isinstance(data, Query)

    # will print AD, AE, AF, AG, AI, AL, AM, AO, ...
    print(', '.join(country.code for country in data.countries))



Documentation Indices and tables
================================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`