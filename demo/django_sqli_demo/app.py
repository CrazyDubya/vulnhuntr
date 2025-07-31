"""
Django SQL Injection (SQLI) Demo Application

This application contains intentional SQL injection vulnerabilities for demonstration purposes.
DO NOT USE IN PRODUCTION - FOR EDUCATIONAL/TESTING PURPOSES ONLY.

Vulnerabilities included:
1. Raw SQL queries with string concatenation
2. ORM bypasses with raw() method
3. Custom SQL with user-controlled parameters
4. UNION-based SQL injection
5. Blind SQL injection vulnerabilities
6. Time-based SQL injection
"""

import os
import sys
import django
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.urls import path
from django.core.wsgi import get_wsgi_application
from django.db import models, connection
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json
import time
import logging
import sqlite3
from datetime import datetime

# Configure Django settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY='demo_secret_key_unsafe_for_testing_only',
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',  # In-memory database for demo
            }
        },
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'django.contrib.auth',
            '__main__',  # This module
        ],
        USE_TZ=True,
        ROOT_URLCONF='__main__',  # URL patterns defined in this file
    )

django.setup()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Django Models
from django.contrib.auth.models import User

class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=100)
    stock = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        app_label = '__main__'

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    order_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, default='pending')
    
    class Meta:
        app_label = '__main__'

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20)
    address = models.TextField()
    credit_card = models.CharField(max_length=20)  # Don't store real credit cards!
    
    class Meta:
        app_label = '__main__'

# Create tables and populate with sample data
def setup_demo_data():
    """Create tables and populate with demo data"""
    # Create tables
    from django.core.management.color import no_style
    from django.db import connection
    
    style = no_style()
    sql = connection.ops.sql_table_creation_suffix()
    
    # Get SQL for model creation
    from django.core.management.sql import sql_create_index
    from django.db import models
    
    # Create tables manually since we're not using migrations
    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(Product)
        schema_editor.create_model(Order)
        schema_editor.create_model(UserProfile)
    
    # Create sample users
    admin_user = User.objects.create_user('admin', 'admin@demo.com', 'admin123')
    admin_user.is_staff = True
    admin_user.is_superuser = True
    admin_user.save()
    
    user1 = User.objects.create_user('john_doe', 'john@demo.com', 'password123')
    user2 = User.objects.create_user('jane_smith', 'jane@demo.com', 'password456')
    
    # Create user profiles
    UserProfile.objects.create(
        user=admin_user,
        phone='+1-555-0001',
        address='123 Admin St, Admin City',
        credit_card='4111-1111-1111-1111'
    )
    
    UserProfile.objects.create(
        user=user1,
        phone='+1-555-0123',
        address='456 User Ave, User Town',
        credit_card='4222-2222-2222-2222'
    )
    
    UserProfile.objects.create(
        user=user2,
        phone='+1-555-0456',
        address='789 Customer Blvd, Customer City',
        credit_card='4333-3333-3333-3333'
    )
    
    # Create sample products
    products_data = [
        {'name': 'Laptop Pro', 'description': 'High-performance laptop', 'price': 1299.99, 'category': 'electronics', 'stock': 10},
        {'name': 'Smartphone X', 'description': 'Latest smartphone model', 'price': 899.99, 'category': 'electronics', 'stock': 25},
        {'name': 'Coffee Maker', 'description': 'Automatic coffee machine', 'price': 199.99, 'category': 'home', 'stock': 15},
        {'name': 'Book Set', 'description': 'Programming books collection', 'price': 89.99, 'category': 'books', 'stock': 50},
        {'name': 'Wireless Headphones', 'description': 'Noise-canceling headphones', 'price': 299.99, 'category': 'electronics', 'stock': 30},
    ]
    
    for product_data in products_data:
        Product.objects.create(**product_data)
    
    # Create sample orders
    products = Product.objects.all()
    Order.objects.create(user=user1, product=products[0], quantity=1, total_price=1299.99, status='completed')
    Order.objects.create(user=user1, product=products[2], quantity=2, total_price=399.98, status='pending')
    Order.objects.create(user=user2, product=products[1], quantity=1, total_price=899.99, status='shipped')

# Views with SQL Injection vulnerabilities

def index(request):
    """Main page with navigation to vulnerable endpoints"""
    return HttpResponse("""
    <html>
    <head><title>Django SQL Injection Demo</title></head>
    <body>
        <h1>Django SQL Injection Demo</h1>
        <p>This application demonstrates various SQL injection vulnerabilities in Django applications.</p>
        
        <h2>Vulnerable Endpoints:</h2>
        <ul>
            <li><a href="/search?q=laptop">Product Search (String Concatenation)</a></li>
            <li><a href="/user/1">User Details (Raw SQL)</a></li>
            <li><a href="/orders?user_id=1">Order History (Raw ORM)</a></li>
            <li><a href="/filter?category=electronics&min_price=100">Product Filter (Complex Query)</a></li>
            <li><a href="/reports?start_date=2024-01-01&end_date=2024-12-31">Sales Reports (Date Range)</a></li>
            <li><a href="/api/products?sort=name&order=asc">API Products (Sort Parameter)</a></li>
            <li><a href="/admin/users?role=admin">Admin Panel (Authorization Bypass)</a></li>
        </ul>
        
        <h2>Test Payloads:</h2>
        <h3>Basic Injection:</h3>
        <ul>
            <li><code>' OR '1'='1</code></li>
            <li><code>' UNION SELECT 1,2,3,4,5--</code></li>
            <li><code>' AND (SELECT COUNT(*) FROM auth_user) > 0--</code></li>
        </ul>
        
        <h3>Time-based Blind:</h3>
        <ul>
            <li><code>' AND (SELECT CASE WHEN (1=1) THEN sqlite3_sleep(5000) ELSE 0 END)--</code></li>
            <li><code>' OR (SELECT sqlite_version())='3.x.x</code></li>
        </ul>
        
        <h3>UNION-based:</h3>
        <ul>
            <li><code>' UNION SELECT username,password,email,1,2 FROM auth_user--</code></li>
            <li><code>' UNION SELECT credit_card,phone,address,1,2 FROM __main___userprofile--</code></li>
        </ul>
        
        <h3>Boolean-based Blind:</h3>
        <ul>
            <li><code>' AND (SELECT LENGTH(password) FROM auth_user WHERE username='admin') > 10--</code></li>
            <li><code>' AND EXISTS(SELECT 1 FROM auth_user WHERE username='admin' AND is_superuser=1)--</code></li>
        </ul>
    </body>
    </html>
    """)

def vulnerable_search(request):
    """
    VULNERABILITY 1: String concatenation in raw SQL query
    User input directly concatenated into SQL query
    """
    search_query = request.GET.get('q', '')
    
    if not search_query:
        return JsonResponse({'error': 'No search query provided'})
    
    # VULNERABLE: Direct string concatenation
    sql = f"SELECT * FROM __main___product WHERE name LIKE '%{search_query}%' OR description LIKE '%{search_query}%'"
    
    logger.warning(f"Executing vulnerable search query: {sql}")
    
    try:
        with connection.cursor() as cursor:
            # VULNERABLE: Raw SQL execution without parameterization
            cursor.execute(sql)
            columns = [col[0] for col in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        return JsonResponse({
            'query': search_query,
            'sql_executed': sql,
            'results': results,
            'count': len(results)
        })
    except Exception as e:
        return JsonResponse({
            'query': search_query,
            'sql_executed': sql,
            'error': str(e)
        })

def vulnerable_user_details(request, user_id):
    """
    VULNERABILITY 2: Raw SQL with user-controlled parameter
    User ID parameter directly inserted into SQL query
    """
    # VULNERABLE: User input directly used in SQL
    sql = f"""
    SELECT u.id, u.username, u.email, u.is_staff, u.is_superuser, u.date_joined,
           p.phone, p.address, p.credit_card
    FROM auth_user u
    LEFT JOIN __main___userprofile p ON u.id = p.user_id
    WHERE u.id = {user_id}
    """
    
    logger.warning(f"Executing user details query: {sql}")
    
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql)
            columns = [col[0] for col in cursor.description]
            result = cursor.fetchone()
            
            if result:
                user_data = dict(zip(columns, result))
                return JsonResponse({
                    'user_id': user_id,
                    'sql_executed': sql,
                    'user_data': user_data
                })
            else:
                return JsonResponse({
                    'user_id': user_id,
                    'sql_executed': sql,
                    'error': 'User not found'
                })
    except Exception as e:
        return JsonResponse({
            'user_id': user_id,
            'sql_executed': sql,
            'error': str(e)
        })

# URL patterns
urlpatterns = [
    path('', index, name='index'),
    path('search', vulnerable_search, name='search'),
    path('user/<str:user_id>', vulnerable_user_details, name='user_details'),
]

if __name__ == '__main__':
    import sys
    
    # Set up demo data
    setup_demo_data()
    
    # Run development server
    if len(sys.argv) > 1 and sys.argv[1] == 'runserver':
        from django.core.management import execute_from_command_line
        execute_from_command_line(['manage.py', 'runserver', '0.0.0.0:8001'])
    else:
        print("🗃️  Django SQL Injection Demo")
        print("Usage: python app.py runserver")
        print("Then visit: http://localhost:8001")
        print("")
        print("Test payloads:")
        print("- Search: ' UNION SELECT username,password,email,1,2 FROM auth_user--")
        print("- User ID: 1 OR 1=1")
        print("- Login: admin' OR '1'='1'-- ")