from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ModStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    MOD_STATUS_UNSPECIFIED: _ClassVar[ModStatus]
    MOD_STATUS_UPLOADED: _ClassVar[ModStatus]
    MOD_STATUS_BANNED: _ClassVar[ModStatus]
    MOD_STATUS_HIDDEN: _ClassVar[ModStatus]
MOD_STATUS_UNSPECIFIED: ModStatus
MOD_STATUS_UPLOADED: ModStatus
MOD_STATUS_BANNED: ModStatus
MOD_STATUS_HIDDEN: ModStatus

class SetStatusRequest(_message.Message):
    __slots__ = ("mod_id", "status")
    MOD_ID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    mod_id: int
    status: ModStatus
    def __init__(self, mod_id: _Optional[int] = ..., status: _Optional[_Union[ModStatus, str]] = ...) -> None: ...

class SetStatusResponse(_message.Message):
    __slots__ = ("success",)
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    def __init__(self, success: bool = ...) -> None: ...

class CreateModRequest(_message.Message):
    __slots__ = ("mod_title", "author_id", "filename", "description")
    MOD_TITLE_FIELD_NUMBER: _ClassVar[int]
    AUTHOR_ID_FIELD_NUMBER: _ClassVar[int]
    FILENAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    mod_title: str
    author_id: int
    filename: str
    description: str
    def __init__(self, mod_title: _Optional[str] = ..., author_id: _Optional[int] = ..., filename: _Optional[str] = ..., description: _Optional[str] = ...) -> None: ...

class CreateModResponse(_message.Message):
    __slots__ = ("mod_id", "upload_url", "s3_key")
    MOD_ID_FIELD_NUMBER: _ClassVar[int]
    UPLOAD_URL_FIELD_NUMBER: _ClassVar[int]
    S3_KEY_FIELD_NUMBER: _ClassVar[int]
    mod_id: int
    upload_url: str
    s3_key: str
    def __init__(self, mod_id: _Optional[int] = ..., upload_url: _Optional[str] = ..., s3_key: _Optional[str] = ...) -> None: ...

class GetModDownloadLinkRequest(_message.Message):
    __slots__ = ("mod_id",)
    MOD_ID_FIELD_NUMBER: _ClassVar[int]
    mod_id: int
    def __init__(self, mod_id: _Optional[int] = ...) -> None: ...

class GetModDownloadLinkResponse(_message.Message):
    __slots__ = ("link_url",)
    LINK_URL_FIELD_NUMBER: _ClassVar[int]
    link_url: str
    def __init__(self, link_url: _Optional[str] = ...) -> None: ...
