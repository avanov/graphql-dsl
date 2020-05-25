from typing import NamedTuple, Sequence
from graphql_dsl import *


def test_github_query_example():
    """ Composes the following example from
    query ListIssues($owner: String!, $name: String!) {
        repository(owner: $owner, name: $name) {
            issues(first: 100) {
                nodes {
                    number
                    title
                }
                pageInfo {
                    hasNextPage
                    endCursor
                }
            }
        }
    }
    """
    result = """
    query ListIssues($owner:String!,$name:String!,$numFirstIssues:Int!){repository(owner:$owner,name:$name){issues(first:$numFirstIssues){nodes{number title}pageInfo{hasNextPage endCursor}}}}\
    """

    class Node(NamedTuple):
        number: int
        title: str

    class PageInfo(NamedTuple):
        hasNextPage: bool
        endCursor: str

    class Issue(NamedTuple):
        nodes: Sequence[Node]
        pageInfo: PageInfo

    class Repository(NamedTuple):
        issues: Sequence[Issue]

    class ListIssues(NamedTuple):
        repository: Repository

    class Input(NamedTuple):
        owner: str
        name: str
        numFirstIssues: int

    q = GQL( QUERY | ListIssues
             | WITH  | Input
             | PASS  | Input.owner          * TO * ListIssues.repository
             & Input.name           * TO * ListIssues.repository
             & Input.numFirstIssues * TO * Repository.issues * AS * 'first'
             )

    assert q.query == result.strip()