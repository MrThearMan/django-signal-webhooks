from collections.abc import Callable, Coroutine, Generator, Iterator, Mapping, Sequence
from typing import (
    Any,
    Dict,
    List,
    Literal,
    NamedTuple,
    Optional,
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
    "ClientKwargs",
    "Coroutine",
    "Dict",
    "Generator",
    "HooksData",
    "Iterator",
    "JSONData",
    "JSONValue",
    "List",
    "Literal",
    "Method",
    "NamedTuple",
    "Optional",
    "PostDeleteData",
    "PostSaveData",
    "Sequence",
    "Set",
    "SignalChoices",
    "Tuple",
    "Type",
    "TypedDict",
    "Union",
]


class PostSaveData(TypedDict):
    signal: ModelSignal
    instance: Model
    created: bool
    raw: bool
    using: str  # database name
    update_fields: Union[frozenset[str], None]


class PostDeleteData(TypedDict):
    signal: ModelSignal
    instance: Model
    using: str  # database name

    if django.VERSION >= (4, 1):
        origin: Union[Model, QuerySet]


JSONValue = Union[
    str,
    int,
    float,
    bool,
    None,
    tuple["JSONValue"],
    list["JSONValue"],
    dict[str, "JSONValue"],
]
JSONData = Union[list[dict[str, JSONValue]], dict[str, JSONValue]]
Method = Literal["CREATE", "UPDATE", "DELETE"]


class ClientKwargs(TypedDict, total=False):
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
    def create_choises(cls) -> set["SignalChoices"]:
        return {
            cls.CREATE,
            cls.CREATE_OR_UPDATE,
            cls.CREATE_OR_DELETE,
            cls.ALL,
        }

    @classmethod
    def update_choises(cls) -> set["SignalChoices"]:
        return {
            cls.UPDATE,
            cls.CREATE_OR_UPDATE,
            cls.UPDATE_OR_DELETE,
            cls.ALL,
        }

    @classmethod
    def delete_choises(cls) -> set["SignalChoices"]:
        return {
            cls.DELETE,
            cls.CREATE_OR_DELETE,
            cls.UPDATE_OR_DELETE,
            cls.ALL,
        }


METHOD_SIGNALS: dict[Method, set[SignalChoices]] = {
    "CREATE": SignalChoices.create_choises(),
    "UPDATE": SignalChoices.update_choises(),
    "DELETE": SignalChoices.delete_choises(),
}

# Define a maximum column size based on MS SQL Server limitation:
# https://docs.microsoft.com/en-us/sql/sql-server/maximum-capacity-specifications-for-sql-server
MAX_COL_SIZE: int = 8_000
