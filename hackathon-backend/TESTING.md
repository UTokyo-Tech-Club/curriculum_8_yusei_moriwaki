# Testing the Backend

## Prerequisites

1. **Database Setup**: Ensure your MySQL database is running and accessible
2. **Environment Variables**: Update `.env` with your database credentials
3. **Dependencies**: Install all required packages

## Setup Steps

### 1. Install Dependencies

```bash
cd hackathon-backend
pip install -r requirements.txt
```

### 2. Configure Environment

Update `.env` file with your database credentials:

```bash
MYSQL_HOST=your_cloud_sql_host
MYSQL_USER=your_user
MYSQL_PWD=your_password
MYSQL_DATABASE=hackathon
```

### 3. Run Database Migrations

```bash
# Apply migrations to add new tables and columns
alembic upgrade head
```

This will:
- Add `bio` and `location` columns to `users` table
- Create new `purchases` table

### 4. Start the Backend Server

```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at:
- Base URL: http://localhost:8000
- API endpoints: http://localhost:8000/api
- Interactive docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing with FastAPI Docs

1. Open http://localhost:8000/docs in your browser
2. Test endpoints in this order:

### Authentication Flow

**Register a new user:**
```json
POST /api/auth/register
{
  "email": "test@example.com",
  "name": "Test User"
}
```

**Login (get JWT token):**
```json
POST /api/auth/login
{
  "email": "test@example.com"
}
```

Copy the `token` from the response.

**Authorize in Swagger UI:**
1. Click the "Authorize" button (lock icon) at the top
2. Enter: `Bearer YOUR_TOKEN_HERE`
3. Click "Authorize"

### Items Flow

**Get all items:**
```
GET /api/items?limit=10
```

**Get single item:**
```
GET /api/items/1
```

**Get recommended items:**
```
GET /api/items/1/recommended
```

**Create item listing (requires auth):**
```json
POST /api/items
{
  "item_id": 123456,
  "product_id": "PROD123"
}
```

### Favorites Flow

**Get user favorites:**
```
GET /api/favorites/users/{user_id}
```

**Add favorite (requires auth):**
```json
POST /api/favorites
{
  "item_id": 123456
}
```

**Remove favorite (requires auth):**
```json
DELETE /api/favorites
{
  "item_id": 123456
}
```

### User Profile Flow

**Get user profile:**
```
GET /api/users/{user_id}/profile
```

**Update profile (requires auth):**
```json
PUT /api/users/{user_id}/profile
{
  "name": "Updated Name",
  "bio": "My bio",
  "location": "Tokyo"
}
```

**Get user's items:**
```
GET /api/users/{user_id}/items
```

### Purchase Flow

**Create purchase (requires auth):**
```json
POST /api/purchases
{
  "item_id": 1,
  "payment_method": "credit",
  "shipping_address": {
    "postal_code": "100-0001",
    "prefecture": "Tokyo",
    "city": "Chiyoda",
    "address": "1-1-1",
    "building": "Building A",
    "name": "John Doe",
    "phone": "090-1234-5678"
  }
}
```

**Get purchase history (requires auth):**
```
GET /api/purchases/users/{user_id}
```

## Testing with Frontend

### 1. Update Frontend API Base URL

In your frontend code, update the API base URL to:
```
http://localhost:8000/api
```

### 2. Start Frontend

```bash
cd ../hackathon-frontend
npm run dev
```

Frontend will run on http://localhost:3000

### 3. Test User Flow

1. **Browse Items**: Should load items from the database
2. **Register**: Create a new account
3. **Login**: Login with the registered email
4. **View Item Details**: Click on any item
5. **Add to Favorites**: Click the favorite button
6. **Purchase**: Complete a purchase
7. **View Purchase History**: Check your purchases
8. **Edit Profile**: Update your profile information

## Common Issues & Solutions

### Issue: Connection refused

**Solution**: Check that MySQL is running and credentials in `.env` are correct

### Issue: Table doesn't exist

**Solution**: Run migrations: `alembic upgrade head`

### Issue: CORS error in frontend

**Solution**: Verify CORS_ORIGINS in `app/config.py` includes your frontend URL

### Issue: 401 Unauthorized

**Solution**: Make sure you're sending the JWT token in the Authorization header:
```
Authorization: Bearer YOUR_TOKEN
```

### Issue: No items returned

**Solution**: Verify that:
1. `item_listings` table has data
2. `mercari_items` table has corresponding data
3. Items are joined correctly (check logs)

## Debugging

### Enable SQL Query Logging

In `app/models/base.py`, set `echo=True`:
```python
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,  # This will log all SQL queries
    ...
)
```

### Check Logs

The terminal where you run `uvicorn` will show:
- HTTP requests
- SQL queries (if echo=True)
- Error tracebacks

### Test Database Connection

```python
# test_connection.py
import asyncio
from app.models.base import async_engine

async def test_connection():
    async with async_engine.begin() as conn:
        result = await conn.execute(text("SELECT 1"))
        print("Connection successful:", result.scalar())

if __name__ == "__main__":
    asyncio.run(test_connection())
```

## API Response Examples

### Successful Authentication Response
```json
{
  "user": {
    "id": "1234567890",
    "email": "test@example.com",
    "name": "Test User",
    "avatar": null,
    "created_at": "2025-12-16T10:00:00"
  },
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### Successful Item Response
```json
{
  "id": "1",
  "item_id": 123456,
  "title": "Sample Item",
  "description": "Item description",
  "price": 5000.0,
  "images": [],
  "category": "fashion",
  "status": "available",
  "seller_id": "45",
  "seller_name": "Samuel Boyle",
  "views_count": 10,
  "likes_count": 2,
  "created_at": "2025-12-16T10:00:00"
}
```

## Next Steps

Once basic testing is complete:

1. **Add Image Upload**: Implement image storage (S3, Cloudinary)
2. **Add Real Authentication**: Implement password hashing and verification
3. **Add Pagination**: Implement cursor-based pagination for items
4. **Add Search**: Implement full-text search
5. **Add Caching**: Implement Redis caching for frequently accessed data
6. **Add Rate Limiting**: Protect endpoints from abuse
7. **Add Logging**: Implement structured logging
8. **Add Monitoring**: Set up application monitoring (e.g., Sentry)




