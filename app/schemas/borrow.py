# Pydantic schemas for borrowing and returning books (Pydantic v2).

from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BorrowCreate(BaseModel):
    """What the client sends to POST /borrow."""
    book_id: int = Field(..., ge=1, examples=[1])
    member_id: int = Field(..., ge=1, examples=[1])
    # Optional. If missing, the service uses today's date.
    borrow_date: Optional[date] = None

    @field_validator("borrow_date")
    @classmethod
    def borrow_date_not_in_future(cls, value):
        if value is not None and value > date.today():
            raise ValueError("borrow_date cannot be in the future")
        return value


class BorrowResponse(BaseModel):
    """A borrow record exactly as stored in the database."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    book_id: int
    member_id: int
    borrow_date: date
    due_date: date
    return_date: Optional[date] = None
    status: str


class MemberBookResponse(BaseModel):
    """One book currently borrowed by a member (GET /members/{id}/books)."""
    borrow_id: int
    book_id: int
    title: str
    author: str
    isbn: str
    borrow_date: date
    due_date: date
    status: str


class BorrowHistoryResponse(BaseModel):
    """One row of a book's history (GET /books/{id}/borrow-history)."""
    borrow_id: int
    member_id: int
    member_name: str
    borrow_date: date
    due_date: date
    return_date: Optional[date] = None
    status: str


class OverdueResponse(BaseModel):
    """One overdue record (GET /borrow/overdue)."""
    borrow_id: int
    book_id: int
    book_title: str
    member_id: int
    member_name: str
    borrow_date: date
    due_date: date
    days_overdue: int
    status: str
