from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class UserSchema(BaseModel):
    id: str
    name: str
    email: str
    phone: str
    photo: Optional[str] = None
    role: str
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class TokenSchema(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: str
    scope: str

class RegisterUserRequest(BaseModel):
    name: str
    email: str
    phone: str
    password: str

class LoginUserRequest(BaseModel):
    email_or_phone: str
    password: str