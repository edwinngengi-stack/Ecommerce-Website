# Auspify Market

Full-stack e-commerce platform for product browsing and management.

Live demo: https://auspify-market.onrender.com

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
- Database: SQLite for local development; PostgreSQL for deployment
- Production server: Gunicorn

## Setup

```bash
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000

For local development, set `FLASK_DEBUG=true` to enable Flask debug mode.
Without `DATABASE_URL`, the app uses a local SQLite database.

## Deploy to Render

1. Create a PostgreSQL database in the Render dashboard.
2. Create a **Web Service** for this GitHub repository and select the `main`
   branch. Leave the root directory blank.
3. Use these commands:

   - Build: `pip install -r requirements.txt`
   - Start: `gunicorn --workers 1 --bind 0.0.0.0:$PORT app:app`

   The included `Procfile` provides the same start command.
4. In the web service's environment settings, add:

   - `DATABASE_URL`: the PostgreSQL database's **Internal Database URL**
   - `SECRET_KEY`: a newly generated, private random value
   - `ADMIN_USERNAME`: the username for the first administrator
   - `ADMIN_EMAIL`: the administrator's email address
   - `ADMIN_PASSWORD`: a private password of at least 12 characters

   Set all three `ADMIN_...` variables together. The app creates this
   administrator when it first initializes the database; it does not reset
   that account's password on later restarts. Keep these values private and
   never commit them to the repository.
5. Deploy the service. Render will provide its public URL and can deploy future
   pushes to `main` automatically.

The app seeds sample products in an empty database. It no longer creates public
demo or default administrator accounts. If you reuse an older local database,
the users already in that database remain; change or remove any old demo
credentials before exposing that database publicly.

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
