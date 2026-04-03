import services
import auth

def admin_menu(user):
    while True:
        print("\n--- Admin Menu ---")
        print("1. Add User")
        print("2. Remove User")
        print("3. View All Users")
        print("4. Logout")
        choice = input("Select an option: ")
        
        if choice == '1':
            username = input("Username: ")
            password = input("Password: ")
            role = input("Role (admin/librarian/student/faculty): ")
            name = input("Full Name: ")
            if services.add_user(username, password, role, name):
                print(f"User {username} added successfully.")
            else:
                print("Failed to add user.")
        elif choice == '2':
            username = input("Enter username to remove: ")
            if services.delete_user(username):
                print(f"User {username} deleted successfully.")
            else:
                print("Failed to delete user or user not found.")
        elif choice == '3':
            users = services.get_all_users()
            print(f"\nTotal users: {len(users)}")
            for u in users:
                print(f"ID: {u.id} | Username: {u.username} | Role: {u.role} | Name: {u.name}")
        elif choice == '4':
            print("Logging out...")
            break
        else:
            print("Invalid option.")

def librarian_menu(user):
    while True:
        print("\n--- Librarian Menu ---")
        print("1. Add Book")
        print("2. Remove Book")
        print("3. Search Books")
        print("4. View Pending Requests")
        print("5. Approve/Reject Request")
        print("6. Logout")
        choice = input("Select an option: ")
        
        if choice == '1':
            title = input("Title: ")
            author = input("Author: ")
            keywords = input("Keywords (comma separated): ")
            try:
                copies = int(input("Total Copies: "))
                if services.add_book(title, author, keywords, copies):
                    print("Book added successfully.")
                else:
                    print("Failed to add book.")
            except ValueError:
                print("Invalid input for copies.")
        elif choice == '2':
            try:
                book_id = int(input("Enter Book ID to remove: "))
                if services.remove_book(book_id):
                    print("Book removed successfully.")
                else:
                    print("Failed to remove book.")
            except ValueError:
                print("Invalid input.")
        elif choice == '3':
            query = input("Search by title, author, or keyword: ")
            books = services.search_books(query)
            if not books: print("No books found.")
            for b in books:
                print(f"ID: {b.id} | Title: {b.title} | Author: {b.author} | Available: {b.available_copies}/{b.total_copies}")
        elif choice == '4':
            requests = services.get_pending_requests()
            if not requests: print("No pending requests.")
            for r in requests:
                username = services.get_username_by_id(r.user_id)
                book = services.get_book_by_id(r.book_id)
                book_title = book.title if book else "Unknown"
                print(f"Req ID: {r.id} | User: {username} | Book: {book_title} | Type: {r.type} | Time: {r.timestamp}")
        elif choice == '5':
            try:
                req_id = int(input("Enter Request ID: "))
                action = input("Action (a = approve / r = reject): ").lower()
                status = 'approved' if action == 'a' else 'rejected' if action == 'r' else None
                if status:
                    if services.handle_request(req_id, status):
                        print(f"Request {status}.")
                    else:
                        print("Failed to handle request.")
                else:
                    print("Invalid action.")
            except ValueError:
                print("Invalid input.")
        elif choice == '6':
            print("Logging out...")
            break
        else:
            print("Invalid option.")

def student_menu(user):
    while True:
        print(f"\n--- {user.role.capitalize()} Menu ---")
        print("1. Search Books")
        print("2. Request Issue Book")
        print("3. View Issued Books")
        print("4. Request Return Book")
        print("5. Request Renew Book")
        print("6. Logout")
        choice = input("Select an option: ")
        
        if choice == '1':
            query = input("Search by title, author, or keyword: ")
            books = services.search_books(query)
            if not books: print("No books found.")
            for b in books:
                print(f"ID: {b.id} | Title: {b.title} | Author: {b.author} | Available: {b.available_copies}/{b.total_copies}")
        elif choice == '2':
            try:
                book_id = int(input("Enter Book ID to request issue: "))
                if services.create_request(user.id, book_id, 'issue'):
                    print("Issue request submitted.")
                else:
                    print("Failed to submit request. Check book availability and ID.")
            except ValueError:
                print("Invalid input.")
        elif choice == '3':
            issued = services.get_issued_books(user.id)
            if not issued: print("You have no issued books.")
            for ib in issued:
                book = services.get_book_by_id(ib.book_id)
                book_title = book.title if book else "Unknown"
                print(f"Book ID: {ib.book_id} | Title: {book_title} | Due Date: {ib.due_date}")
        elif choice == '4':
            try:
                book_id = int(input("Enter Book ID to return: "))
                if services.create_request(user.id, book_id, 'return'):
                    print("Return request submitted.")
                else:
                    print("Failed to submit request.")
            except ValueError:
                print("Invalid input.")
        elif choice == '5':
            try:
                book_id = int(input("Enter Book ID to renew: "))
                if services.create_request(user.id, book_id, 'renew'):
                    print("Renew request submitted.")
                else:
                    print("Failed to submit request.")
            except ValueError:
                print("Invalid input.")
        elif choice == '6':
            print("Logging out...")
            break
        else:
            print("Invalid option.")
