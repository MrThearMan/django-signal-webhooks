from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Coroutine,
    Dict,
    FrozenSet,
    Generator,
    Iterator,
    List,
    Literal,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
    TypedDict,
    Union,
)

import django
from django.db import models
from django.db.models import QuerySet
from django.db.models.base import Model
from django.db.models.signals import ModelSignal
from httpx._client import UseClientDefault
from httpx._types import (
    AuthTypes,
    CookieTypes,
    HeaderTypes,
    QueryParamTypes,
    RequestContent,
    RequestData,
    RequestFiles,
    TimeoutTypes,
)


__all__ = [
    "Any",
    "Callable",
    "ClientMethodKwargs",
    "Coroutine",
    "Dict",
    "Generator",
    "HooksData",
    "Iterator",
    "JSONData",
    "JSONValue",
    "List",
    "Literal",
    "NamedTuple",
    "Optional",
    "PostDeleteData",
    "PostSaveData",
    "Set",
    "SignalChoices",
    "Tuple",
    "Type",
    "TYPE_CHECKING",
    "TypedDict",
    "Union",
    "Sequence",
]


class PostSaveData(TypedDict):
    signal: ModelSignal
    instance: Model
    created: bool
    raw: bool
    using: str  # database name
    update_fields: Optional[FrozenSet[str]]


class PostDeleteData(TypedDict):
    signal: ModelSignal
    instance: Model
    using: str  # database name

    if django.VERSION >= (4, 1):
        origin: Union[Model, QuerySet]


JSONValue = Union[str, int, float, bool, None, Tuple["JSONValue"], List["JSONValue"], Dict[str, "JSONValue"]]
JSONData = Union[List[Dict[str, JSONValue]], Dict[str, JSONValue]]


class ClientMethodKwargs(TypedDict, total=False):
    content: RequestContent
    data: RequestData
    files: RequestFiles
    json: JSONData
    params: QueryParamTypes
    headers: HeaderTypes
    cookies: CookieTypes
    auth: Union[AuthTypes, UseClientDefault]
    follow_redirects: Union[bool, UseClientDefault]
    timeout: Union[TimeoutTypes, UseClientDefault]
    extensions: Mapping[str, Any]


class HooksData(TypedDict, total=False):
    CREATE: Union[str, Callable, None]
    UPDATE: Union[str, Callable, None]
    DELETE: Union[str, Callable, None]


class SignalChoices(models.IntegerChoices):
    CREATE = 0, "CREATE"
    UPDATE = 1, "UPDATE"
    DELETE = 2, "DELETE"
    CREATE_OR_UPDATE = 3, "CREATE OR UPDATE"
    CREATE_OR_DELETE = 4, "CREATE OR DELETE"
    UPDATE_OR_DELETE = 5, "UPDATE OR DELETE"
    ALL = 6, "ALL"

    @classmethod
    def create_choises(cls) -> Set["SignalChoices"]:
        return {
            cls.CREATE,
            cls.CREATE_OR_UPDATE,
            cls.CREATE_OR_DELETE,
            cls.ALL,
        }

    @classmethod
    def update_choises(cls) -> Set["SignalChoices"]:
        return {
            cls.UPDATE,
            cls.CREATE_OR_UPDATE,
            cls.UPDATE_OR_DELETE,
            cls.ALL,
        }

    @classmethod
    def delete_choises(cls) -> Set["SignalChoices"]:
        return {
            cls.DELETE,
            cls.CREATE_OR_DELETE,
            cls.UPDATE_OR_DELETE,
            cls.ALL,
        }
