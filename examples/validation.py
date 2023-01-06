from typing import Optional

from pydantic import BaseModel

from examples.main import app
from liteapi import Router

validation_router = Router('/validation')


@validation_router.get('/required_query')
def optional_and_required_query_params(
        required: str,
        optional: Optional[str],
        default: str = 'has_default'):
    return {
        'required': required,
        'optional': optional,
        'optional_with_default': default
    }


@validation_router.get('/type_check')
def type_check(decimal: float):
    return f'Converted value: {decimal}'


class NumberModel(BaseModel):
    required_integer: int
    optional_float: Optional[float] = 3.14


@validation_router.get('/type_check')
def pydantic_check(model: NumberModel):
    return model


app.add_router(validation_router)
