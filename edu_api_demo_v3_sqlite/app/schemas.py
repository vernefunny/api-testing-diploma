from datetime import date
import re

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 64
MIN_AGE = 18
MAX_AGE = 120


def calculate_age(birth_date: date, today: date | None = None) -> int:
    today = today or date.today()
    age = today.year - birth_date.year
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1
    return age


def validate_password_policy(value: str) -> str:
    if len(value) < MIN_PASSWORD_LENGTH:
        raise ValueError("Password must contain at least 8 characters.")
    if len(value) > MAX_PASSWORD_LENGTH:
        raise ValueError("Password must not be longer than 64 characters.")
    if not re.search(r"\d", value):
        raise ValueError("Password must contain at least one digit.")
    if not re.search(r"[^\w\s]", value, flags=re.UNICODE):
        raise ValueError("Password must contain at least one special character.")
    return value


def validate_birth_date(value: date) -> date:
    if value > date.today():
        raise ValueError("Birth date cannot be in the future.")
    age = calculate_age(value)
    if age < MIN_AGE:
        raise ValueError("User must be at least 18 years old.")
    if age > MAX_AGE:
        raise ValueError("User age must not be greater than 120 years.")
    return value


class RegisterStudentRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: EmailStr
    password: str = Field(min_length=8, max_length=64)
    password_confirmation: str = Field(min_length=8, max_length=64)
    full_name: str = Field(min_length=2, max_length=100)
    birth_date: date
    receive_marketing_messages: bool = False

    @field_validator("password")
    @classmethod
    def password_strength(cls, value: str) -> str:
        return validate_password_policy(value)

    @field_validator("birth_date")
    @classmethod
    def birth_date_rules(cls, value: date) -> date:
        return validate_birth_date(value)

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.password_confirmation:
            raise ValueError("Password confirmation does not match password.")
        return self


class LoginStudentRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=64)


class EditProfileRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=100)
    birth_date: date | None = None
    receive_marketing_messages: bool | None = None

    @field_validator("birth_date")
    @classmethod
    def birth_date_rules(cls, value: date | None) -> date | None:
        if value is None:
            return None
        return validate_birth_date(value)


class SetInterestsRequest(BaseModel):
    interestIds: list[int] = Field(min_length=1, max_length=10)

    @field_validator("interestIds")
    @classmethod
    def validate_interests(cls, value: list[int]) -> list[int]:
        if len(value) != len(set(value)):
            raise ValueError("Interest IDs must be unique.")
        if any(item <= 0 for item in value):
            raise ValueError("Interest IDs must be positive integers.")
        return value


class SetRatingRequest(BaseModel):
    rating: float = Field(ge=1.0, le=5.0)
    comment: str | None = Field(default=None, max_length=500)


class ComplaintRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=100)
    text: str = Field(min_length=10, max_length=1000)
    link: str | None = Field(default=None, max_length=300)


class SupportEmailRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=100)
    text: str = Field(min_length=10, max_length=1000)
    email: EmailStr


class InstallmentRequest(BaseModel):
    installments_count: int = Field(ge=2, le=36)
    installments_term: int = Field(ge=1, le=36)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
