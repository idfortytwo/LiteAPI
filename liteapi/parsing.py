import cgi
import inspect
import json
import traceback
from io import BytesIO
from typing import Dict, Any, Tuple

from pydantic import BaseModel, ValidationError

from liteapi.endpoint import Endpoint


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

    error_response = _parse_args(endpoint, args, parsed_args)
    if error_response:
        return error_response

    try:
        if inspect.iscoroutinefunction(endpoint.func):
            result = await endpoint.func(**parsed_args)
        else:
            result = endpoint.func(**parsed_args)
    except Exception as e:
        response = {
            'message': 'internal server error',
            'error': str(e),
            'details': traceback.format_exc()
        }
        return response, 500, 'application/json'

    return result, endpoint.status_code, endpoint.content_type


def _parse_args(endpoint: Endpoint, args: Dict, parsed_args: Dict):
    sig = inspect.signature(endpoint.func)
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
