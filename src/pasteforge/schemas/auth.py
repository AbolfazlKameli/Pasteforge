from pydantic import BaseModel, EmailStr


class UserOTPResponse(BaseModel):
    message: str
    otp_valid_time: int


class UserRegisterRequest(BaseModel):
    email: EmailStr
