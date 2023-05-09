from typing import Any, Callable, List

import pydantic
import pydash


class DomainBaseModel(pydantic.BaseModel):
    class Config(pydantic.BaseConfig):
        frozen: bool = True
        orm_mode: bool = True
        from_attributes: bool = True

    def __hash__(self) -> int:  # pyright: ignore[reportIncompatibleVariableOverride]
        return hash((type(self),) + tuple(self.__dict__.values()))


class Event(pydantic.BaseModel):
    ...


class ValueObject(DomainBaseModel):
    def __hash__(self) -> int:
        return super().__hash__()


class Entity(DomainBaseModel):
    id: str

    class Config(DomainBaseModel.Config):
        frozen: bool = False

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.id}>"

    def __hash__(self) -> int:
        return hash(self.__class__) + hash(self.id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return other.id == self.id


class Aggregate(DomainBaseModel):
    version_number: int = pydantic.Field(default=0)
    events: List[Event] = pydantic.Field(default_factory=list)

    class Config(DomainBaseModel.Config):
        frozen: bool = False

    def __hash__(self) -> int:
        _pk = self._get_primary_key()
        return hash(self.__class__) + hash(_pk)

    def _update_version(self) -> None:
        self.version_number += 1

    def _get_primary_key(self) -> str:
        _properties = self.schema().get("properties")
        assert (
            _properties is not None
        ), "Aggregate object must have at least one field"

        _fields: List[str] = _properties.keys()
        _filter: Callable[[str], bool] = (
            lambda x: _properties[x].get("primary_key") is True
        )
        _pk: Any = pydash.collections.find(_fields, _filter)
        assert _pk is not None, "Aggregate object must have a primary_key"
        return _pk
