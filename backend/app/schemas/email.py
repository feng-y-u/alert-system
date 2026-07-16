from pydantic import BaseModel


class EmailConfigStatus(BaseModel):
    configured: bool
    host: str
    port: int
    has_user: bool
    from_addr: str
    note: str = ""


class EmailTestResult(BaseModel):
    success: bool
    message: str
