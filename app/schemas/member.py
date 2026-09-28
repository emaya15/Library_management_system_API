# Pydantic schemas for members (Pydantic v2).

from datetime import date

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class MemberBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(..., min_length=1, max_length=100, examples=["Emaya"])
    email: EmailStr = Field(..., examples=["emaya@example.com"])  # checked by Pydantic
    phone: str = Field(..., examples=["+919876543210"])
    address: str = Field(..., min_length=1, max_length=255, examples=["12 Anna Nagar, Chennai"])
    membership_date: date = Field(..., examples=["2026-01-15"])
    is_active: bool = True

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        # Simple rule: optional "+" at the start, then 10 to 15 digits.
        # Spaces and dashes are allowed in the input and removed.
        cleaned = value.replace(" ", "").replace("-", "")
        digits = cleaned[1:] if cleaned.startswith("+") else cleaned

        if not digits.isdigit():
            raise ValueError("Phone number must contain only digits (optional + at the start)")
        if not 10 <= len(digits) <= 15:
            raise ValueError("Phone number must have 10 to 15 digits")
        return cleaned


class MemberCreate(MemberBase):
    """Data the client sends when creating a member."""
    pass


class MemberUpdate(MemberBase):
    """Data the client sends when updating a member (PUT)."""
    pass


class MemberResponse(MemberBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
