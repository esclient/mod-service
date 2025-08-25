from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

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
