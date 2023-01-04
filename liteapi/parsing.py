import cgi
import inspect
import json
from io import BytesIO
from typing import Dict, Any, get_origin, Union, get_args

from pydantic import BaseModel, ValidationError

from liteapi.endpoint import Endpoint
from liteapi.requests import Request
from liteapi.responses import Response, JSONResponse


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


async def _handle_endpoint(endpoint: Endpoint, request: Request) -> Response:
    error_response = _validate_and_convert_args(endpoint.signature, request)
    if error_response:
        return error_response

    return await endpoint.handle(request)


def _validate_and_convert_args(sig: inspect.Signature, request: Request):
    parsed_args = {}
    for param in sig.parameters.values():
        cls = param.annotation
        optional = is_optional(param)

        try:
            if optional:
                cls = extract_from_optional(param)
            if issubclass(cls, BaseModel):
                arg = cls(**request.args)
            else:
                arg = cls(request.args[param.name])
        except ValidationError as e:
            response = {
                'message': 'validation failed',
                'details': e.errors()
            }
            return JSONResponse(response, 400)
        except ValueError:
            response = {
                'message': 'conversion failed',
                'details': {
                    'param_name': param.name,
                    'param_type': cls.__name__,
                    'value': request.args[param.name]
                }
            }
            return JSONResponse(response, 400)
        except KeyError:
            if optional:
                arg = None
            elif param.default == inspect.Parameter.empty:
                response = {
                    'message': 'missing required argument',
                    'details': {
                        'param_name': param.name,
                        'param_type': cls.__name__
                    }
                }
                return JSONResponse(response, 400)
            else:
                arg = param.default

        parsed_args[param.name] = arg
    request.args = parsed_args


def is_optional(param: inspect.Parameter):
    return get_origin(param.annotation) is Union and type(None) in get_args(param.annotation)


def extract_from_optional(param: inspect.Parameter):
    return get_args(param.annotation)[0]
