import typeit


__all__ = ('NewIDType', 'ID')


class ID(str):
    pass


class IDSchema(typeit.schema.primitives.Str):
    def deserialize(self, node, cstruct: str) -> ID:
        """ Converts input string value ``cstruct`` to ``PortMapping``
        """
        rv = super().deserialize(node, cstruct)
        return ID(rv)

    def serialize(self, node, appstruct: ID) -> str:
        """ Converts ``PortMapping`` back to string value suitable
        for YAML config
        """
        return super().serialize(
            node,
            str(appstruct)
        )

NewIDType = IDSchema[ID]
