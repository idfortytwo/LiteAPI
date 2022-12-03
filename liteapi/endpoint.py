from dataclasses import dataclass
from typing import Callable


@dataclass
class Endpoint:
    func: Callable
    http_method: str
    status_code: int
    content_type: str


not_found = Endpoint(lambda: 'No such endpoint', 'GET', 404, 'application/json')
