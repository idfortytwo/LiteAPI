from typing import Callable, Dict

from liteapi.endpoint import Endpoint
from liteapi.openapi import OpenAPI
from liteapi.parsing import RequestParser, EndpointProcessor
from liteapi.requests import RequestScope, Request
from liteapi.responses import ResponseDispatcher, Response
from liteapi.routing import RoutingMixin, Router


class App(RoutingMixin):
    def __init__(
            self,
            title='Application',
            doc_path='/api',
            doc_json_path='/api_json'
    ):
        super().__init__()

        self._endpoints: Dict[str, Dict[str, Endpoint]] = {}
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
                endpoint.tags = router.tags
            new_endpoints[router.prefix + route] = endpoints

        self._endpoints.update(new_endpoints)

    async def __call__(self, scope: dict, receive: Callable, send: Callable):
        scope = RequestScope(**scope)
        response = await self._process_request(scope, receive)
        await ResponseDispatcher(response, send).send()

    async def _process_request(self, scope: RequestScope, receive: Callable) -> Response:
        parser = RequestParser(self._endpoints, scope, receive)
        args, endpoint = await parser.extract_args_and_endpoint()
        processor = EndpointProcessor(endpoint, Request(scope, args))
        return await processor.execute()
