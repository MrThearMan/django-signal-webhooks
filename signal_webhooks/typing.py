from collections.abc import Callable, Coroutine, Generator, Iterator, Mapping, Sequence
from typing import (
    Any,
    Dict,
    FrozenSet,
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

JSONValue = Union[str, int, float, bool, None, Tuple["JSONValue"], List["JSONValue"], Dict[str, "JSONValue"]]
JSONData = Union[List[Dict[str, JSONValue]], Dict[str, JSONValue]]
Method = Literal["CREATE", "UPDATE", "DELETE", "M2M_ADD", "M2M_REMOVE", "M2M_CLEAR"]
M2MAction = Literal["pre_add", "post_add", "pre_remove", "post_remove", "pre_clear", "post_clear"]


class PostSaveData(TypedDict):
    signal: ModelSignal
    instance: Model
    created: bool
    raw: bool
    using: str  # database name
    update_fields: Union[FrozenSet[str], None]


class PostDeleteData(TypedDict):
    signal: ModelSignal
    instance: Model
    using: str  # database name

    if django.VERSION >= (4, 1):
        origin: Union[Model, QuerySet]


class M2MChangedData(TypedDict):
    signal: ModelSignal
    action: M2MAction
    instance: Model
    reverse: bool
    model: Type[Model]
    pk_set: Set[int]
    using: str  # database name


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
    M2M_ADD: Union[str, Callable, None]
    M2M_REMOVE: Union[str, Callable, None]
    M2M_CLEAR: Union[str, Callable, None]


class SignalChoices(models.TextChoices):
    CREATE = (
        "CREATE",
        "Create",
    )
    UPDATE = (
        "UPDATE",
        "Update",
    )
    DELETE = (
        "DELETE",
        "Delete",
    )
    M2M = (
        "M2M",
        "M2M changed",
    )
    CREATE_OR_UPDATE = (
        "CREATE_OR_UPDATE",
        "Create or Update",
    )
    CREATE_OR_DELETE = (
        "CREATE_OR_DELETE",
        "Create or Delete",
    )
    CREATE_OR_M2M = (
        "CREATE_OR_M2M",
        "Create or M2M changed",
    )
    UPDATE_OR_DELETE = (
        "UPDATE_OR_DELETE",
        "Update or Delete",
    )
    UPDATE_OR_M2M = (
        "UPDATE_OR_M2M",
        "Update or M2M changed",
    )
    DELETE_OR_M2M = (
        "DELETE_OR_M2M",
        "Delete or M2M changed",
    )
    CREATE_UPDATE_OR_DELETE = (
        "CREATE_UPDATE_OR_DELETE",
        "Create, Update or Delete",
    )
    CREATE_UPDATE_OR_M2M = (
        "CREATE_UPDATE_OR_M2M",
        "Create, Update or M2M changed",
    )
    CREATE_DELETE_OR_M2M = (
        "CREATE_DELETE_OR_M2M",
        "Create, Delete or M2M changed",
    )
    UPDATE_DELETE_OR_M2M = (
        "UPDATE_DELETE_OR_M2M",
        "Update, Delete or M2M changed",
    )
    CREATE_UPDATE_DELETE_OR_M2M = (
        "CREATE_UPDATE_DELETE_OR_M2M",
        "Create, Update or Delete, or M2M changed",
    )

    @classmethod
    def create_choices(cls) -> Set["SignalChoices"]:
        return {
            cls.CREATE,
            cls.CREATE_OR_UPDATE,
            cls.CREATE_OR_DELETE,
            cls.CREATE_OR_M2M,
            cls.CREATE_UPDATE_OR_DELETE,
            cls.CREATE_DELETE_OR_M2M,
            cls.CREATE_UPDATE_OR_M2M,
            cls.CREATE_UPDATE_DELETE_OR_M2M,
        }

    @classmethod
    def update_choices(cls) -> Set["SignalChoices"]:
        return {
            cls.UPDATE,
            cls.CREATE_OR_UPDATE,
            cls.UPDATE_OR_DELETE,
            cls.UPDATE_OR_M2M,
            cls.CREATE_UPDATE_OR_DELETE,
            cls.CREATE_UPDATE_OR_M2M,
            cls.UPDATE_DELETE_OR_M2M,
            cls.CREATE_UPDATE_DELETE_OR_M2M,
        }

    @classmethod
    def delete_choices(cls) -> Set["SignalChoices"]:
        return {
            cls.DELETE,
            cls.CREATE_OR_DELETE,
            cls.UPDATE_OR_DELETE,
            cls.DELETE_OR_M2M,
            cls.CREATE_UPDATE_OR_DELETE,
            cls.CREATE_DELETE_OR_M2M,
            cls.UPDATE_DELETE_OR_M2M,
            cls.CREATE_UPDATE_DELETE_OR_M2M,
        }

    @classmethod
    def m2m_choices(cls) -> Set["SignalChoices"]:
        return {
            cls.M2M,
            cls.CREATE_OR_M2M,
            cls.UPDATE_OR_M2M,
            cls.DELETE_OR_M2M,
            cls.CREATE_DELETE_OR_M2M,
            cls.CREATE_UPDATE_OR_M2M,
            cls.UPDATE_DELETE_OR_M2M,
            cls.CREATE_UPDATE_DELETE_OR_M2M,
        }


METHOD_SIGNALS: Dict[Method, Set[SignalChoices]] = {
    "CREATE": SignalChoices.create_choices(),
    "UPDATE": SignalChoices.update_choices(),
    "DELETE": SignalChoices.delete_choices(),
    "M2M_ADD": SignalChoices.m2m_choices(),
    "M2M_REMOVE": SignalChoices.m2m_choices(),
    "M2M_CLEAR": SignalChoices.m2m_choices(),
}

ACTION_TO_METHOD: Dict[M2MAction, Method] = {
    "post_add": "M2M_ADD",
    "post_remove": "M2M_REMOVE",
    "post_clear": "M2M_CLEAR",
}

# Define a maximum column size based on MS SQL Server limitation:
# https://docs.microsoft.com/en-us/sql/sql-server/maximum-capacity-specifications-for-sql-server
MAX_COL_SIZE: int = 8_000
