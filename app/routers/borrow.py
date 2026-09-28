# Borrow / return endpoints. The real logic is in services/borrow_service.py.

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.borrow import (
    BorrowCreate,
    BorrowHistoryResponse,
    BorrowResponse,
    MemberBookResponse,
    OverdueResponse,
)
from app.services import borrow_service

router = APIRouter(tags=["Borrow and Return"])


@router.post("/borrow", response_model=BorrowResponse, status_code=201)
def borrow_book(data: BorrowCreate, db: Session = Depends(get_db)):
    return borrow_service.borrow_book(db, data)


@router.put("/return/{borrow_id}", response_model=BorrowResponse)
def return_book(borrow_id: int, db: Session = Depends(get_db)):
    return borrow_service.return_book(db, borrow_id)


@router.get("/members/{member_id}/books", response_model=list[MemberBookResponse])
def get_member_books(member_id: int, db: Session = Depends(get_db)):
    return borrow_service.get_member_active_books(db, member_id)


@router.get("/books/{book_id}/borrow-history", response_model=list[BorrowHistoryResponse])
def get_book_borrow_history(book_id: int, db: Session = Depends(get_db)):
    return borrow_service.get_book_borrow_history(db, book_id)


@router.get("/borrow/overdue", response_model=list[OverdueResponse])
def get_overdue(db: Session = Depends(get_db)):
    return borrow_service.get_overdue_records(db)
