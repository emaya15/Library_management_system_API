# Borrow model = the "borrow_records" table in MySQL.
# Each row means: "this member borrowed this book on this date".

from sqlalchemy import Column, Date, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base

# The three allowed status values.
STATUS_BORROWED = "Borrowed"
STATUS_RETURNED = "Returned"
STATUS_OVERDUE = "Overdue"


class Borrow(Base):
    __tablename__ = "borrow_records"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    borrow_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    return_date = Column(Date, nullable=True)  # NULL until the book is returned
    status = Column(String(20), nullable=False, default=STATUS_BORROWED)

    # Many Borrow records -> One Book / One Member
    book = relationship("Book", back_populates="borrow_records")
    member = relationship("Member", back_populates="borrow_records")
