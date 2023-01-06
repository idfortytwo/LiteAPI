from typing import List

from pydantic import BaseModel

from examples.main import app
from liteapi import Router


class TestModel(BaseModel):
    some_string: str
    some_float: float
    numbers: List[int]


model_router = Router('/models')


@model_router.get('/single', content_type='application/json', returns=TestModel)
def single_model():
    return TestModel(some_string='one', some_float=3.14, numbers=[1, 2, 3])


@model_router.get('/list', content_type='application/json', returns=List[TestModel])
def model_list():
    return [
        TestModel(some_string='one', some_float=3.14, numbers=[1, 2, 3]),
        TestModel(some_string='two', some_float=6.28, numbers=[2, 4, 6])
    ]


app.add_router(model_router)
