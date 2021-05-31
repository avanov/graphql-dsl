.. _badges:

.. image:: https://github.com/avanov/graphql-dsl/workflows/GitHub%20CI/badge.svg?branch=develop
    :target: https://github.com/avanov/graphql-dsl/actions?query=workflow%3A%22GitHub+CI%22

.. image:: https://travis-ci.org/avanov/graphql-dsl.svg?branch=develop
    :target: https://travis-ci.org/avanov/graphql-dsl

.. image:: https://circleci.com/gh/avanov/graphql-dsl/tree/develop.svg?style=svg
    :target: https://circleci.com/gh/avanov/graphql-dsl/tree/develop

.. image:: https://coveralls.io/repos/github/avanov/graphql-dsl/badge.svg?branch=develop
    :target: https://coveralls.io/github/avanov/graphql-dsl?branch=develop

.. image:: https://requires.io/github/avanov/graphql-dsl/requirements.svg?branch=develop
    :target: https://requires.io/github/avanov/graphql-dsl/requirements/?branch=develop
    :alt: Requirements Status

.. image:: https://readthedocs.org/projects/graphql-dsl/badge/?version=develop
    :target: http://graphql-dsl.readthedocs.org/en/develop/
    :alt: Documentation Status

.. image:: http://img.shields.io/pypi/v/graphql-dsl.svg
    :target: https://pypi.python.org/pypi/graphql-dsl
    :alt: Latest PyPI Release

Compose GraphQL queries by composing Python types
=================================================

.. code-block:: bash

    pip install graphql-dsl

Let's take a manually written `GraphQL query from the official docs <https://graphql.org/learn/schema/#the-query-and-mutation-types>`_:

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

The value of ``q.query`` is a GraphQL query template that should be used with instances of ``Input`` to call
servers with GraphQL API

.. code-block:: python

    import requests

    q = GQL(...)

    def call_server(droid_id: ID) -> HeroAndDroid:
        response = requests.post(
            url='https://<graphql-server-url>/',
            json=q.request_payload(Input(droid_id=droid_id)),
            headers={ 'Content-Type': 'application/json'
                    , 'Accept': 'application/json'
                    }
        )
        response.raise_for_status()
        return q.get_result(response.json())

Note that the query `q` resides at the top-level module scope, as the query constructor doesn't depend on the
query's input values, it only needs to know about the shapes of input and output data.

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

Find out more from `Official Documentation <https://graphql-dsl.readthedocs.io/en/develop/>`_.


Test Suite
----------

Test environment is based on `Nix <https://nixos.org/nix/>`_.

.. code-block:: bash

    nix-shell
    pytest
