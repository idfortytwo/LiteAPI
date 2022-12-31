import json
from datetime import datetime
from inspect import Parameter, isclass
from typing import Dict, Callable, get_origin, Union, get_args, Set, Type, Optional, Any, Tuple, List

from pydantic import BaseModel

from liteapi.endpoint import Endpoint


def get_doc_json_endpoint(app) -> Callable:
    # noinspection PyProtectedMember
    def doc_json_endpoint():
        schemas: Set[Type[BaseModel]] = set()
        paths = {}
        for path, endpoints in app._endpoints.items():
            if path in [app._doc_path, app._doc_json_path]:
                continue

            method_endpoints = {}
            for method, endpoint in endpoints.items():
                method_endpoints[method.lower()] = get_endpoint_data(endpoint, path, schemas)

            paths[path] = method_endpoints

        components = {
            'schemas': {
                schema.__name__: json.loads(schema.schema_json())
                for schema
                in schemas
            }
        }

        return {
            'openapi': '3.0.3',
            'info': {
                'title': app._title,
                'version': '0.1.0'
            },
            'paths': paths,
            'components': components,
        }

    return doc_json_endpoint


def get_endpoint_data(endpoint: Endpoint, path: str, schemas: Set[Type[BaseModel]]) -> Dict:
    endpoint_data = {
        'tags': endpoint.tags,
        'summary': endpoint.func.__name__.replace('_', ' ').capitalize(),
        'description': endpoint.func.__doc__
    }
    params, request_body = get_params_and_request_body(endpoint, path, schemas)
    responses = get_responses(endpoint, schemas)
    if params:
        endpoint_data['parameters'] = params
    if request_body:
        endpoint_data['requestBody'] = request_body
    if responses:
        endpoint_data['responses'] = responses

    return endpoint_data


def get_params_and_request_body(
        endpoint: Endpoint,
        path: str,
        schemas: Set[Type[BaseModel]]
) -> Tuple[List[Dict[str, Any]], Dict]:
    params = []
    json_content = None
    form_data = {}
    content: Dict[str, Dict] = {}

    for name, param in endpoint.signature.parameters.items():
        if is_optional(param):
            type_ = get_args(param.annotation)[0]
        else:
            type_ = param.annotation

        if issubclass(type_, BaseModel):
            schemas.add(type_)
            json_content = {
                'schema': {
                    '$ref': f'#/components/schemas/{type_.__name__}'
                }
            }
        elif type_ is bytes:
            print(param.name)
            form_data[param.name] = {
                'type': 'string',
                'format': 'binary'
            }
        else:
            schema = {
                'title': name,
                **get_type_format(type_)
            }
            if param.default is not param.empty:
                schema['default'] = param.default

            params.append({
                'required': param.default is param.empty and not is_optional(param),
                'name': name,
                'in': get_param_location(name, path),
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

    request_body = {
        'content': content
    }

    return params, request_body


type_map = {
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


def get_type_format(type_):
    return type_map.get(type_, {
        'type': 'string'
    })


def get_param_location(name: str, path: str) -> str:
    if '{' + name in path:
        return 'path'
    else:
        return 'query'


def is_optional(param: Parameter):
    return get_origin(param.annotation) is Union and type(None) in get_args(param.annotation)


def get_responses(endpoint: Endpoint, schemas: Set[Type[BaseModel]]) -> Optional[Dict[str, Any]]:
    response_schema = get_response_schema(endpoint, schemas)
    return {
        str(endpoint.status_code): {
            'content': {
                endpoint.content_type: {
                    'schema': response_schema
                }
            }
        }
    }


def get_response_schema(endpoint: Endpoint, schemas) -> dict:
    schema = None
    anno = endpoint.signature.return_annotation
    if anno and anno is not endpoint.signature.empty:
        schema = parse_return_annotation(anno, schemas)
    return schema


def parse_return_annotation(anno: Any, schemas):
    if get_origin(anno) is list:
        type_ = get_args(anno)[0]
        sub_type = parse_return_annotation(type_, schemas)
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
            schemas.add(anno)
            schema = {
                '$ref': f'#/components/schemas/{anno.__name__}'
            }
        else:
            schema = get_type_format(anno)

    return schema


def get_doc_endpoint(doc_json_path) -> Callable:
    def doc_endpoint():
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
                  url: '{doc_json_path}',
                  dom_id: '#swagger-ui',
                }});
              }};
            </script>
            </body>
            </html>
        '''

    return doc_endpoint
