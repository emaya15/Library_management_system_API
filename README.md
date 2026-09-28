# Library Management System - FastAPI

## 1. Project description
A REST API built with FastAPI, SQLAlchemy and MySQL to manage a small library:
categories, books, members, and borrowing/returning of books.

## 2. Features
- Category, Book and Member CRUD (create, read, update, delete)
- Borrow and return books with business rules (3-book limit, 14-day due date, copy counts)
- Book search by title, author and category, with pagination
- Member's current books, book borrow history, overdue list
- Pydantic v2 validation and clear error messages
- Tables are created automatically when the app starts

## 3. Technologies
Python 3.9+, FastAPI, Pydantic v2, SQLAlchemy 2, MySQL, Uvicorn, pydantic-settings, pymysql>=1.1.0

## 4. Project structure
```
library_management_system/
├── app/
│   ├── __init__.py
│   ├── main.py              # creates the app, tables, includes routers
│   ├── database.py          # engine, SessionLocal, Base, get_db()
│   ├── models/              # SQLAlchemy tables
│   ├── schemas/             # Pydantic request/response models
│   ├── routers/             # API endpoints
│   └── services/borrow_service.py   # borrow/return business logic
├── .env                     # database URL (never commit!)
├── .gitignore
├── requirements.txt
└── README.md
```

## 5. MySQL database setup
Open MySQL (Workbench or terminal) and run:
```sql
CREATE DATABASE library_db;
```
The app creates the tables itself. It does NOT create the database.

## 6. `.env` setup
Open `.env` and replace `YOUR_PASSWORD` with your real MySQL password:
```
DATABASE_URL=mysql+mysqlconnector://root:YOUR_PASSWORD@localhost:3306/library_db
```
If your password contains special characters (`@ : / # ?`), URL-encode them (`@` becomes `%40`).
`.env` is listed in `.gitignore`, so your password is not uploaded to GitHub.

## 7. Virtual environment setup
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

## 8. Installation commands
```bash
pip install -r requirements.txt
```

## 9. How to run
Run from the project root folder (the one containing `app/` and `.env`):
```bash
uvicorn app.main:app --reload
```

## 10. Swagger URL
http://127.0.0.1:8000/docs

## 11. API endpoints
| Method | URL | Purpose |
|---|---|---|
| POST | /categories | Create category (201) |
| GET | /categories?skip=0&limit=10 | List categories |
| PUT | /categories/{category_id} | Update category |
| DELETE | /categories/{category_id} | Delete category (blocked if it has books) |
| POST | /books | Create book (201) |
| GET | /books?title=&author=&category_id=&skip=0&limit=10 | List/search books |
| GET | /books/{book_id} | Get one book |
| PUT | /books/{book_id} | Update book |
| DELETE | /books/{book_id} | Delete book |
| POST | /members | Create member (201) |
| GET | /members?skip=0&limit=10 | List members |
| GET | /members/{member_id} | Get one member |
| PUT | /members/{member_id} | Update member |
| DELETE | /members/{member_id} | Delete member |
| POST | /borrow | Borrow a book (201) |
| PUT | /return/{borrow_id} | Return a book |
| GET | /members/{member_id}/books | Books a member currently has |
| GET | /books/{book_id}/borrow-history | Borrow history of a book |
| GET | /borrow/overdue | Overdue borrow records |

## 12. Example API requests
Create a category:
```json
{ "category_name": "Fiction", "description": "Novels and stories" }
```
Create a book:
```json
{
  "title": "Harry Potter",
  "author": "J.K. Rowling",
  "isbn": "9780747532699",
  "category_id": 1,
  "total_copies": 5,
  "available_copies": 5,
  "published_year": 1997
}
```
Create a member:
```json
{
  "name": "Emaya",
  "email": "emaya@example.com",
  "phone": "+919876543210",
  "address": "12 Anna Nagar, Chennai",
  "membership_date": "2026-01-15",
  "is_active": true
}
```
Borrow a book:
```json
{ "book_id": 1, "member_id": 1 }
```

## 13. Business rules
- Member must exist (404) and be active (400).
- Book must exist (404) and have `available_copies` > 0 (400 "No available copies").
- A member can hold at most 3 books at once (409).
- A member cannot borrow the same book again while the first borrow is active (409).
- Borrowing reduces `available_copies` by 1; `borrow_date` defaults to today; `due_date` = borrow date + 14 days; status starts as `Borrowed`; `return_date` is NULL.
- Returning sets `return_date` to today and increases `available_copies` by 1. Late return -> status `Overdue`, on time -> `Returned`. Returning twice gives 400.
- A borrow record is "active" while `return_date` is NULL.
- `GET /borrow/overdue` lists active records with `due_date` before today and changes their status from `Borrowed` to `Overdue`.
- Deleting: a category with books, a book with active borrows (or any borrow history), and a member with active borrows (or any borrow history) cannot be deleted (409). To retire a member, set `is_active` to false with PUT.

## 14. Validation rules
- Category name unique; ISBN unique; email unique (409)
- Email format checked by Pydantic (422)
- Phone: optional `+`, then 10-15 digits (spaces and dashes allowed) (422)
- Required fields (422)
- `total_copies` >= 0, `available_copies` >= 0, `available_copies` <= `total_copies` (422)
- `skip` >= 0, `limit` between 1 and 100 (422)

## 15. Example MySQL database creation command
```sql
CREATE DATABASE library_db;
```
