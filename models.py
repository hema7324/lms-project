from dataclasses import dataclass
from datetime import datetime

@dataclass
class User:
    id: int
    username: str
    password: str
    role: str
    name: str

@dataclass
class Book:
    id: int
    title: str
    author: str
    keywords: str
    total_copies: int
    available_copies: int

@dataclass
class Request:
    id: int
    user_id: int
    book_id: int
    type: str
    status: str
    timestamp: datetime

@dataclass
class IssuedBook:
    id: int
    user_id: int
    book_id: int
    issue_date: datetime
    due_date: datetime
