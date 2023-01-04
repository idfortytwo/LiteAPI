from dataclasses import dataclass, field
from typing import Dict, Tuple, List, Any


@dataclass
class Scope:
    type: str
    asgi: Dict[str, str]
    http_version: str
    server: Tuple[str, int]
    client: Tuple[str, int]
    scheme: str
    method: str
    root_path: str
    path: str
    raw_path: bytes
    query_string: bytes
    headers: Dict[str, str]
    _headers: Dict[str, str] = field(repr=False, init=False)

    @property
    def headers(self):
        return self._headers

    @headers.setter
    def headers(self, headers: List[Tuple[bytes, bytes]]):
        self._headers = {}
        for key, value in headers:
            self._headers[key.decode()] = value.decode()


class Request:
    def __init__(self, scope: Scope, args: Dict[str, Any]):
        self.scope = scope
        self.args = args
