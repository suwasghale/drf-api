# 🛒 Django E-Commerce Platform (DRF-Based)

A **scalable, secure, and production-ready e-commerce backend** built using **Django REST Framework (DRF)** — following modern software engineering best practices and clean architecture.

---

## 🌟 Key Features

- 🔐 **Authentication & Authorization**
  - JWT-based authentication (using `djangorestframework-simplejwt`)
  - Email verification & password reset system
  - Role-based access (admin, staff, customer)

- 👤 **User Management**
  - Custom user model
  - Profile handling with signals
  - Secure account activation & deactivation

- 🏠 **Addresses**
  - User shipping & billing addresses
  - CRUD APIs with validation

- 🛍️ **Products, Discounts & Wishlist**
  - Product CRUD with categories, tags, and slugs
  - Smart discount engine with percentage and fixed discounts
  - User wishlist with easy management APIs

- 🛒 **Cart & Orders**
  - Persistent shopping cart (authenticated + guest)
  - Orders with items, taxes, discounts, and statuses
  - Payment gateway integration (Stripe / PayPal ready)

- 💳 **Payments**
  - Secure transaction records
  - Refund handling and webhook support

- 🚚 **Shipments**
  - Order shipment tracking
  - Integration hooks for external carriers (DHL, UPS, etc.)

- 🧾 **Invoices**
  - Auto-generated PDF invoices
  - Email delivery with Celery task scheduling

- 🔔 **Notifications**
  - System and user notifications (real-time ready)
  - Admin actions in Django admin panel

- 📊 **Analytics**
  - Daily, weekly, and monthly reports
  - Sales performance tracking
  - Data aggregation via background services

- 🎟️ **Discounts**
  - Coupon codes with validity periods
  - Percentage and flat discounts

- 🛠️ **Support**
  - Ticket-based user support system
  - Prioritization and response tracking

---

## 🧱 Project Architecture

## 🧱 Project Architecture

```text
apps/
│
├── users/              # Authentication, Profiles
├── addresses/          # User Addresses
├── cart/               # Shopping Cart
├── orders/             # Orders & Items
├── payments/           # Payment Handling
├── shipments/          # Shipments
├── invoices/           # Billing & Invoices
├── notifications/      # Alerts & Messages
├── analytics/          # Reports & Insights
├── discounts/          # Coupons & Rules
└── support/            # Customer Support

core/
├── settings/           # Environment-specific configs
├── middleware/         # Custom middlewares
├── utils/              # Helpers & common utilities
└── urls.py



This architecture follows a **modular monolith** pattern — each app can scale or be extracted into microservices later.

---

## ⚙️ Installation Guide

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/<yourusername>/<your-repo-name>.git
cd <your-repo-name>

2️⃣ Create & Activate Virtual Environment

python -m venv venv
source venv/bin/activate   # For macOS/Linux
venv\Scripts\activate      # For Windows

3️⃣ Install Dependencies

pip install -r requirements.txt

4️⃣ Apply Migrations

python manage.py makemigrations
python manage.py migrate

5️⃣ Create Superuser

python manage.py createsuperuser

6️⃣ Run Development Server

python manage.py runserver

🧪 API Testing (via Postman)

    Import the postman_collection.json file (if available).

    Base URL:

    http://127.0.0.1:8000/api/

    Example endpoints:

Endpoint	Method	Description
/api/users/register/	POST	Register new user
/api/users/login/	POST	Login (JWT)
/api/users/verify-email/	GET	Verify email
/api/users/resend-verification/	POST	Resend verification link
/api/products/	GET	List products
/api/cart/	GET / POST	Manage user cart
/api/orders/	POST	Create order
/api/payments/	POST	Process payment
/api/analytics/sales-report/	GET	Get monthly sales
/api/support/tickets/	GET	List support tickets
🛠️ Environment Variables (.env)

SECRET_KEY=your_django_secret_key
DEBUG=True
DATABASE_URL=postgres://user:password@localhost:5432/ecommerce
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_password
EMAIL_PORT=587
EMAIL_USE_TLS=True
STRIPE_SECRET_KEY=your_stripe_secret

Use django-environ or similar to manage environment configs securely.
🧰 Tech Stack
Category	Tools / Libraries
Framework	Django, Django REST Framework
Auth	JWT (SimpleJWT)
DB	PostgreSQL
Caching	Redis
Task Queue	Celery + Redis
API Docs	drf-spectacular
Testing	Pytest, DRF test client
Container	Docker (optional)
🔄 Background Jobs (Celery)

Used for:

    Sending email verification links

    Generating monthly sales reports

    Sending invoice PDFs

    Async notifications

Start Celery worker:

celery -A core worker -l info

🔒 Security Best Practices

    Enforce HTTPS in production.

    Use environment variables for secrets.

    Apply DRF throttling & permissions.

    Use select_related / prefetch_related to prevent N+1 queries.

    Enable SECURE_* settings in production.

    Regular database backups.

🧠 Future Improvements

    Integrate full-text search with ElasticSearch

    WebSockets / Channels for real-time notifications

    Multi-vendor support

    GraphQL API layer

    Payment refunds automation

📜 License

MIT License © 2025 — Developed by Suwas Ghale
💬 Contact

If you’d like to collaborate or suggest improvements:
📧 suwasghale2281@gmail.com

