# Book endpoints: create, list/search, get one, update, delete.

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.book import Book
from app.models.borrow import Borrow
from app.models.category import Category
from app.schemas.book import BookCreate, BookResponse, BookUpdate

router = APIRouter(tags=["Books"])


@router.post("/books", response_model=BookResponse, status_code=201)
def create_book(book: BookCreate, db: Session = Depends(get_db)):
    # category_id must exist
    category = db.query(Category).filter(Category.id == book.category_id).first()
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")

    # ISBN must be unique
    if db.query(Book).filter(Book.isbn == book.isbn).first():
        raise HTTPException(status_code=409, detail="ISBN already exists")

    new_book = Book(**book.model_dump())
    db.add(new_book)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="ISBN already exists")

    db.refresh(new_book)
    return new_book


@router.get("/books", response_model=list[BookResponse])
def get_books(
    title: Optional[str] = Query(None, description="Partial title match"),
    author: Optional[str] = Query(None, description="Partial author match"),
    category_id: Optional[int] = Query(None, ge=1, description="Exact category id"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Book)

    # Add a filter only when the user sent that query parameter.
    if title:
        query = query.filter(Book.title.ilike(f"%{title}%"))    # contains, case-insensitive
    if author:
        query = query.filter(Book.author.ilike(f"%{author}%"))
    if category_id:
        query = query.filter(Book.category_id == category_id)

    return query.order_by(Book.id).offset(skip).limit(limit).all()


@router.get("/books/{book_id}", response_model=BookResponse)
def get_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@router.put("/books/{book_id}", response_model=BookResponse)
def update_book(book_id: int, data: BookUpdate, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    # Category must exist
    if db.query(Category).filter(Category.id == data.category_id).first() is None:
        raise HTTPException(status_code=404, detail="Category not found")

    # ISBN must not belong to a DIFFERENT book
    duplicate = db.query(Book).filter(Book.isbn == data.isbn, Book.id != book_id).first()
    if duplicate:
        raise HTTPException(status_code=409, detail="ISBN already exists")

    # Copies that are currently borrowed are not on the shelf, so
    # available_copies cannot be higher than total_copies - borrowed copies.
    borrowed_now = (
        db.query(Borrow)
        .filter(Borrow.book_id == book_id, Borrow.return_date.is_(None))
        .count()
    )
    if data.available_copies > data.total_copies - borrowed_now:
        raise HTTPException(
            status_code=400,
            detail=(
                "available_copies cannot be more than total_copies minus "
                f"the copies currently borrowed ({borrowed_now})"
            ),
        )

    book.title = data.title
    book.author = data.author
    book.isbn = data.isbn
    book.category_id = data.category_id
    book.total_copies = data.total_copies
    book.available_copies = data.available_copies
    book.published_year = data.published_year

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="ISBN already exists")

    db.refresh(book)
    return book


@router.delete("/books/{book_id}")
def delete_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    # Rule 1: cannot delete while someone still has the book
    active = (
        db.query(Borrow)
        .filter(Borrow.book_id == book_id, Borrow.return_date.is_(None))
        .first()
    )
    if active:
        raise HTTPException(
            status_code=409,
            detail="Book cannot be deleted because it is currently borrowed",
        )

    # Rule 2 (safe alternative): keep old history intact, so block deletion too.
    history = db.query(Borrow).filter(Borrow.book_id == book_id).first()
    if history:
        raise HTTPException(
            status_code=409,
            detail="Book cannot be deleted because it has borrow history",
        )

    db.delete(book)
    db.commit()
    return {"message": "Book deleted successfully"}
