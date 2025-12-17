# Quick Start Guide

## 🚀 Start Backend in 5 Minutes

### Step 1: Install Dependencies (1 min)

```bash
cd curriculum_8_yusei_moriwaki/hackathon-backend
pip install -r requirements.txt
```

### Step 2: Configure Database (1 min)

Create `.env` file (or update existing one):

```bash
MYSQL_HOST=your_cloud_sql_host
MYSQL_USER=your_username
MYSQL_PWD=your_password
MYSQL_DATABASE=hackathon
```

### Step 3: Run Migrations (1 min)

```bash
alembic upgrade head
```

This adds:
- `bio` and `location` columns to `users` table
- Creates new `purchases` table

### Step 4: Start Server (1 min)

```bash
uvicorn app.main:app --reload --port 8000
```

### Step 5: Test It Works (1 min)

Open in browser: http://localhost:8000/docs

Try the health check:
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "ok", "service": "hackathon-backend"}
```

## 🎯 Test with Frontend

### Update Frontend API URL

In your frontend, point to:
```
http://localhost:8000/api
```

### Start Frontend

```bash
cd ../../../hackathon-frontend
npm run dev
```

Frontend runs on http://localhost:3000

## 📍 API Endpoints

All endpoints are under `/api`:

**Auth (no password required):**
- `POST /api/auth/register` - Register with email + name
- `POST /api/auth/login` - Login with email only
- `GET /api/auth/me` - Get current user

**Items:**
- `GET /api/items` - Browse items (with filters)
- `GET /api/items/{id}` - Item details
- `POST /api/items` - Create listing 🔒

**Favorites:**
- `GET /api/favorites/users/{userId}` - Get favorites
- `POST /api/favorites` - Add favorite 🔒
- `DELETE /api/favorites` - Remove favorite 🔒

**Users:**
- `GET /api/users/{userId}/profile` - User profile
- `PUT /api/users/{userId}/profile` - Update profile 🔒
- `GET /api/users/{userId}/items` - User's items

**Purchases:**
- `POST /api/purchases` - Buy item 🔒
- `GET /api/purchases/users/{userId}` - Purchase history 🔒

🔒 = Requires JWT token in header: `Authorization: Bearer <token>`

## 🐛 Common Issues

**"Connection refused"**
→ Check database credentials in `.env`

**"Table doesn't exist"**
→ Run: `alembic upgrade head`

**"CORS error"**
→ Check CORS_ORIGINS in `app/config.py`

**"401 Unauthorized"**
→ Get token from `/api/auth/login` first
→ Add header: `Authorization: Bearer YOUR_TOKEN`

## 📚 More Info

- Full testing guide: [TESTING.md](TESTING.md)
- Implementation details: [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)
- Architecture: 4-layer (Routes → Services → Repositories → Models)
- Interactive docs: http://localhost:8000/docs

## ✅ Health Check

```bash
# Should return OK
curl http://localhost:8000/health

# Should return list of items
curl http://localhost:8000/api/items?limit=5

# Should return API info
curl http://localhost:8000/
```

---

**That's it! Your backend is running! 🎉**



