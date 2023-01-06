from abc import ABC, abstractmethod

from pydantic import ValidationError

from liteapi.responses import JSONResponse


class ParsingError(ABC):
    @abstractmethod
    def to_request(self) -> JSONResponse:
        pass


class PydanticError(ValidationError, ParsingError):
    def to_request(self):
        response = {
            'message': 'Validation failed',
            'details': self.errors()
        }
        return JSONResponse(response, 400)


class ConversionError(ValueError, ParsingError):
    def __init__(self, param_name, param_type, arg_value, *args):
        super().__init__(*args)
        self.param_name = param_name
        self.param_type = param_type
        self.arg_value = arg_value

    def to_request(self):
        response = {
            'message': 'Conversion failed',
            'details': {
                'param_name': self.param_name,
                'param_type': self.param_type,
                'value': self.arg_value
            }
        }
        return JSONResponse(response, 400)


class MissingRequiredError(KeyError, ParsingError):
    def __init__(self, param_name, param_type, *args):
        super().__init__(*args)
        self.param_name = param_name
        self.param_type = param_type

    def to_request(self):
        response = {
            'message': 'Missing required argument',
            'details': {
                'param_name': self.param_name,
                'param_type': self.param_type,
            }
        }
        return JSONResponse(response, 400)
