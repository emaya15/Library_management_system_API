# Importing every model here makes sure SQLAlchemy "knows" about all tables
# before Base.metadata.create_all() runs in main.py.
from app.models.category import Category
from app.models.book import Book
from app.models.member import Member
from app.models.borrow import Borrow

__all__ = ["Category", "Book", "Member", "Borrow"]
