# Hackathon Backend - 4 Layer Architecture

FastAPI backend with SQLAlchemy and Alembic for the marketplace application.

## Architecture

This backend follows a clean 4-layer architecture:

1. **Layer 1: Presentation (API Routes)** - `app/api/routes/`
   - FastAPI route handlers
   - Request/response validation
   - HTTP status codes

2. **Layer 2: Business Logic (Services)** - `app/services/`
   - Business rules and validation
   - Data transformation
   - Authorization logic

3. **Layer 3: Data Access (Repositories)** - `app/repositories/`
   - Database queries
   - CRUD operations
   - Complex joins

4. **Layer 4: Database (Models)** - `app/models/`
   - SQLAlchemy ORM models
   - Database schema definitions

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and update with your database credentials:

```bash
cp .env.example .env
```

### 3. Run Database Migrations

```bash
alembic upgrade head
```

### 4. Start the Server

```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at:
- API: http://localhost:8000/api
- Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Authentication (Dummy)
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get JWT token
- `POST /api/auth/logout` - Logout (dummy)
- `GET /api/auth/me` - Get current user

### Items
- `GET /api/items` - List items with filters
- `GET /api/items/{id}` - Get item details
- `POST /api/items` - Create item listing
- `PUT /api/items/{id}` - Update item
- `DELETE /api/items/{id}` - Delete item
- `GET /api/items/{id}/recommended` - Get recommended items

### Favorites
- `GET /api/users/{userId}/favorites` - Get user favorites
- `POST /api/favorites` - Add favorite
- `DELETE /api/favorites` - Remove favorite

### Users
- `GET /api/users/{userId}/profile` - Get user profile
- `PUT /api/users/{userId}/profile` - Update profile

### Purchases
- `POST /api/purchases` - Create purchase
- `GET /api/users/{userId}/purchases` - Get purchase history
- `GET /api/purchases/{id}` - Get purchase details

## Development

### Database Migrations

Create new migration:
```bash
alembic revision --autogenerate -m "Description"
```

Apply migrations:
```bash
alembic upgrade head
```

Rollback migration:
```bash
alembic downgrade -1
```

### Testing with Frontend

1. Start backend: `uvicorn app.main:app --reload`
2. Start frontend: `cd ../../../hackathon-frontend && npm run dev`
3. Frontend will connect to `http://localhost:8000/api`

## Project Structure

```
hackathon-backend/
├── alembic/              # Database migrations
├── app/
│   ├── api/             # Layer 1: API Routes & Schemas
│   ├── services/        # Layer 2: Business Logic
│   ├── repositories/    # Layer 3: Data Access
│   ├── models/          # Layer 4: Database Models
│   ├── config.py        # Configuration
│   ├── dependencies.py  # Dependency Injection
│   └── main.py         # Application entry point
└── requirements.txt
```
