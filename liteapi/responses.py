import json
from json import JSONEncoder
from typing import Any, Iterable, Callable, Union, Dict

from pydantic import BaseModel


class Response:
    def __init__(self, data: Any, status_code=200, content_type='text/plain'):
        self._data = data
        self._status_code = status_code
        self._content_type = content_type

    def to_bytes(self) -> bytes:
        return str(self._data).encode()

    @property
    def data(self) -> Any:
        return self._data

    @property
    def status_code(self) -> int:
        return self._status_code

    @property
    def content_type(self) -> str:
        return self._content_type


class PydanticEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, BaseModel):
            return o.dict()
        else:
            return super().default(o)


class PlainResponse(Response):
    def __init__(self, data: Union[Dict, Any], status_code=200, content_type='text/plain'):
        super().__init__(data, status_code, content_type)


class HTMLResponse(Response):
    def __init__(self, data: Union[Dict, Any], status_code=200, content_type='text/html'):
        super().__init__(data, status_code, content_type)


class JSONResponse(Response):
    def __init__(self, data: Union[Dict, Any], status_code=200, content_type='application/json'):
        super().__init__(data, status_code, content_type)

    def to_bytes(self) -> bytes:
        return json.dumps(self._data, cls=PydanticEncoder).encode()


class BinaryResponse(Response):
    def __init__(self, data: bytes, status_code=200, content_type='application/octet-stream'):
        super().__init__(data, status_code, content_type)

    def to_bytes(self) -> bytes:
        return self._data


class ChunkedBinaryResponse(Response):
    def __init__(self, data: Iterable[bytes], status_code=200, content_type='application/octet-stream'):
        super().__init__(data, status_code, content_type)

    def to_bytes(self) -> bytes:
        yield from self._data


def response_factory(data: Any, code, content_type):
    if content_type == 'application/json':
        cls = JSONResponse
    elif (content_type == 'application/octet-stream' or
          content_type.startswith('image') or
          content_type.startswith('audio') or
          content_type.startswith('video') or
          isinstance(data, bytes)):
        if isinstance(data, list):
            cls = ChunkedBinaryResponse
        else:
            cls = BinaryResponse
    else:
        cls = Response

    return cls(data, code, content_type)


class ResponseDispatcher:
    def __init__(self, response: Response, send: Callable):
        self._response = response
        self._send = send

    async def send(self):
        await self._send({
            'type': 'http.response.start',
            'status': self._response.status_code,
            'headers': [
                [b'content-type', self._response.content_type.encode()],
            ],
        })

        body = self._response.to_bytes()

        if isinstance(self._response, ChunkedBinaryResponse):
            for chunk in body:
                await self._send({
                    'type': 'http.response.body',
                    'body': chunk,
                    'more_body': True
                })
            await self._send({
                'type': 'http.response.body',
                'body': b'',
            })
        else:
            await self._send({
                'type': 'http.response.body',
                'body': body,
            })
