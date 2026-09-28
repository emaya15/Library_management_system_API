# Book model = the "books" table in MySQL.

from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Book(Base):
    __tablename__ = "books"

    # Database-level safety rules for the copy counts.
    # (MySQL 8.0.16+ enforces these. The API also checks them in Python.)
    __table_args__ = (
        CheckConstraint("total_copies >= 0", name="check_total_copies_not_negative"),
        CheckConstraint("available_copies >= 0", name="check_available_copies_not_negative"),
        CheckConstraint("available_copies <= total_copies", name="check_available_not_above_total"),
    )

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    author = Column(String(150), nullable=False)
    isbn = Column(String(20), unique=True, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    total_copies = Column(Integer, nullable=False)
    available_copies = Column(Integer, nullable=False)
    published_year = Column(Integer, nullable=False)

    # Many Books -> One Category
    category = relationship("Category", back_populates="books")
    # One Book -> Many Borrow records
    borrow_records = relationship("Borrow", back_populates="book")
