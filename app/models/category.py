# Category model = the "categories" table in MySQL.

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    category_name = Column(String(100), unique=True, nullable=False)  # must be unique
    description = Column(String(255), nullable=True)                  # optional

    # One Category -> Many Books
    books = relationship("Book", back_populates="category")
