from pydantic import BaseModel, EmailStr


class UserOTPResponse(BaseModel):
    message: str
    otp_valid_time: str


class UserRegisterRequest(BaseModel):
    email: EmailStr
