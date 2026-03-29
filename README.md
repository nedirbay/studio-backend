# Doganlar Studio Backend (Django + DRF)

Backend for customers, appointments, orders, equipment, expenses, gallery, and basic auth with JWT. PostgreSQL is used as the default database.

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

## Models (summary)

- Customer, Appointment, User, Role, GalleryItem, Equipment, EquipmentAssignment, Order, OrderDay, OrderStaff, Expense.

## Testing

- Run all tests:
  ```bash
  python manage.py test
  ```
- Current suite covers auth (login/refresh/me/profile), CRUD flows for customers/appointments/orders/equipment/expenses, financial stats, and service-layer token change/stats.

## Notes / Deploy

- Set `SECRET_KEY`, `DEBUG=False`, and tighten `ALLOWED_HOSTS` for production.
- Token lifetimes: access 30 minutes, refresh 7 days (configurable in code).
