# Category endpoints: create, list, update, delete.

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.book import Book
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate

router = APIRouter(tags=["Categories"])


@router.post("/categories", response_model=CategoryResponse, status_code=201)
def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    # category_name must be unique
    existing = db.query(Category).filter(Category.category_name == category.category_name).first()
    if existing:
        raise HTTPException(status_code=409, detail="Category name already exists")

    new_category = Category(**category.model_dump())
    db.add(new_category)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Category name already exists")

    db.refresh(new_category)
    return new_category


@router.get("/categories", response_model=list[CategoryResponse])
def get_categories(
    skip: int = Query(0, ge=0, description="How many records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Max records to return"),
    db: Session = Depends(get_db),
):
    return db.query(Category).order_by(Category.id).offset(skip).limit(limit).all()


@router.put("/categories/{category_id}", response_model=CategoryResponse)
def update_category(category_id: int, data: CategoryUpdate, db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.id == category_id).first()
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")

    # New name must not belong to a DIFFERENT category
    duplicate = (
        db.query(Category)
        .filter(Category.category_name == data.category_name, Category.id != category_id)
        .first()
    )
    if duplicate:
        raise HTTPException(status_code=409, detail="Category name already exists")

    category.category_name = data.category_name
    category.description = data.description
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Category name already exists")

    db.refresh(category)
    return category


@router.delete("/categories/{category_id}")
def delete_category(category_id: int, db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.id == category_id).first()
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")

    # Safe rule: a category that still has books cannot be deleted.
    has_books = db.query(Book).filter(Book.category_id == category_id).first()
    if has_books:
        raise HTTPException(
            status_code=409,
            detail="Category cannot be deleted because it still has books",
        )

    db.delete(category)
    db.commit()
    return {"message": "Category deleted successfully"}
