# Pydantic schemas for categories (Pydantic v2).

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CategoryBase(BaseModel):
    # str_strip_whitespace removes accidental spaces at the start/end of text
    model_config = ConfigDict(str_strip_whitespace=True)

    category_name: str = Field(..., min_length=1, max_length=100, examples=["Fiction"])
    description: Optional[str] = Field(None, max_length=255, examples=["Novels and stories"])


class CategoryCreate(CategoryBase):
    """Data the client sends when creating a category."""
    pass


class CategoryUpdate(CategoryBase):
    """Data the client sends when updating a category (PUT)."""
    pass


class CategoryResponse(CategoryBase):
    """Data we send back. from_attributes lets Pydantic read SQLAlchemy objects."""
    model_config = ConfigDict(from_attributes=True)

    id: int
