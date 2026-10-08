from typing import NoReturn

from fastapi import HTTPException


def fail(status: int, code: str, message: str) -> NoReturn:
    headers = {"WWW-Authenticate": "Bearer"} if status == 401 else None
    raise HTTPException(status, {"code": code, "message": message}, headers=headers)
