# Auspify Market

Full-stack e-commerce platform for product browsing and management.

## Features

- Product catalog with search and category filters
- Product detail pages
- Shopping cart
- User registration and login
- Customer profile and password management
- Order placement and order history
- Admin product and order management
- Stock validation during cart updates and checkout
- REST APIs for products and cart

## Tech Stack

- Backend: Python, Flask, SQLAlchemy, Flask-Login
- Frontend: HTML, Tailwind CSS, JavaScript
- Database: SQLite

## Setup

```bash
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000

For local development, set `FLASK_DEBUG=true` to enable Flask debug mode. Set
`SECRET_KEY` and `DATABASE_URL` in the environment when deploying or using a
non-default database.

## Demo Accounts (local development only)

| Role  | Username | Password  |
|-------|----------|-----------|
| User  | demo     | demo123   |
| Admin | admin    | admin123  |

Admin panels: `/admin/products` and `/admin/orders`

Checkout is in demo mode and does not process payments.

## Tests

Run the end-to-end shopping workflow tests with:

```bash
python -m unittest discover -s tests
```

## API Endpoints

- GET    /api/products
- GET    /api/products/<id>
- POST   /api/products          (admin)
- PUT    /api/products/<id>     (admin)
- DELETE /api/products/<id>     (admin)
- GET    /api/cart              (authenticated)
