from http import HTTPStatus
from typing import Any, Dict, Optional

class ResultadoOperacion:
    def __init__(self, status: HTTPStatus = HTTPStatus.INTERNAL_SERVER_ERROR, datos: Any = None, error: Any = None):
        self.status: HTTPStatus = status
        self.datos: dict[Any,Any] = datos
        self.error = error

    @classmethod
    def exitoso(cls, data: Optional[Dict[Any,Any]] = None):
        return cls(status=HTTPStatus.OK,datos=data)

    @classmethod
    def error(cls, status: HTTPStatus, error: str):
        return cls(status=status, error=error)