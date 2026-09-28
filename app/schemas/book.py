# Pydantic schemas for books (Pydantic v2).

from pydantic import BaseModel, ConfigDict, Field, model_validator


class BookBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(..., min_length=1, max_length=200, examples=["Harry Potter"])
    author: str = Field(..., min_length=1, max_length=150, examples=["J.K. Rowling"])
    isbn: str = Field(..., min_length=1, max_length=20, examples=["9780747532699"])
    category_id: int = Field(..., ge=1, examples=[1])
    total_copies: int = Field(..., ge=0, examples=[5])        # cannot be negative
    available_copies: int = Field(..., ge=0, examples=[5])    # cannot be negative
    published_year: int = Field(..., ge=1000, le=2100, examples=[1997])

    @model_validator(mode="after")
    def check_copies(self):
        # This runs after every field is valid. It compares two fields.
        if self.available_copies > self.total_copies:
            raise ValueError("available_copies cannot be greater than total_copies")
        return self


class BookCreate(BookBase):
    """Data the client sends when creating a book."""
    pass


class BookUpdate(BookBase):
    """Data the client sends when updating a book (PUT)."""
    pass


class BookResponse(BookBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
