from pydantic import BaseModel, ConfigDict


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Output(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Page[T](BaseModel):
    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int


class Message(BaseModel):
    message: str


class ErrorDetail(BaseModel):
    code: str
    message: str
    errors: list[dict] | None = None


class ErrorResponse(BaseModel):
    detail: ErrorDetail


ERROR_RESPONSES = {status: {"model": ErrorResponse} for status in
                   (400, 401, 403, 404, 409, 413, 422, 429, 500, 503)}


def page_result[T](items: list[T], total: int, page: int, page_size: int) -> dict:
    return {"items": items, "total": total, "page": page, "page_size": page_size,
            "pages": (total + page_size - 1) // page_size}
