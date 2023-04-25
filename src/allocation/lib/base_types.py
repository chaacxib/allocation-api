import pydantic


@pydantic.dataclasses.dataclass(unsafe_hash=True)
class ValueObject:
    ...


@pydantic.dataclasses.dataclass
class Entity:
    id: str

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.id}>"

    def __hash__(self) -> int:
        return hash(self.__class__) + hash(self.id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return other.id == self.id


@pydantic.dataclasses.dataclass(unsafe_hash=True)
class Aggregate:
    ...
