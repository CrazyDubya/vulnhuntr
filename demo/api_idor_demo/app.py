"""
API Insecure Direct Object Reference (IDOR) Demo Application

This application contains intentional IDOR vulnerabilities for demonstration purposes.
DO NOT USE IN PRODUCTION - FOR EDUCATIONAL/TESTING PURPOSES ONLY.

Vulnerabilities included:
1. Direct object access without authorization
2. Predictable resource identifiers
3. Missing access controls on API endpoints
4. Privilege escalation through IDOR
5. Information disclosure via enumeration
6. Cross-user data access
7. Administrative function bypass
"""

from flask import Flask, jsonify, request, render_template_string
import sqlite3
import hashlib
import json
import logging
import os
import random
import string
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)
app.secret_key = 'demo_secret_key_unsafe'

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
DATABASE = 'demo_idor.db'

def init_database():
    """Initialize SQLite database with demo data"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            email TEXT,
            password_hash TEXT,
            role TEXT DEFAULT 'user',
            created_at TEXT,
            is_active BOOLEAN DEFAULT 1,
            profile_data TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY,
            title TEXT,
            content TEXT,
            owner_id INTEGER,
            is_private BOOLEAN DEFAULT 0,
            created_at TEXT,
            category TEXT,
            access_level TEXT DEFAULT 'public',
            FOREIGN KEY (owner_id) REFERENCES users (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            product_name TEXT,
            amount DECIMAL(10,2),
            status TEXT,
            created_at TEXT,
            shipping_address TEXT,
            payment_method TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY,
            sender_id INTEGER,
            recipient_id INTEGER,
            subject TEXT,
            content TEXT,
            sent_at TEXT,
            is_read BOOLEAN DEFAULT 0,
            FOREIGN KEY (sender_id) REFERENCES users (id),
            FOREIGN KEY (recipient_id) REFERENCES users (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            key_value TEXT UNIQUE,
            key_name TEXT,
            permissions TEXT,
            created_at TEXT,
            expires_at TEXT,
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Insert demo users
    demo_users = [
        (1, 'admin', 'admin@demo.com', hashlib.md5(b'admin123').hexdigest(), 'admin', datetime.now().isoformat(), 1, 
         '{"full_name": "Admin User", "phone": "+1-555-0001", "ssn": "123-45-6789", "salary": 150000}'),
        (2, 'john_doe', 'john@demo.com', hashlib.md5(b'password123').hexdigest(), 'user', datetime.now().isoformat(), 1,
         '{"full_name": "John Doe", "phone": "+1-555-0123", "ssn": "987-65-4321", "salary": 75000}'),
        (3, 'jane_smith', 'jane@demo.com', hashlib.md5(b'password456').hexdigest(), 'user', datetime.now().isoformat(), 1,
         '{"full_name": "Jane Smith", "phone": "+1-555-0456", "ssn": "456-78-9012", "salary": 80000}'),
        (4, 'bob_wilson', 'bob@demo.com', hashlib.md5(b'qwerty').hexdigest(), 'manager', datetime.now().isoformat(), 1,
         '{"full_name": "Bob Wilson", "phone": "+1-555-0789", "ssn": "789-01-2345", "salary": 95000}'),
        (5, 'alice_brown', 'alice@demo.com', hashlib.md5(b'secret').hexdigest(), 'user', datetime.now().isoformat(), 1,
         '{"full_name": "Alice Brown", "phone": "+1-555-0246", "ssn": "246-81-3579", "salary": 70000}')
    ]
    
    cursor.executemany('''
        INSERT OR REPLACE INTO users (id, username, email, password_hash, role, created_at, is_active, profile_data)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', demo_users)
    
    # Insert demo documents
    demo_documents = [
        (1, 'Public API Documentation', 'This is public documentation for our API...', 1, 0, datetime.now().isoformat(), 'documentation', 'public'),
        (2, 'Salary Information 2024', 'CONFIDENTIAL: Annual salary data for all employees...', 1, 1, datetime.now().isoformat(), 'hr', 'confidential'),
        (3, 'My Personal Notes', 'Personal notes and thoughts...', 2, 1, datetime.now().isoformat(), 'personal', 'private'),
        (4, 'Project Requirements', 'Requirements for the new project...', 2, 0, datetime.now().isoformat(), 'project', 'internal'),
        (5, 'Admin Security Guide', 'INTERNAL: Security procedures and admin passwords...', 1, 1, datetime.now().isoformat(), 'security', 'admin_only'),
        (6, 'Customer Database Backup', 'Complete customer database with personal info...', 4, 1, datetime.now().isoformat(), 'database', 'restricted'),
        (7, 'Meeting Minutes', 'Minutes from the weekly team meeting...', 3, 0, datetime.now().isoformat(), 'meeting', 'internal')
    ]
    
    cursor.executemany('''
        INSERT OR REPLACE INTO documents (id, title, content, owner_id, is_private, created_at, category, access_level)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', demo_documents)
    
    # Insert demo orders
    demo_orders = [
        (1, 2, 'Laptop Pro', 1299.99, 'completed', datetime.now().isoformat(), '123 Main St, Anytown, USA', 'credit_card'),
        (2, 2, 'Wireless Mouse', 29.99, 'shipped', datetime.now().isoformat(), '123 Main St, Anytown, USA', 'paypal'),
        (3, 3, 'Monitor', 399.99, 'pending', datetime.now().isoformat(), '456 Oak Ave, Other City, USA', 'credit_card'),
        (4, 4, 'Keyboard', 149.99, 'completed', datetime.now().isoformat(), '789 Pine St, Manager Town, USA', 'bank_transfer'),
        (5, 5, 'Webcam', 89.99, 'cancelled', datetime.now().isoformat(), '321 Elm St, User City, USA', 'credit_card'),
        (6, 1, 'Enterprise License', 9999.99, 'completed', datetime.now().isoformat(), '1 Admin Plaza, Admin City, USA', 'invoice')
    ]
    
    cursor.executemany('''
        INSERT OR REPLACE INTO orders (id, user_id, product_name, amount, status, created_at, shipping_address, payment_method)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', demo_orders)
    
    # Insert demo messages
    demo_messages = [
        (1, 1, 2, 'Welcome to the platform', 'Welcome John! Your account has been activated.', datetime.now().isoformat(), 1),
        (2, 2, 3, 'Project Update', 'Hi Jane, here is the latest project update...', datetime.now().isoformat(), 0),
        (3, 1, 4, 'Admin Notice', 'CONFIDENTIAL: New security protocols...', datetime.now().isoformat(), 0),
        (4, 4, 5, 'Performance Review', 'Alice, your performance review is scheduled...', datetime.now().isoformat(), 1),
        (5, 1, 1, 'System Alert', 'ADMIN: Critical system alert requires attention...', datetime.now().isoformat(), 0)
    ]
    
    cursor.executemany('''
        INSERT OR REPLACE INTO messages (id, sender_id, recipient_id, subject, content, sent_at, is_read)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', demo_messages)
    
    # Insert demo API keys
    demo_api_keys = [
        (1, 1, 'sk_admin_' + ''.join(random.choices(string.ascii_letters + string.digits, k=32)), 'Admin Master Key', 'admin,read,write,delete', datetime.now().isoformat(), (datetime.now() + timedelta(days=365)).isoformat(), 1),
        (2, 2, 'sk_user_' + ''.join(random.choices(string.ascii_letters + string.digits, k=32)), 'John Personal Key', 'read,write', datetime.now().isoformat(), (datetime.now() + timedelta(days=90)).isoformat(), 1),
        (3, 4, 'sk_mgr_' + ''.join(random.choices(string.ascii_letters + string.digits, k=32)), 'Manager Key', 'read,write,manage', datetime.now().isoformat(), (datetime.now() + timedelta(days=180)).isoformat(), 1)
    ]
    
    cursor.executemany('''
        INSERT OR REPLACE INTO api_keys (id, user_id, key_value, key_name, permissions, created_at, expires_at, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', demo_api_keys)
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_database()

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    """Main page with API documentation and test links"""
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>API IDOR Demo</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .endpoint { border: 1px solid #ccc; padding: 15px; margin: 15px 0; }
            .method { background: #007bff; color: white; padding: 2px 8px; border-radius: 3px; }
            .payload { background: #f0f0f0; padding: 5px; margin: 5px 0; font-family: monospace; }
            .vulnerability { background: #ffe6e6; padding: 10px; margin: 10px 0; }
            .warning { color: red; font-weight: bold; }
        </style>
    </head>
    <body>
        <h1>🔑 API IDOR Vulnerability Demo</h1>
        <p class="warning">⚠️ WARNING: This API contains intentional security vulnerabilities!</p>
        
        <h2>Demo Users:</h2>
        <ul>
            <li><strong>admin</strong> (ID: 1) - Administrator</li>
            <li><strong>john_doe</strong> (ID: 2) - Regular user</li>
            <li><strong>jane_smith</strong> (ID: 3) - Regular user</li>
            <li><strong>bob_wilson</strong> (ID: 4) - Manager</li>
            <li><strong>alice_brown</strong> (ID: 5) - Regular user</li>
        </ul>
        
        <h2>Vulnerable API Endpoints:</h2>
        
        <div class="endpoint">
            <h3><span class="method">GET</span> /api/users/{user_id}</h3>
            <p>Get user details by ID</p>
            <div class="payload">
                <a href="/api/users/1">GET /api/users/1</a> (Admin user)<br>
                <a href="/api/users/2">GET /api/users/2</a> (Regular user)
            </div>
            <div class="vulnerability">
                <strong>IDOR:</strong> Access any user's profile without authentication
            </div>
        </div>
        
        <div class="endpoint">
            <h3><span class="method">GET</span> /api/documents/{doc_id}</h3>
            <p>Get document by ID</p>
            <div class="payload">
                <a href="/api/documents/1">GET /api/documents/1</a> (Public doc)<br>
                <a href="/api/documents/2">GET /api/documents/2</a> (Private salary data)<br>
                <a href="/api/documents/5">GET /api/documents/5</a> (Admin security guide)
            </div>
            <div class="vulnerability">
                <strong>IDOR:</strong> Access private documents belonging to other users
            </div>
        </div>
        
        <div class="endpoint">
            <h3><span class="method">GET</span> /api/orders/{order_id}</h3>
            <p>Get order details by ID</p>
            <div class="payload">
                <a href="/api/orders/1">GET /api/orders/1</a> (John's order)<br>
                <a href="/api/orders/6">GET /api/orders/6</a> (Admin's enterprise order)
            </div>
            <div class="vulnerability">
                <strong>IDOR:</strong> View other users' order details and payment info
            </div>
        </div>
        
        <div class="endpoint">
            <h3><span class="method">GET</span> /api/messages/{message_id}</h3>
            <p>Get message by ID</p>
            <div class="payload">
                <a href="/api/messages/3">GET /api/messages/3</a> (Admin confidential notice)<br>
                <a href="/api/messages/4">GET /api/messages/4</a> (Performance review)
            </div>
            <div class="vulnerability">
                <strong>IDOR:</strong> Read private messages between other users
            </div>
        </div>
        
        <div class="endpoint">
            <h3><span class="method">GET</span> /api/api-keys/{key_id}</h3>
            <p>Get API key details by ID</p>
            <div class="payload">
                <a href="/api/api-keys/1">GET /api/api-keys/1</a> (Admin master key)<br>
                <a href="/api/api-keys/2">GET /api/api-keys/2</a> (User personal key)
            </div>
            <div class="vulnerability">
                <strong>IDOR:</strong> Access other users' API keys and permissions
            </div>
        </div>
        
        <div class="endpoint">
            <h3><span class="method">PUT</span> /api/users/{user_id}</h3>
            <p>Update user profile (POST with _method=PUT)</p>
            <div class="payload">
                <form method="post" action="/api/users/2">
                    <input type="hidden" name="_method" value="PUT">
                    User ID: <input type="number" name="user_id" value="2"><br>
                    New Email: <input type="email" name="email" value="hacked@evil.com"><br>
                    <input type="submit" value="Update User">
                </form>
            </div>
            <div class="vulnerability">
                <strong>IDOR:</strong> Modify other users' profiles without permission
            </div>
        </div>
        
        <div class="endpoint">
            <h3><span class="method">DELETE</span> /api/documents/{doc_id}</h3>
            <p>Delete document (POST with _method=DELETE)</p>
            <div class="payload">
                <form method="post" action="/api/documents/3">
                    <input type="hidden" name="_method" value="DELETE">
                    Document ID: <input type="number" name="doc_id" value="3"><br>
                    <input type="submit" value="Delete Document">
                </form>
            </div>
            <div class="vulnerability">
                <strong>IDOR:</strong> Delete other users' documents
            </div>
        </div>

        <h2>Enumeration Endpoints:</h2>
        
        <div class="endpoint">
            <h3><span class="method">GET</span> /api/users/list</h3>
            <p><a href="/api/users/list">List all users with details</a></p>
            <div class="vulnerability">
                <strong>Information Disclosure:</strong> Enumerate all users and their sensitive data
            </div>
        </div>
        
        <div class="endpoint">
            <h3><span class="method">GET</span> /api/admin/stats</h3>
            <p><a href="/api/admin/stats">Administrative statistics</a></p>
            <div class="vulnerability">
                <strong>Privilege Escalation:</strong> Access admin-only information
            </div>
        </div>

        <h2>Testing Techniques:</h2>
        <ol>
            <li><strong>ID Enumeration:</strong> Try sequential IDs (1, 2, 3, ...)</li>
            <li><strong>Privilege Escalation:</strong> Access admin users/documents</li>
            <li><strong>Cross-User Access:</strong> View other users' private data</li>
            <li><strong>Bulk Enumeration:</strong> Script to download all accessible resources</li>
            <li><strong>Parameter Manipulation:</strong> Change user_id in requests</li>
        </ol>

        <h2>Test Script:</h2>
        <div class="payload">
        # Enumerate all users<br>
        for i in range(1, 20):<br>
        &nbsp;&nbsp;&nbsp;&nbsp;requests.get(f'/api/users/{i}')<br><br>
        
        # Enumerate all documents<br>
        for i in range(1, 50):<br>
        &nbsp;&nbsp;&nbsp;&nbsp;requests.get(f'/api/documents/{i}')<br>
        </div>
    </body>
    </html>
    """)

@app.route('/api/users/<int:user_id>')
def get_user(user_id):
    """
    VULNERABILITY 1: Direct access to user data without authentication
    No authorization check - can access any user's profile
    """
    logger.warning(f"Accessing user data without authorization: user_id={user_id}")
    
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    
    if user:
        # VULNERABLE: Return sensitive user data without authorization
        profile_data = json.loads(user['profile_data']) if user['profile_data'] else {}
        
        return jsonify({
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'role': user['role'],
            'created_at': user['created_at'],
            'is_active': user['is_active'],
            'profile': profile_data,  # Contains sensitive data like SSN, salary
            'vulnerability': 'No authorization check allows access to any user data'
        })
    else:
        return jsonify({'error': 'User not found'}), 404

@app.route('/api/users/list')
def list_all_users():
    """
    VULNERABILITY 2: Information disclosure - list all users
    Exposes sensitive information about all users
    """
    logger.warning("Listing all users without authorization")
    
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users').fetchall()
    conn.close()
    
    # VULNERABLE: Return all users with sensitive data
    users_list = []
    for user in users:
        profile_data = json.loads(user['profile_data']) if user['profile_data'] else {}
        users_list.append({
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'role': user['role'],
            'profile': profile_data,
            'password_hash': user['password_hash']  # VERY DANGEROUS!
        })
    
    return jsonify({
        'users': users_list,
        'total_count': len(users_list),
        'vulnerability': 'All user data exposed without authentication'
    })

@app.route('/api/documents/<int:doc_id>')
def get_document(doc_id):
    """
    VULNERABILITY 3: Access private documents without authorization
    No ownership or access level checks
    """
    logger.warning(f"Accessing document without authorization: doc_id={doc_id}")
    
    conn = get_db_connection()
    document = conn.execute('''
        SELECT d.*, u.username as owner_username 
        FROM documents d 
        JOIN users u ON d.owner_id = u.id 
        WHERE d.id = ?
    ''', (doc_id,)).fetchone()
    conn.close()
    
    if document:
        # VULNERABLE: Return document regardless of privacy settings or ownership
        return jsonify({
            'id': document['id'],
            'title': document['title'],
            'content': document['content'],
            'owner_id': document['owner_id'],
            'owner_username': document['owner_username'],
            'is_private': document['is_private'],
            'access_level': document['access_level'],
            'category': document['category'],
            'created_at': document['created_at'],
            'vulnerability': 'No access control allows reading private documents'
        })
    else:
        return jsonify({'error': 'Document not found'}), 404

@app.route('/api/orders/<int:order_id>')
def get_order(order_id):
    """
    VULNERABILITY 4: Access other users' order information
    Order details including payment info exposed
    """
    logger.warning(f"Accessing order without authorization: order_id={order_id}")
    
    conn = get_db_connection()
    order = conn.execute('''
        SELECT o.*, u.username, u.email 
        FROM orders o 
        JOIN users u ON o.user_id = u.id 
        WHERE o.id = ?
    ''', (order_id,)).fetchone()
    conn.close()
    
    if order:
        # VULNERABLE: Return sensitive order and payment information
        return jsonify({
            'id': order['id'],
            'user_id': order['user_id'],
            'username': order['username'],
            'user_email': order['email'],
            'product_name': order['product_name'],
            'amount': order['amount'],
            'status': order['status'],
            'shipping_address': order['shipping_address'],
            'payment_method': order['payment_method'],
            'created_at': order['created_at'],
            'vulnerability': 'Order data accessible without ownership verification'
        })
    else:
        return jsonify({'error': 'Order not found'}), 404

@app.route('/api/messages/<int:message_id>')
def get_message(message_id):
    """
    VULNERABILITY 5: Read private messages between other users
    No sender/recipient authorization check
    """
    logger.warning(f"Accessing message without authorization: message_id={message_id}")
    
    conn = get_db_connection()
    message = conn.execute('''
        SELECT m.*, 
               s.username as sender_username, 
               r.username as recipient_username
        FROM messages m 
        JOIN users s ON m.sender_id = s.id 
        JOIN users r ON m.recipient_id = r.id 
        WHERE m.id = ?
    ''', (message_id,)).fetchone()
    conn.close()
    
    if message:
        # VULNERABLE: Return private message content
        return jsonify({
            'id': message['id'],
            'sender_id': message['sender_id'],
            'sender_username': message['sender_username'],
            'recipient_id': message['recipient_id'],
            'recipient_username': message['recipient_username'],
            'subject': message['subject'],
            'content': message['content'],
            'sent_at': message['sent_at'],
            'is_read': message['is_read'],
            'vulnerability': 'Private messages accessible without authorization'
        })
    else:
        return jsonify({'error': 'Message not found'}), 404

@app.route('/api/api-keys/<int:key_id>')
def get_api_key(key_id):
    """
    VULNERABILITY 6: Access other users' API keys
    Exposes sensitive API credentials
    """
    logger.warning(f"Accessing API key without authorization: key_id={key_id}")
    
    conn = get_db_connection()
    api_key = conn.execute('''
        SELECT k.*, u.username 
        FROM api_keys k 
        JOIN users u ON k.user_id = u.id 
        WHERE k.id = ?
    ''', (key_id,)).fetchone()
    conn.close()
    
    if api_key:
        # VULNERABLE: Return sensitive API key information
        return jsonify({
            'id': api_key['id'],
            'user_id': api_key['user_id'],
            'username': api_key['username'],
            'key_value': api_key['key_value'],  # VERY DANGEROUS!
            'key_name': api_key['key_name'],
            'permissions': api_key['permissions'],
            'created_at': api_key['created_at'],
            'expires_at': api_key['expires_at'],
            'is_active': api_key['is_active'],
            'vulnerability': 'API keys exposed without ownership verification'
        })
    else:
        return jsonify({'error': 'API key not found'}), 404

@app.route('/api/users/<int:user_id>', methods=['POST', 'PUT'])
def update_user(user_id):
    """
    VULNERABILITY 7: Update any user's profile without authorization
    Allows privilege escalation and account takeover
    """
    # Handle method override for HTML forms
    method = request.form.get('_method', request.method).upper()
    
    if method != 'PUT':
        return jsonify({'error': 'Method not allowed'}), 405
    
    logger.warning(f"Updating user without authorization: user_id={user_id}")
    
    # Get update data
    email = request.form.get('email')
    role = request.form.get('role')
    is_active = request.form.get('is_active')
    
    if not any([email, role, is_active]):
        return jsonify({'error': 'No update data provided'}), 400
    
    # VULNERABLE: No authorization check - can update any user
    conn = get_db_connection()
    
    # Check if user exists
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        conn.close()
        return jsonify({'error': 'User not found'}), 404
    
    # Build update query
    updates = []
    params = []
    
    if email:
        updates.append('email = ?')
        params.append(email)
    
    if role:
        updates.append('role = ?')
        params.append(role)
    
    if is_active is not None:
        updates.append('is_active = ?')
        params.append(1 if is_active.lower() == 'true' else 0)
    
    params.append(user_id)
    
    # VULNERABLE: Execute update without authorization
    conn.execute(f'UPDATE users SET {", ".join(updates)} WHERE id = ?', params)
    conn.commit()
    
    # Return updated user
    updated_user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    
    return jsonify({
        'id': updated_user['id'],
        'username': updated_user['username'],
        'email': updated_user['email'],
        'role': updated_user['role'],
        'is_active': updated_user['is_active'],
        'vulnerability': 'User update performed without authorization check'
    })

@app.route('/api/documents/<int:doc_id>', methods=['POST', 'DELETE'])
def delete_document(doc_id):
    """
    VULNERABILITY 8: Delete any document without authorization
    Allows data destruction by unauthorized users
    """
    # Handle method override for HTML forms
    method = request.form.get('_method', request.method).upper()
    
    if method != 'DELETE':
        return jsonify({'error': 'Method not allowed'}), 405
    
    logger.warning(f"Deleting document without authorization: doc_id={doc_id}")
    
    conn = get_db_connection()
    
    # Check if document exists
    document = conn.execute('SELECT * FROM documents WHERE id = ?', (doc_id,)).fetchone()
    if not document:
        conn.close()
        return jsonify({'error': 'Document not found'}), 404
    
    # VULNERABLE: Delete without checking ownership or permissions
    conn.execute('DELETE FROM documents WHERE id = ?', (doc_id,))
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'deleted_document_id': doc_id,
        'deleted_title': document['title'],
        'vulnerability': 'Document deleted without authorization check'
    })

@app.route('/api/admin/stats')
def admin_stats():
    """
    VULNERABILITY 9: Administrative endpoint without authentication
    Exposes sensitive system statistics
    """
    logger.warning("Accessing admin stats without authorization")
    
    conn = get_db_connection()
    
    # Get sensitive statistics
    user_count = conn.execute('SELECT COUNT(*) as count FROM users').fetchone()['count']
    admin_count = conn.execute('SELECT COUNT(*) as count FROM users WHERE role = "admin"').fetchone()['count']
    document_count = conn.execute('SELECT COUNT(*) as count FROM documents').fetchone()['count']
    private_doc_count = conn.execute('SELECT COUNT(*) as count FROM documents WHERE is_private = 1').fetchone()['count']
    order_total = conn.execute('SELECT SUM(amount) as total FROM orders').fetchone()['total']
    
    # Get user activity
    users_with_orders = conn.execute('''
        SELECT u.username, COUNT(o.id) as order_count, SUM(o.amount) as total_spent
        FROM users u 
        LEFT JOIN orders o ON u.id = o.user_id 
        GROUP BY u.id, u.username
    ''').fetchall()
    
    conn.close()
    
    # VULNERABLE: Return sensitive administrative data
    return jsonify({
        'system_stats': {
            'total_users': user_count,
            'admin_users': admin_count,
            'total_documents': document_count,
            'private_documents': private_doc_count,
            'total_revenue': order_total
        },
        'user_activity': [dict(user) for user in users_with_orders],
        'vulnerability': 'Administrative data exposed without authentication'
    })

@app.route('/api/bulk_download')
def bulk_download():
    """
    VULNERABILITY 10: Bulk data download without authorization
    Allows mass data exfiltration
    """
    resource_type = request.args.get('type', 'users')
    limit = int(request.args.get('limit', 100))
    
    logger.warning(f"Bulk downloading {resource_type} without authorization")
    
    conn = get_db_connection()
    
    if resource_type == 'users':
        data = conn.execute(f'SELECT * FROM users LIMIT {limit}').fetchall()
    elif resource_type == 'documents':
        data = conn.execute(f'SELECT * FROM documents LIMIT {limit}').fetchall()
    elif resource_type == 'orders':
        data = conn.execute(f'SELECT * FROM orders LIMIT {limit}').fetchall()
    elif resource_type == 'messages':
        data = conn.execute(f'SELECT * FROM messages LIMIT {limit}').fetchall()
    else:
        conn.close()
        return jsonify({'error': 'Invalid resource type'}), 400
    
    conn.close()
    
    # VULNERABLE: Return bulk sensitive data
    return jsonify({
        'resource_type': resource_type,
        'data': [dict(row) for row in data],
        'count': len(data),
        'vulnerability': f'Bulk {resource_type} data exposed without authorization'
    })

if __name__ == '__main__':
    print("🔑 API IDOR Demo Application")
    print("============================")
    print("Starting server on http://0.0.0.0:8004")
    print("")
    print("Test scenarios:")
    print("1. Access user profiles: /api/users/1, /api/users/2, etc.")
    print("2. Read private documents: /api/documents/2, /api/documents/5")
    print("3. View other users' orders: /api/orders/1, /api/orders/6")
    print("4. Read private messages: /api/messages/3, /api/messages/4")
    print("5. Access API keys: /api/api-keys/1, /api/api-keys/2")
    print("6. Admin stats: /api/admin/stats")
    print("7. Bulk download: /api/bulk_download?type=users")
    print("")
    print("⚠️  All endpoints are vulnerable to IDOR attacks!")
    
    app.run(debug=True, host='0.0.0.0', port=8004)