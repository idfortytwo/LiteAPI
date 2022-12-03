from typing import Dict, Callable

from liteapi.endpoint import Endpoint


class RoutingMixin:
    _endpoints: Dict[str, Endpoint]

    def route(self, path: str, method: str = 'ANY', *, status_code: int = 200, content_type: str = 'application/json'):
        def decorator(func: Callable):
            self._endpoints[path] = Endpoint(func, method, status_code, content_type)
            return func

        return decorator

    def get(self, path: str, *, status_code: int = 200, content_type: str = 'application/json'):
        return self.route(path, 'GET', status_code=status_code, content_type=content_type)

    def post(self, path: str, *, status_code: int = 200, content_type: str = 'application/json'):
        return self.route(path, 'POST', status_code=status_code, content_type=content_type)

    def put(self, path: str, *, status_code: int = 200, content_type: str = 'application/json'):
        return self.route(path, 'PUT', status_code=status_code, content_type=content_type)

    def patch(self, path: str, *, status_code: int = 200, content_type: str = 'application/json'):
        return self.route(path, 'PATCH', status_code=status_code, content_type=content_type)

    def delete(self, path: str, *, status_code: int = 200, content_type: str = 'application/json'):
        return self.route(path, 'DELETE', status_code=status_code, content_type=content_type)


class Router(RoutingMixin):
    def __init__(self, prefix: str = ""):
        self._prefix = prefix
        self._endpoints: Dict[str, Endpoint] = {}

    @property
    def prefix(self):
        return self._prefix

    @property
    def endpoints(self):
        return self._endpoints
