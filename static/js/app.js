let currentToken = null;
let currentUser = null;

const API_BASE = '/api';

// UI Helpers
function showView(viewId) {
    document.querySelectorAll('.view-container').forEach(v => v.classList.remove('active'));
    document.getElementById(viewId).classList.add('active');
}

function toggleAuth(type) {
    if(type === 'login') {
        showView('login-view');
    } else {
        showView('signup-view');
    }
}

function updateGreeting() {
    const el = document.getElementById('user-greeting');
    if (currentUser) {
        el.textContent = `Welcome back, ${currentUser.name} (${currentUser.role})`;
        el.classList.remove('hidden');
    } else {
        el.classList.add('hidden');
    }
}

async function apiCall(endpoint, method = 'GET', body = null) {
    const headers = { 'Content-Type': 'application/json' };
    if (currentToken) {
        headers['x-user-id'] = currentToken;
    }
    
    const config = { method, headers };
    if (body) config.body = JSON.stringify(body);
    
    const res = await fetch(`${API_BASE}${endpoint}`, config);
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'API Error');
    return data;
}

// Auth Handlers
document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const u = document.getElementById('login-username').value;
    const p = document.getElementById('login-password').value;
    
    try {
        const data = await apiCall('/auth/login', 'POST', {username: u, password: p});
        currentToken = data.token;
        currentUser = data.user;
        updateGreeting();
        
        // if(currentUser.role === 'admin') showView('admin-view');
        // else if(currentUser.role === 'librarian') {
        //     showView('librarian-view');
        //     fetchLibrarianRequests();
        // }
        if(currentUser.role === 'admin' || currentUser.role === 'librarian') {
              showView('librarian-view');
              fetchLibrarianRequests();  // requests
              fetchUsers();
              fetchBooks();  
        }
        else {
            showView('student-view');
            fetchMyIssued();
            searchBooks(""); // load all default
        }
    } catch (err) {
        alert(err.message);
    }
});

document.getElementById('signup-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
        name: document.getElementById('signup-name').value,
        username: document.getElementById('signup-username').value,
        password: document.getElementById('signup-password').value,
        role: document.getElementById('signup-role').value
    };
    try {
        await apiCall('/auth/signup', 'POST', payload);
        alert('Signup successful! Please log in.');
        toggleAuth('login');
    } catch (err) {
        alert(err.message);
    }
});

function logout() {
    currentToken = null;
    currentUser = null;
    updateGreeting();
    showView('login-view');
}

// --- ADMIN FUNCTIONS ---
async function fetchUsers() {
    try {
        const users = await apiCall('/users', 'GET');
        const tbody = document.querySelector('#admin-users-table tbody');
        tbody.innerHTML = '';
        users.forEach(u => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${u.id}</td>
                <td>${u.username}</td>
                <td><span class="status-badge ${u.role === 'admin'? 'status-approved': 'status-pending'}">${u.role}</span></td>
                <td>${u.name}</td>
                <td>
                    ${u.role !== 'admin' ? `<button class="btn btn-danger" onclick="deleteUser('${u.username}')">Remove</button>` : 'System'}
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) { alert(err.message); }
}

async function deleteUser(username) {
    if(!confirm(`Delete user ${username}?`)) return;
    try {
        await apiCall(`/users/${username}`, 'DELETE');
        fetchUsers();
    } catch (err) { alert(err.message); }
}

document.getElementById('admin-add-user-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
        username: document.getElementById('admin-add-username').value,
        password: document.getElementById('admin-add-password').value,
        name: document.getElementById('admin-add-name').value,
        role: document.getElementById('admin-add-role').value
    };
    try {
        await apiCall('/users', 'POST', payload);
        alert('User created successfully by Admin!');
        e.target.reset();
        fetchUsers();
    } catch (err) { alert(err.message); }
});

// --- LIBRARIAN FUNCTIONS ---
document.getElementById('add-book-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
        title: document.getElementById('add-title').value,
        author: document.getElementById('add-author').value,
        keywords: document.getElementById('add-keywords').value,
        copies: parseInt(document.getElementById('add-copies').value)
    };
    try {
        await apiCall('/books', 'POST', payload);
        alert('Book added successfully');
        e.target.reset();
    } catch (err) { alert(err.message); }
});

async function fetchLibrarianRequests() {
    try {
        const reqs = await apiCall('/requests/pending', 'GET');
        const tbody = document.querySelector('#librarian-req-table tbody');
        tbody.innerHTML = '';
        reqs.forEach(r => {
            const tr = document.createElement('tr');
            // tr.innerHTML = `
            //     <td>${r.id}</td>
            //     <td>${r.username}</td>
            //     <td>${r.book_title}</td>
            //     <td><strong>${r.type.toUpperCase()}</strong></td>
            //     <td>${new Date(r.timestamp).toLocaleString()}</td>
            //     <td style="display:flex; gap:5px;">
            //         <button class="btn btn-success" onclick="handleReq(${r.id}, 'approved')">Approve</button>
            //         <button class="btn btn-danger" onclick="handleReq(${r.id}, 'rejected')">Reject</button>
            //     </td>
            // `;
            tr.innerHTML = `
                <td>${r.id}</td>
                <td>${r.username}</td>
                <td>${r.book_title}</td>
                <td>${r.type}</td>
                <td>${new Date(r.timestamp).toLocaleString()}</td>
                <td style="color:${(r.fine || 0) > 0 ? 'red' : 'lightgreen'}">
                    ₹${r.fine ? r.fine : 0}
                </td>
                <td style="display:flex; gap:5px;">
                    <button class="btn btn-success" onclick="handleReq(${r.id}, 'approved')">Approve</button>
                    <button class="btn btn-danger" onclick="handleReq(${r.id}, 'rejected')">Reject</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) { alert(err.message); }
}

async function handleReq(id, action) {
    try {
        await apiCall(`/requests/handle/${id}`, 'POST', {action});
        fetchLibrarianRequests();
    } catch (err) { alert(err.message); }
}

// --- STUDENT FUNCTIONS ---
async function searchBooks(queryOverride = null) {
    const query = queryOverride !== null ? queryOverride : document.getElementById('search-query').value;
    try {
        const books = await apiCall(`/books?query=${encodeURIComponent(query)}`, 'GET');
        const tbody = document.querySelector('#search-results-table tbody');
        tbody.innerHTML = '';
        books.forEach(b => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${b.title}</td>
                <td>${b.author}</td>
                <td>${b.available_copies} / ${b.total_copies}</td>
                <td>
                    <button class="btn" style="padding: 0.4rem 0.8rem;" onclick="requestBook(${b.id}, 'issue')">Request Issue</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) { alert(err.message); }
}

async function fetchMyIssued() {
    try {
        const issued = await apiCall('/issued', 'GET');
        const tbody = document.querySelector('#my-issued-table tbody');
        const totalFineElement = document.getElementById('total-fine');
        let totalFine = 0;
        tbody.innerHTML = '';
        issued.forEach(ib => {
            const tr = document.createElement('tr');
            // tr.innerHTML = `
            //     <td>${ib.title}</td>
            //     <td>${new Date(ib.due_date).toLocaleDateString()}</td>
            //     <td style="display:flex; gap:5px;">
            //         <button class="btn" style="padding:0.4rem;" onclick="requestBook(${ib.book_id}, 'renew')">Renew</button>
            //         <button class="btn btn-danger" style="padding:0.4rem;" onclick="requestBook(${ib.book_id}, 'return')">Return</button>
            //     </td>
            // `;
            totalFine += ib.fine || 0;
            tr.innerHTML = `
                <td>${ib.title}</td>
                <td>${new Date(ib.due_date).toLocaleDateString()}</td>
                <td style="color:${(ib.fine || 0 )>0? 'red' : 'lightgreen'}">
                    ₹${ib.fine || 0}
                </td>
                <td style="display:flex; gap:5px;">
                    <button onclick="requestBook(${ib.book_id}, 'renew')">Renew</button>
                    <button onclick="requestBook(${ib.book_id}, 'return')">Return</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
        document.getElementById('total-fine').innerText = "Total Fine: ₹" + totalFine;
    } catch (err) { alert(err.message); }
}

async function requestBook(bookId, type) {
    try {
        await apiCall(`/requests/${bookId}/${type}`, 'POST');
        alert(`${type} request submitted!`);
    } catch (err) { alert(err.message); }
}
async function fetchBooks() {
    try {
        const books = await apiCall('/books', 'GET');

        const tbody = document.querySelector('#books-table tbody');
        tbody.innerHTML = '';

        books.forEach(b => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${b.id}</td>
                <td>${b.title}</td>
                <td>${b.author}</td>
                <td>${b.available_copies}</td>
                <td>${b.total_copies}</td>
                <td>
                    <button class="btn btn-danger" onclick="deleteBook(${b.id})">Delete</button>
                </td>
            `;
            tbody.appendChild(tr);
        });

    } catch (err) {
        alert(err.message);
    }
}
async function deleteBook(bookId) {
    if(!confirm("Are you sure you want to delete this book?")) return;

    try {
        await apiCall(`/books/${bookId}`, 'DELETE');
        alert("Book deleted successfully");

        fetchBooks(); // refresh table
    } catch (err) {
        alert(err.message);
    }
}