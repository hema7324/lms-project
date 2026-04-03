from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import sys

import database
import auth
import services

app = FastAPI(title="Library Management System")

# Initialize Databases on startup
@app.on_event("startup")
def startup_event():
    print("Initializing databases...")
    if not database.init_databases():
        print("Failed to initialize databases!")
        sys.exit(1)

# Models for API requests
class LoginRequest(BaseModel):
    username: str
    password: str

class SignupRequest(BaseModel):
    username: str
    password: str
    role: str
    name: str

class BookRequest(BaseModel):
    title: str
    author: str
    keywords: str
    copies: int

class RequestHandleAction(BaseModel):
    action: str  # 'approved' or 'rejected'


# Simple Dependency for "Token" -> User
def get_current_user(x_user_id: str = Header(None)):
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = auth.get_user_by_id(int(x_user_id))
    if not user:
        raise HTTPException(status_code=401, detail="Invalid user")
    return user


@app.post("/api/auth/login")
def login(req: LoginRequest):
    user = auth.authenticate(req.username, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"token": str(user.id), "user": user}

@app.post("/api/auth/signup")
def signup(req: SignupRequest):
    if req.role not in ['student', 'faculty']:
        raise HTTPException(status_code=400, detail="Invalid role")
    if services.add_user(req.username, req.password, req.role, req.name):
        return {"success": True}
    raise HTTPException(status_code=400, detail="Username taken or error")

@app.get("/api/users")
def get_users(user = Depends(get_current_user)):
    if user.role != 'admin':
        raise HTTPException(status_code=403, detail="Unauthorized")
    return services.get_all_users()

@app.post("/api/users")
def create_user_admin(req: SignupRequest, user = Depends(get_current_user)):
    if user.role != 'admin':
        raise HTTPException(status_code=403, detail="Unauthorized")
    if services.add_user(req.username, req.password, req.role, req.name):
        return {"success": True}
    raise HTTPException(status_code=400, detail="Failed to create user (username might exist)")

@app.delete("/api/users/{username}")
def delete_user(username: str, user = Depends(get_current_user)):
    if user.role != 'admin':
        raise HTTPException(status_code=403, detail="Unauthorized")
    if services.delete_user(username):
        return {"success": True}
    raise HTTPException(status_code=400, detail="Failed to delete user")

@app.get("/api/books")
def search_books(query: str = ""):
    return services.search_books(query)

@app.post("/api/books")
def add_book(req: BookRequest, user = Depends(get_current_user)):
    if user.role not in ['librarian', 'admin']:
        raise HTTPException(status_code=403, detail="Unauthorized")
    if services.add_book(req.title, req.author, req.keywords, req.copies):
        return {"success": True}
    raise HTTPException(status_code=400, detail="Failed to add book")

@app.delete("/api/books/{book_id}")
def remove_book(book_id: int, user = Depends(get_current_user)):
    if user.role not in ['librarian', 'admin']:
        raise HTTPException(status_code=403, detail="Unauthorized")
    if services.remove_book(book_id):
        return {"success": True}
    raise HTTPException(status_code=400, detail="Failed to remove book")

@app.post("/api/requests/handle/{req_id}")
def handle_request(req_id: int, handler: RequestHandleAction, user = Depends(get_current_user)):
    if user.role not in ['librarian', 'admin']:
        raise HTTPException(status_code=403, detail="Unauthorized")
    if handler.action not in ['approved', 'rejected']:
        raise HTTPException(status_code=400, detail="Invalid action")
        
    if services.handle_request(req_id, handler.action):
        return {"success": True}
    raise HTTPException(status_code=400, detail="Failed to handle request")

@app.post("/api/requests/{book_id}/{req_type}")
def create_request(book_id: int, req_type: str, user = Depends(get_current_user)):
    if user.role in ['admin', 'librarian']:
        raise HTTPException(status_code=403, detail="Librarians and admins cannot request books")
    if req_type not in ['issue', 'return', 'renew']:
        raise HTTPException(status_code=400, detail="Invalid request type")
    
    if services.create_request(user.id, book_id, req_type):
        return {"success": True}
    raise HTTPException(status_code=400, detail="Failed to create request")

@app.get("/api/requests/pending")
def view_requests(user = Depends(get_current_user)):
    if user.role not in ['librarian', 'admin']:
        raise HTTPException(status_code=403, detail="Unauthorized")
    # reqs = services.get_pending_requests()
    
    # # attach usernames and book titles for the UI
    # enriched = []
    # for r in reqs:
    #     username = services.get_username_by_id(r['user_id'])
    #     book = services.get_book_by_id(r['book_id'])
    #     enriched.append({
    #         "id": r['id'],
    #         "username": username,
    #         "book_title": book.title if book else "Unknown",
    #         "type": r['type'],
    #         "timestamp": r['timestamp']
    #     })
    # return enriched
    return services.get_pending_requests()

@app.get("/api/issued")
def get_my_issued_books(user = Depends(get_current_user)):
        if user.role in ['admin', 'librarian']:
            raise HTTPException(status_code=403, detail="Unauthorized")
        return services.get_issued_books(user.id)

# Mount static files
import os
os.makedirs("static", exist_ok=True)
os.makedirs("static/css", exist_ok=True)
os.makedirs("static/js", exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def serve_index():
    return FileResponse("static/index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
