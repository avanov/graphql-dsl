.. graphql-dsl documentation master file, created by
   sphinx-quickstart on Sun May 10 13:29:16 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

===========
graphql-dsl
===========

Compose GraphQL queries by defining Python types
------------------------------------------------

Let's take a manually written `GraphQL query <https://graphql.org/learn/schema/#the-query-and-mutation-types>`_:

.. code-block:: graphql

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

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
