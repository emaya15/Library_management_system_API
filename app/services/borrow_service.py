# borrow_service.py
# ------------------------------------------------------------
# All borrow / return business rules live here, so the router
# stays short and only handles the HTTP part.
#
# Important idea used in this file:
#   A borrow record is ACTIVE (book still with the member) when
#   return_date is NULL. Once the book is returned, return_date is set.
# ------------------------------------------------------------

from datetime import date, timedelta

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.book import Book
from app.models.borrow import STATUS_BORROWED, STATUS_OVERDUE, STATUS_RETURNED, Borrow
from app.models.member import Member
from app.schemas.borrow import (
    BorrowCreate,
    BorrowHistoryResponse,
    MemberBookResponse,
    OverdueResponse,
)

MAX_BOOKS_PER_MEMBER = 3   # a member can hold at most 3 books at once
LOAN_DAYS = 14             # due date = borrow date + 14 days


def borrow_book(db: Session, data: BorrowCreate) -> Borrow:
    """Create a new borrow record after checking every rule."""

    # 1-2. Member must exist
    member = db.query(Member).filter(Member.id == data.member_id).first()
    if member is None:
        raise HTTPException(status_code=404, detail="Member not found")

    # 3-4. Member must be active
    if not member.is_active:
        raise HTTPException(status_code=400, detail="Member is not active")

    # 5-6. Book must exist.
    # with_for_update() locks this book row until we commit, so two people
    # cannot borrow the last copy at the same moment.
    book = db.query(Book).filter(Book.id == data.book_id).with_for_update().first()
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    # 7-8. There must be a copy available
    if book.available_copies <= 0:
        raise HTTPException(status_code=400, detail="No available copies")

    # 9. Max 3 active borrows per member
    active_count = (
        db.query(Borrow)
        .filter(Borrow.member_id == member.id, Borrow.return_date.is_(None))
        .count()
    )
    if active_count >= MAX_BOOKS_PER_MEMBER:
        raise HTTPException(status_code=409, detail="Member cannot borrow more than 3 books")

    # 10. Same book cannot be borrowed twice while the first borrow is active
    same_book = (
        db.query(Borrow)
        .filter(
            Borrow.member_id == member.id,
            Borrow.book_id == book.id,
            Borrow.return_date.is_(None),
        )
        .first()
    )
    if same_book is not None:
        raise HTTPException(status_code=409, detail="Member has already borrowed this book")

    # 11-15. Create the record and reduce available copies
    borrow_date = data.borrow_date or date.today()
    new_borrow = Borrow(
        book_id=book.id,
        member_id=member.id,
        borrow_date=borrow_date,
        due_date=borrow_date + timedelta(days=LOAN_DAYS),
        return_date=None,
        status=STATUS_BORROWED,
    )
    book.available_copies = book.available_copies - 1

    try:
        db.add(new_borrow)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Could not save the borrow record")

    db.refresh(new_borrow)
    return new_borrow


def return_book(db: Session, borrow_id: int) -> Borrow:
    """Mark a borrow record as returned."""

    # 1-2. Borrow record must exist
    borrow = db.query(Borrow).filter(Borrow.id == borrow_id).first()
    if borrow is None:
        raise HTTPException(status_code=404, detail="Borrow record not found")

    # 3-4. Cannot return twice
    if borrow.return_date is not None:
        raise HTTPException(status_code=400, detail="This book has already been returned")

    # 5. Set the return date to today
    today = date.today()
    borrow.return_date = today

    # 6. Put the copy back on the shelf (never above total_copies)
    book = db.query(Book).filter(Book.id == borrow.book_id).with_for_update().first()
    if book.available_copies < book.total_copies:
        book.available_copies = book.available_copies + 1

    # 7-8. Late return -> Overdue, on-time return -> Returned
    if today > borrow.due_date:
        borrow.status = STATUS_OVERDUE
    else:
        borrow.status = STATUS_RETURNED

    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Could not update the borrow record")

    db.refresh(borrow)
    return borrow


def get_member_active_books(db: Session, member_id: int) -> list:
    """Books a member currently has (only active borrow records)."""
    member = db.query(Member).filter(Member.id == member_id).first()
    if member is None:
        raise HTTPException(status_code=404, detail="Member not found")

    records = (
        db.query(Borrow)
        .filter(Borrow.member_id == member_id, Borrow.return_date.is_(None))
        .order_by(Borrow.id)
        .all()
    )

    result = []
    for record in records:
        result.append(
            MemberBookResponse(
                borrow_id=record.id,
                book_id=record.book.id,
                title=record.book.title,
                author=record.book.author,
                isbn=record.book.isbn,
                borrow_date=record.borrow_date,
                due_date=record.due_date,
                status=record.status,
            )
        )
    return result


def get_book_borrow_history(db: Session, book_id: int) -> list:
    """Every borrow record of one book, newest first."""
    book = db.query(Book).filter(Book.id == book_id).first()
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    records = (
        db.query(Borrow)
        .filter(Borrow.book_id == book_id)
        .order_by(Borrow.id.desc())
        .all()
    )

    result = []
    for record in records:
        result.append(
            BorrowHistoryResponse(
                borrow_id=record.id,
                member_id=record.member.id,
                member_name=record.member.name,
                borrow_date=record.borrow_date,
                due_date=record.due_date,
                return_date=record.return_date,
                status=record.status,
            )
        )
    return result


def get_overdue_records(db: Session) -> list:
    """Books not returned yet whose due date is before today.
    Their status is also updated from Borrowed to Overdue in the database."""
    today = date.today()

    records = (
        db.query(Borrow)
        .filter(Borrow.return_date.is_(None), Borrow.due_date < today)
        .order_by(Borrow.due_date)
        .all()
    )

    # Update the status so the database reflects reality
    for record in records:
        if record.status == STATUS_BORROWED:
            record.status = STATUS_OVERDUE

    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Could not update overdue records")

    result = []
    for record in records:
        result.append(
            OverdueResponse(
                borrow_id=record.id,
                book_id=record.book.id,
                book_title=record.book.title,
                member_id=record.member.id,
                member_name=record.member.name,
                borrow_date=record.borrow_date,
                due_date=record.due_date,
                days_overdue=(today - record.due_date).days,
                status=record.status,
            )
        )
    return result
