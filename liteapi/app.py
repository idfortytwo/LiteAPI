from typing import Callable, Dict, Tuple, Any, List, Union

from parse import parse

from liteapi.endpoint import Endpoint, not_found
from liteapi.middleware import RequestMiddleware, ResponseMiddleware
from liteapi.openapi import OpenAPI
from liteapi.parsing import _parse_query_params, _parse_body, _handle_endpoint, Request
from liteapi.responses import ResponseDispatcher, Response
from liteapi.routing import RoutingMixin, Router


class App(RoutingMixin):
    def __init__(
            self,
            title='Application',
            doc_path='/api',
            doc_json_path='/api_json'
    ):
        self._endpoints: Dict[str, Dict[str, Endpoint]] = {}
        self._request_middlewares: List[RequestMiddleware] = []
        self._response_middlewares: List[ResponseMiddleware] = []

        self._title = title
        self._doc_path = doc_path
        self._doc_json_path = doc_json_path

        self._setup_openapi()

    def _setup_openapi(self):
        openapi = OpenAPI(
            endpoints=self._endpoints,
            doc_path=self._doc_path,
            doc_json_path=self._doc_json_path,
            app_title=self._title
        )
        self.get(self._doc_path, content_type='text/html')(openapi.doc_endpoint)
        self.get(self._doc_json_path, content_type='application/json')(openapi.doc_json_endpoint)

    def add_router(self, router: Router, *, prefix: str = ''):
        if prefix:
            router.prefix = prefix

        new_endpoints = {}
        for route, endpoints in router.endpoints.items():
            for endpoint in endpoints.values():
                endpoint.tags = router.tag
            new_endpoints[router.prefix + route] = endpoints

        self._endpoints.update(new_endpoints)

    def add_middleware(self, cls: Union[RequestMiddleware, ResponseMiddleware]):
        if isinstance(cls, RequestMiddleware):
            self._request_middlewares.append(cls)
        else:
            self._response_middlewares.append(cls)

    async def __call__(self, scope: dict, receive: Callable, send: Callable):
        request = Request(**scope)

        for middleware in self._request_middlewares:
            request = await middleware.handle(request)

        response = await self._process_request(request, receive)

        for middleware in self._response_middlewares:
            response = await middleware.handle(response)

        await ResponseDispatcher(response, send).send()

    async def _process_request(self, scope: Request, receive) -> Response:
        method = scope.method
        path = scope.path
        headers = scope.headers

        content_type = None
        for key, value in headers.items():
            if key == 'content-type':
                content_type = value

        query_args = _parse_query_params(scope.query_string.decode())
        body_args = await _parse_body(receive, content_type)
        endpoint, path_args = self._parse_path(path, method)

        args = {**query_args, **path_args, **body_args, '_headers': headers}
        return await _handle_endpoint(endpoint, args)

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
