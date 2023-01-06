from typing import Optional

from pydantic import BaseModel

from examples.main import app
from liteapi import Router

source_router = Router('/source')


@source_router.get('/positional_and_query/{pos1}/{pos2}')
def positional_and_query(
        pos1: str,
        query1: float,
        query2: Optional[str]):
    return {
        'first positional': pos1,
        'first query': query1,
        'second query': query2
    }


@source_router.post('/from_json')
def from_json(key1: str, key2: str):
    return {
        'key1': key1,
        'key2': key2
    }


class KeysModel(BaseModel):
    key1: str
    key2: str


@source_router.post('/from_json_to_model')
def from_json(model: KeysModel):
    return {
        'key1': model.key1,
        'key2': model.key2
    }


@source_router.get('/mixed/{pos}')
def pydantic_and_query(model: KeysModel, query: str, positional: str):
    return {
        'query': query,
        'model': model,
        'positional': positional
    }


app.add_router(source_router)
