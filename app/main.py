# main.py - the entry point. Uvicorn starts the app from here:
#   uvicorn app.main:app --reload

from fastapi import FastAPI

from app import models  # noqa: F401  (loads all models so their tables get created)
from app.database import Base, engine
from app.routers import books, borrow, categories, members

# Create all tables inside the existing library_db database (if missing).
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Library Management System",
    description=(
        "A beginner-friendly FastAPI project to manage categories, books, "
        "members, and borrowing/returning of books using MySQL."
    ),
    version="1.0.0",
)

# Register every router so its endpoints appear in the app and in Swagger.
app.include_router(categories.router)
app.include_router(books.router)
app.include_router(members.router)
app.include_router(borrow.router)


@app.get("/", tags=["Home"])
def home():
    return {"message": "Library Management System API is running. Open /docs for Swagger UI."}
