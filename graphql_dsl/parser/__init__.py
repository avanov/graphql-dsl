import graphql


def parse(src: str) -> graphql.DocumentNode:
    schema = graphql.parse(src)
    schema.definitions[0].operation_types[0].type.name.value
    return schema
