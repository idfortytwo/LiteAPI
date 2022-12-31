from dataclasses import dataclass, field
from inspect import signature, Signature
from typing import Callable, List


@dataclass
class Endpoint:
    func: Callable
    http_method: str
    status_code: int
    content_type: str
    tags: List[str] = None
    signature: Signature = field(init=False, repr=False)

    def __post_init__(self):
        self.signature = signature(self.func)


not_found = Endpoint(lambda: 'No such endpoint', 'GET', 404, 'application/json')
