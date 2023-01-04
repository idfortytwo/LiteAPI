import json
from datetime import datetime
from functools import lru_cache
from inspect import isclass
from typing import Dict, get_origin, get_args, Set, Type, Optional, Any, Tuple, List

from pydantic import BaseModel

from liteapi.endpoint import Endpoint
from liteapi.parsing import is_optional


class OpenAPI:
    def __init__(
            self,
            endpoints: Dict[str, Dict[str, Endpoint]],
            doc_path: str,
            doc_json_path: str,
            app_title: str
    ):
        self._endpoints = endpoints
        self._doc_path = doc_path
        self._doc_json_path = doc_json_path
        self._app_title = app_title

        self._schemas: Set[Type[BaseModel]] = set()

    def doc_endpoint(self) -> str:
        return f'''
            <!DOCTYPE html>
            <html lang='en'>
            <head>
              <meta charset='utf-8' />
              <meta name='viewport' content='width=device-width, initial-scale=1' />
              <meta name='description' content='SwaggerUI' />
              <title>SwaggerUI</title>
              <link rel='stylesheet' href='https://unpkg.com/swagger-ui-dist@4.5.0/swagger-ui.css' />
            </head>
            <body>
            <div id='swagger-ui'></div>
            <script src='https://unpkg.com/swagger-ui-dist@4.5.0/swagger-ui-bundle.js' crossorigin></script>
            <script>
              window.onload = () => {{
                window.ui = SwaggerUIBundle({{
                  url: '{self._doc_json_path}',
                  dom_id: '#swagger-ui',
                }});
              }};
            </script>
            </body>
            </html>
        '''

    @lru_cache
    def doc_json_endpoint(self) -> Dict[str, Any]:
        paths = {}
        for path, endpoints in self._endpoints.items():
            if path in [self._doc_path, self._doc_json_path]:
                continue

            paths[path] = {
                method.lower(): self._get_endpoint_data(endpoint, path)
                for method, endpoint
                in endpoints.items()
            }

        components = {
            'schemas': {
                schema.__name__: json.loads(schema.schema_json())
                for schema
                in self._schemas
            }
        }

        openapi_json = {
            'openapi': '3.0.3',
            'info': {
                'title': self._app_title,
                'version': '0.1.0'
            },
            'paths': paths,
            'components': components,
        }
        return openapi_json

    def _get_endpoint_data(self, endpoint: Endpoint, path: str) -> Dict[str, Any]:
        endpoint_data = {
            'tags': endpoint.tags,
            'summary': endpoint.func.__name__.replace('_', ' ').capitalize(),
            'description': endpoint.func.__doc__
        }

        params, request_body = self._get_params_and_request_body(endpoint, path)
        responses = self._get_responses(endpoint)
        if params:
            endpoint_data['parameters'] = params
        if request_body:
            endpoint_data['requestBody'] = {
                'content': request_body
            }
        if responses:
            endpoint_data['responses'] = responses

        return endpoint_data

    def _get_params_and_request_body(
            self,
            endpoint: Endpoint,
            path: str
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        params = []
        json_content = {}
        form_data = {}
        content: Dict[str, Dict] = {}

        for name, param in endpoint.signature.parameters.items():
            if is_optional(param):
                type_ = get_args(param.annotation)[0]
            else:
                type_ = param.annotation

            if issubclass(type_, BaseModel):
                self._schemas.add(type_)
                json_content = {
                    'schema': {
                        '$ref': f'#/components/schemas/{type_.__name__}'
                    }
                }
            elif type_ is bytes:
                form_data[name] = {
                    'type': 'string',
                    'format': 'binary'
                }
            else:
                schema = {
                    'title': name,
                    **self._type_to_schema(type_)
                }
                if param.default is not param.empty:
                    schema['default'] = param.default

                params.append({
                    'required': param.default is param.empty and not is_optional(param),
                    'name': name,
                    'in': self._get_param_location(name, path),
                    'schema': schema
                })

        if json_content:
            content['application/json'] = json_content
        if form_data:
            content['multipart/form-data'] = {
                'schema': {
                    'type': 'object',
                    'properties': form_data
                }
            }

        return params, content

    _type_map = {
        int: {
            'type': 'integer'
        },
        float: {
            'type': 'number'
        },
        bool: {
            'type': 'boolean'
        },
        bytes: {
            'type': 'file',
        },
        datetime: {
            'type': 'string',
            'format': 'date-time'
        }
    }

    def _type_to_schema(self, type_) -> Dict[str, str]:
        return self._type_map.get(type_, {
            'type': 'string'
        })

    @staticmethod
    def _get_param_location(name: str, path: str) -> str:
        if '{' + name in path:
            return 'path'
        else:
            return 'query'

    def _get_responses(self, endpoint: Endpoint) -> Optional[Dict[str, Any]]:
        response_schema = self._parse_return_annotation(endpoint.returns)
        return {
            str(endpoint.status_code): {
                'content': {
                    endpoint.content_type: {
                        'schema': response_schema
                    }
                }
            }
        }

    def _parse_return_annotation(self, anno: Any) -> Dict[str, Any]:
        if get_origin(anno) is list:
            type_ = get_args(anno)[0]
            sub_type = self._parse_return_annotation(type_)
            schema = {
                'type': 'array',
                'items': sub_type
            }
        elif get_origin(anno) is dict:
            schema = {
                'type': 'object'
            }
        else:
            if isclass(anno) and issubclass(anno, BaseModel):
                self._schemas.add(anno)
                schema = {
                    '$ref': f'#/components/schemas/{anno.__name__}'
                }
            else:
                schema = self._type_to_schema(anno)

        return schema
