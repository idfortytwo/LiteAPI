import cgi
import inspect
import json
from io import BytesIO
from typing import Dict, Any, get_origin, Union, get_args, Callable, Tuple

from parse import parse
from pydantic import BaseModel

from liteapi.endpoint import Endpoint, not_found
from liteapi.errors import ParsingError, ConversionError, MissingRequiredError
from liteapi.requests import Request, RequestScope
from liteapi.responses import Response


class RequestParser:
    def __init__(self, endpoints: Dict[str, Dict[str, Endpoint]], request_scope: RequestScope, receive: Callable):
        self._endpoints = endpoints
        self._request_scope = request_scope
        self._receive = receive

    async def extract_args_and_endpoint(self) -> Tuple[dict, Endpoint]:
        method = self._request_scope.method
        path = self._request_scope.path
        content_type = self._request_scope.headers.get('content-type', None)

        query_args = self._parse_query()
        body_args = await self._parse_body(content_type)
        endpoint, path_args = self._parse_path(path, method)

        args = {**query_args, **path_args, **body_args}
        return args, endpoint

    def _parse_query(self) -> Dict[str, str]:
        query_params = self._request_scope.query_string.decode()
        args = {}
        if query_params:
            for param in query_params.split('&'):
                key, value = param.split('=')
                args[key] = value
        return args

    async def _parse_body(self, content_type: str) -> Dict[str, Any]:
        if content_type:
            body = await self._read_body()
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

    async def _read_body(self) -> bytes:
        body = b''
        more_body = True

        while more_body:
            message = await self._receive()
            body += message.get('body', b'')
            more_body = message.get('more_body', False)

        return body

    def _parse_path(self, path: str, method: str) -> Tuple[Endpoint, Dict[str, Any]]:
        for route, endpoints in self._endpoints.items():
            path_match = parse(route, path)
            if path_match:
                endpoint = endpoints.get(
                    method,
                    endpoints.get('ANY', not_found)
                )
                return endpoint, path_match.named

        return not_found, {}


class EndpointProcessor:
    def __init__(self, endpoint: Endpoint, request: Request):
        self._endpoint = endpoint
        self._request = request

    async def execute(self) -> Response:
        try:
            self._validate_and_convert_args()
        except ParsingError as e:
            return e.to_request()

        return await self._endpoint.process(self._request)

    def _validate_and_convert_args(self):
        parsed_args = {}
        for param in self._endpoint.signature.parameters.values():
            cls = param.annotation
            optional = is_optional(param)

            try:
                if optional:
                    cls = extract_from_optional(param)
                if issubclass(cls, BaseModel):
                    arg = cls(**self._request.args)
                else:
                    arg = cls(self._request.args[param.name])
            except ValueError:
                raise ConversionError(param.name, cls.__name__, self._request.args[param.name])
            except KeyError:
                if optional:
                    arg = None
                elif param.default == inspect.Parameter.empty:
                    raise MissingRequiredError(param.name, cls.__name__)
                else:
                    arg = param.default

            parsed_args[param.name] = arg
        self._request.args = parsed_args


def is_optional(param: inspect.Parameter):
    return get_origin(param.annotation) is Union and type(None) in get_args(param.annotation)


def extract_from_optional(param: inspect.Parameter):
    return get_args(param.annotation)[0]
