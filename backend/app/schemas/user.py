from pydantic import BaseModel, Field


class UserUpdateRequest(BaseModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=120)
    telefono: str | None = Field(default=None, max_length=20)


class PasswordChangeRequest(BaseModel):
    password_actual: str = Field(min_length=1, max_length=128)
    password_nueva: str = Field(min_length=8, max_length=128)
