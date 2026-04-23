# Doganlar Studio Backend (Django + DRF)

Backend for customers, appointments, orders, equipment, expenses, gallery, blog, commerce, and auth with JWT. PostgreSQL is used as the default database.

## Stack

- Python / Django 6 + Django REST Framework
- PostgreSQL
- JWT (HS256) custom auth
- Swagger UI via drf-spectacular

## Quick start

1. Create/ensure PostgreSQL DB:
   - NAME: `appname`
   - USER: `yourpostgresusername`
   - PASSWORD: `yourpostgrespassword`
   - HOST: `yourpostgresip`
   - PORT: `yourpostgresport`
2. Install deps (already in `venv` here; otherwise `pip install -r requirements.txt`).
3. Apply migrations:
   ```bash
   python manage.py migrate
   ```
4. Run server:
   ```bash
   python manage.py runserver
   ```

## Auth

- Legacy tokens stored on `User.token` are used only for the login step.
- Login: `POST /api/auth/login` with JSON `{ "token": "<legacy_token>" }`
  - Returns: `jwt` (access, 30 minutes), `refresh` (7 days), plus user info.
- Google Sign-In: `POST /api/auth/google` with JSON `{ "credential": "<google_id_token>" }`
  - Requires env: `GOOGLE_CLIENT_ID`
- Use the access token in requests:
  - Header: `Authorization: Bearer <jwt>`
- Refresh: `POST /api/auth/refresh` with `{ "refresh": "<refresh_token>" }`
  - Returns new `jwt` and `refresh`.
- Access tokens are required for all protected endpoints (everything except login/refresh/schema/docs).

## Swagger & Schema

- Swagger UI: `/api/docs`
- OpenAPI JSON: `/api/schema`

## API endpoints (main ones)

- Auth: `POST /api/auth/login`, `GET /api/auth/me`, `PUT /api/auth/profile`, `POST /api/auth/refresh`
- Customers: `GET/POST /api/customers`, `GET/PUT/DELETE /api/customers/{id}`
- Appointments: `GET/POST /api/appointments`, `GET /api/appointments/date/{yyyy-mm-dd}`, `PUT /api/appointments/{id}`
- Orders: `GET/POST /api/orders`, `GET/PUT/DELETE /api/orders/{id}`, `GET /api/orders/staff/{userId}`
- Equipment: `GET/POST /api/equipments`, `GET /api/equipments/assigned`
- Expenses & Stats: `GET/POST /api/expenses`, `GET /api/stats/financial`
- Blog: `GET/POST /api/blogs`, `GET/PUT/DELETE /api/blogs/{id}` (supports multiple images/videos per post)
- Commerce:
  - Categories: `GET/POST /api/categories`
  - Products: `GET/POST /api/products`, `GET/PUT/DELETE /api/products/{id}` (supports multiple images/videos per product)

## Models (summary)

- Auth: Role, User (moved to `auth` app; JWT auth class lives there)
- Core: Customer, Appointment, GalleryItem, Equipment, EquipmentAssignment, Order, OrderDay, OrderStaff, Expense
- Blog: BlogPost, BlogMedia (many images/videos per post)
- Commerce: Category, Product, ProductMedia (many images/videos per product)

## Testing

- Run all tests:
  ```bash
  python manage.py test
  ```
- Current suite covers:
  - Auth (login/refresh/me/profile, token change)
  - CRUD flows for customers, appointments, orders (incl. staff filter), equipment, expenses, financial stats
  - Blog endpoints (list/create/update/delete with multiple media)
  - Commerce endpoints (categories, products with multiple media)

## Notes / Deploy

- Set `SECRET_KEY`, `DEBUG=False`, and tighten `ALLOWED_HOSTS` for production.
- Token lifetimes: access 30 minutes, refresh 7 days (configurable in code).
