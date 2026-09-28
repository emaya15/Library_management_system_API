# Member endpoints: create, list, get one, update, delete.

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.borrow import Borrow
from app.models.member import Member
from app.schemas.member import MemberCreate, MemberResponse, MemberUpdate

router = APIRouter(tags=["Members"])


@router.post("/members", response_model=MemberResponse, status_code=201)
def create_member(member: MemberCreate, db: Session = Depends(get_db)):
    # Email must be unique
    if db.query(Member).filter(Member.email == member.email).first():
        raise HTTPException(status_code=409, detail="Email already exists")

    new_member = Member(**member.model_dump())
    db.add(new_member)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Email already exists")

    db.refresh(new_member)
    return new_member


@router.get("/members", response_model=list[MemberResponse])
def get_members(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return db.query(Member).order_by(Member.id).offset(skip).limit(limit).all()


@router.get("/members/{member_id}", response_model=MemberResponse)
def get_member(member_id: int, db: Session = Depends(get_db)):
    member = db.query(Member).filter(Member.id == member_id).first()
    if member is None:
        raise HTTPException(status_code=404, detail="Member not found")
    return member


@router.put("/members/{member_id}", response_model=MemberResponse)
def update_member(member_id: int, data: MemberUpdate, db: Session = Depends(get_db)):
    member = db.query(Member).filter(Member.id == member_id).first()
    if member is None:
        raise HTTPException(status_code=404, detail="Member not found")

    # Email must not belong to a DIFFERENT member
    duplicate = (
        db.query(Member).filter(Member.email == data.email, Member.id != member_id).first()
    )
    if duplicate:
        raise HTTPException(status_code=409, detail="Email already exists")

    member.name = data.name
    member.email = data.email
    member.phone = data.phone
    member.address = data.address
    member.membership_date = data.membership_date
    member.is_active = data.is_active

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Email already exists")

    db.refresh(member)
    return member


@router.delete("/members/{member_id}")
def delete_member(member_id: int, db: Session = Depends(get_db)):
    member = db.query(Member).filter(Member.id == member_id).first()
    if member is None:
        raise HTTPException(status_code=404, detail="Member not found")

    # Cannot delete a member who still holds a book
    active = (
        db.query(Borrow)
        .filter(Borrow.member_id == member_id, Borrow.return_date.is_(None))
        .first()
    )
    if active:
        raise HTTPException(
            status_code=409,
            detail="Member cannot be deleted because they have borrowed books",
        )

    # Safe alternative: keep borrow history. Deactivate instead (PUT is_active=false).
    history = db.query(Borrow).filter(Borrow.member_id == member_id).first()
    if history:
        raise HTTPException(
            status_code=409,
            detail="Member has borrow history and cannot be deleted. Set is_active to false instead",
        )

    db.delete(member)
    db.commit()
    return {"message": "Member deleted successfully"}
