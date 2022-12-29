import cgi
import inspect
import json
import traceback
from dataclasses import dataclass, field
from io import BytesIO
from typing import Dict, Any, Tuple

from pydantic import BaseModel, ValidationError

from liteapi.endpoint import Endpoint


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


def _parse_query_params(query_params: str) -> Dict[str, str]:
    params = {}
    if query_params:
        for param in query_params.split('&'):
            key, value = param.split('=')
            params[key] = value
    return params


async def _parse_body(receive, content_type) -> Dict[str, Any]:
    if content_type:
        body = await _read_body(receive)
        if content_type == 'application/json':
            return json.loads(body)
        elif content_type.startswith('multipart/form-data'):
            ctype, pdict = cgi.parse_header(content_type)
            pdict['boundary'] = pdict['boundary'].encode("utf-8")  # noqa

            fields = cgi.parse_multipart(BytesIO(body), pdict)  # noqa
            return {
                key: value[0] if len(value) == 1 else value
                for key, value
                in fields.items()
            }
    return {}


async def _read_body(receive) -> bytes:
    body = b''
    more_body = True

    while more_body:
        message = await receive()
        body += message.get('body', b'')
        more_body = message.get('more_body', False)

    return body


async def _handle_endpoint(endpoint: Endpoint, args: Dict[str, Any]) -> Tuple[Any, int, str]:
    parsed_args = {}

    sig = inspect.signature(endpoint.func)
    error_response = _validate_and_convert_args(sig, args, parsed_args)
    if error_response:
        return error_response

    try:
        if inspect.iscoroutinefunction(endpoint.func):
            result = await endpoint.func(**parsed_args)
        else:
            result = endpoint.func(**parsed_args)

        match result:
            case result, int(code):
                pass
            case result:
                code = endpoint.status_code

    except Exception as e:
        response = {
            'message': 'internal server error',
            'error': str(e),
            'details': traceback.format_exc()
        }
        return response, 500, 'application/json'

    return result, code, endpoint.content_type


def _validate_and_convert_args(sig: inspect.Signature, args: Dict, parsed_args: Dict):
    for param in sig.parameters.values():
        cls = param.annotation

        try:
            if issubclass(cls, BaseModel):
                arg = cls(**args)
            else:
                arg = cls(args[param.name])
        except ValidationError as e:
            response = {
                'message': 'validation failed',
                'details': e.errors()
            }
            return response, 400, 'application/json'
        except ValueError:
            response = {
                'message': 'conversion failed',
                'details': {
                    'param_name': param.name,
                    'param_type': cls.__name__,
                    'value': args[param.name]
                }
            }
            return response, 400, 'application/json'
        except KeyError:
            if param.default == inspect.Parameter.empty:
                response = {
                    'message': 'missing required argument',
                    'details': {
                        'param_name': param.name,
                        'param_type': cls.__name__
                    }
                }
                return response, 400, 'application/json'
            else:
                arg = param.default

        parsed_args[param.name] = arg
