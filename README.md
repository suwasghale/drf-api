🛒 Ecommerce Platform — Django REST API

A scalable, secure, and modular E-commerce backend built with Django REST Framework.
Designed for enterprise-level extensibility, following clean architecture and best practices used in top companies.

🚀 Features
🔐 Authentication & Users

JWT-based authentication (access + refresh tokens)

Email verification with expiring tokens

Password reset & change (with history enforcement)

Account lockout after multiple failed logins

Role-based access control (RBAC)

Two-Factor Authentication (2FA) ready structure

Full audit logging for user actions

🧾 Orders, Payments, Shipments

Complete order lifecycle: cart → checkout → shipment

Payment integration-ready (Stripe / PayPal adapters)

Shipment tracking support with status updates

Invoice generation and PDF-ready models

🧮 Analytics & Reports

Sales analytics & performance tracking

Automated report generation service

Celery-ready for scheduling and async reporting

💬 Notifications & Support

Real-time (and email) notifications

Customer support ticketing system

Admin dashboard customization

🏷️ Discounts & Coupons

Configurable percentage and fixed discounts

Coupon usage tracking and expiration management

📦 Product & Inventory Management

Category hierarchy and slug-based product URLs

Inventory count, stock management, SKU support

🧱 Project Structure
apps/
├── analytics/
│   ├── api/
│   ├── models.py
│   ├── services/
│   ├── views.py
│   ├── admin.py
│   └── apps.py
├── cart/
├── discounts/
├── invoices/
├── notifications/
├── orders/
├── payments/
├── product/
├── shipments/
├── support/
├── users/
└── wishlist/
