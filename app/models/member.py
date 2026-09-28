# Member model = the "members" table in MySQL.

from sqlalchemy import Boolean, Column, Date, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Member(Base):
    __tablename__ = "members"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    phone = Column(String(20), nullable=False)
    address = Column(String(255), nullable=False)
    membership_date = Column(Date, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)

    # One Member -> Many Borrow records
    borrow_records = relationship("Borrow", back_populates="member")
