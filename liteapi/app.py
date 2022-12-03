import json
from typing import Callable, Dict, Tuple, Any, List

from parse import parse

from liteapi.endpoint import Endpoint, not_found
from liteapi.middleware import Middleware
from liteapi.parsing import _parse_query_params, _parse_body, _handle_endpoint
from liteapi.routing import RoutingMixin, Router


class App(RoutingMixin):
    def __init__(self):
        self._endpoints: Dict[str, Endpoint] = {}
        self._middlewares: List[Middleware] = []

    def add_router(self, router: Router, *, prefix: str = ""):
        if not prefix:
            prefix = router.prefix

        self._endpoints.update({
            prefix + route: endpoint
            for route, endpoint
            in router.endpoints.items()
        })

    def add_middleware(self, cls: Middleware):
        self._middlewares.append(cls)

    async def __call__(self, scope, receive, send):
        for middleware in self._middlewares:
            scope, receive, send = await middleware.handle(scope, receive, send)
        await self._handle(scope, receive, send)

    async def _handle(self, scope, receive, send):
        method = scope['method']
        path = scope['path']
        headers = scope['headers']

        content_type = None
        for key, value in headers:
            if key == b'content-type':
                content_type = value.decode()

        query_args = _parse_query_params(scope['query_string'].decode())
        body_args = await _parse_body(receive, content_type)
        endpoint, path_args = self._parse_path(path, method)

        args = {**query_args, **path_args, **body_args, '_headers': headers}
        result, code, content_type = await _handle_endpoint(endpoint, args)
        await _send_response(send, result, code, content_type)

    def _parse_path(self, path: str, method: str) -> Tuple[Endpoint, Dict[str, Any]]:
        for route, endpoint in self._endpoints.items():
            path_match = parse(route, path)
            if path_match and endpoint.http_method in [method, 'ANY']:
                return endpoint, path_match.named

        return not_found, {}


async def _send_response(send: Callable, body: Any, status_code: int, content_type: str):
    await send({
        'type': 'http.response.start',
        'status': status_code,
        'headers': [
            [b'content-type', content_type.encode()],
        ],
    })

    if content_type.startswith('image') or \
            content_type.startswith('audio') or \
            content_type.startswith('video') or \
            content_type == 'application/octet-stream' or \
            isinstance(body, bytes):

        if isinstance(body, list):
            for chunk in body:
                await send({
                    'type': 'http.response.body',
                    'body': chunk,
                    'more_body': True
                })
            await send({
                'type': 'http.response.body',
                'body': b'',
            })
        else:
            await send({
                'type': 'http.response.body',
                'body': body,
            })
    else:
        if content_type == 'application/json':
            body = json.dumps(body).encode()
        else:
            body = str.encode(body)

        await send({
            'type': 'http.response.body',
            'body': body,
        })
