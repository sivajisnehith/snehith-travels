# Snehith Travels 🚌

> **Production-grade Bus Booking Backend & Demo MVP**
> Designed as the deterministic source-of-truth travel booking service for **Saarthi AI** (an upcoming AI voice travel agent).

---

## 🌟 Tech Stack

- **Frontend**: Next.js 16 (App Router), TypeScript, Tailwind CSS
- **Backend**: Python 3.12, FastAPI, SQLAlchemy 2.0, Pydantic v2
- **Database**: PostgreSQL (Docker Compose) with automatic SQLite fallback for lightweight local dev/testing
- **Authentication**: JWT (JSON Web Tokens) with bcrypt password hashing
- **Security & Concurrency**: Transactional 10-minute temporary seat holding to prevent double booking
- **Digital Ticketing**: Dynamic QR code generation with secure booking references

---

## 🚀 Quick Start Guide

### 1. Database (PostgreSQL via Docker Compose)

Start the persistent PostgreSQL service:

```bash
# In the project root
docker compose up -d
```

> **Note**: The backend is configured to connect to PostgreSQL at `localhost:5432` by default. If PostgreSQL is not running or during local tests, the engine gracefully falls back to local SQLite (`snehith_travels.db`), so you can develop immediately without getting blocked!

### 2. Backend (FastAPI on Port 8000)

```bash
cd backend

# Activate virtual environment
.\venv\Scripts\activate   # On Windows (PowerShell)
# or: source venv/bin/activate (on Unix)

# Install dependencies (already pre-installed in venv)
pip install -r requirements.txt

# Run database migrations / seed demo data
python -m app.db.seed

# Start FastAPI server
uvicorn app.main:app --reload --port 8000
```

FastAPI will be available at:
- **API URL**: http://localhost:8000
- **Interactive Swagger Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 3. Frontend (Next.js on Port 3000)

```bash
cd frontend

# Run development server
npm run dev
```

Next.js will be running at:
- **Web App**: http://localhost:3000

---

## 🔑 Demo Accounts

| Role | Email | Password |
|---|---|---|
| **Admin** | `admin@snehithtravels.com` | `AdminPassword123!` |
| **Customer** | `demo@snehithtravels.com` | `DemoPassword123!` |

*(Both accounts are pre-seeded with 1-click auto-fill buttons on the `/login` page).*

---

## 🧪 Running Backend Tests

The test suite validates health checks, JWT authentication, bus searches with filtering and sorting, seat availability, deterministic seat recommendation scoring, 10-minute seat holds, double-booking prevention, mock payments, and digital ticket QR code generation.

```bash
cd backend
python -m pytest -v
```

All 15 tests pass with a 100% success rate:
- `tests/test_health.py`
- `tests/test_auth.py`
- `tests/test_buses.py`
- `tests/test_recommendation.py`
- `tests/test_seat_hold.py`
- `tests/test_booking.py`
- `tests/test_payment.py`
- `tests/test_double_booking.py`

---

## 🗺️ Seeded Routes & Demo Data

The database includes realistic schedules across major South Indian routes:
1. **Hyderabad ⇄ Vijayawada**
2. **Hyderabad ⇄ Bangalore**
3. **Bangalore ⇄ Chennai**
4. **Hyderabad ⇄ Chennai**

Bus types include:
- **AC Sleeper** (Upper / Lower deck 2+1 layout, Window/Aisle berths)
- **Non-AC Sleeper**
- **AC Seater** (2+2 layout, 32 seats)
- **Semi-Sleeper** (2+2 layout, 28 seats)

Every seat includes metadata: `seat_number`, `row`, `column`, `seat_type`, `window`, `aisle`, `upper_lower`, `front_rear`, `price`, and dynamic status (`available`, `held`, `booked`).

---

## 🔌 API Endpoints Reference

### 🔐 Authentication
- `POST /api/auth/register` — Register a customer account
- `POST /api/auth/login` — Log in and receive JWT token
- `GET /api/auth/me` — Get profile for authenticated user

### 🚌 Buses & Routes
- `GET /api/buses/routes` — Discover all active routes
- `GET /api/buses/search` — Search buses by origin, destination, journey date, passengers, price, AC, sleeper/seater, departure time, and sorting
- `GET /api/buses/{bus_id}` — Get single bus information
- `GET /api/buses/{bus_id}/seats?journey_date=YYYY-MM-DD` — Dynamic seat availability (available/held/booked)
- `POST /api/buses/{bus_id}/recommend-seats` — Deterministic seat scoring and ranking for travelers or AI agent

### 🪑 Seat Holding
- `POST /api/seats/hold` — Temporarily hold seats for 10 minutes (prevents race conditions)
- `DELETE /api/seats/hold` — Release held seats

### 📋 Bookings
- `POST /api/bookings` — Create a booking with passenger details (`PENDING_PAYMENT` state)
- `GET /api/bookings` — List authenticated user's bookings
- `GET /api/bookings/{booking_id}` — Get booking details by ID or reference (`ST-XXXXXX`)
- `POST /api/bookings/{booking_id}/cancel` — Cancel a booking and release seats

### 💳 Razorpay Test Mode Payments
- `POST /api/payments` — Create a payment and generate Razorpay hosted payment link
- `GET /api/payments/{payment_id}` — Authoritative local payment verification (PENDING, PAID, FAILED, EXPIRED)
- `POST /api/payments/webhook/razorpay` — Authoritative Razorpay Webhook (verifies HMAC SHA256 signature, confirms booking)
- `POST /api/payments/deliver-link` — Saarthi AI delivery endpoint for dispatching payment links via WhatsApp/Telegram

### 🎟️ Digital Ticket
- `GET /api/tickets/{booking_id}` — Retrieve full digital ticket with embedded safe base64 verification QR code

---

## 💳 Razorpay Test Mode & Webhook Architecture

```
Customer Browser / Saarthi AI
          ↓
  POST /api/payments
          ↓
FastAPI Backend (PaymentLinkService)
          ↓ (Amount from booking, never trusted from client)
Razorpay Payment Links API (Test Mode)
          ↓
Returns Hosted Link: https://rzp.io/i/...
          ↓
Customer completes Sandbox payment on Razorpay hosted page
          ↓
Razorpay Server-to-Server Webhook
          ↓ (Signed with RAZORPAY_WEBHOOK_SECRET)
POST /api/payments/webhook/razorpay
          ↓
FastAPI verifies HMAC SHA-256 signature
          ↓
Payment -> PAID | Booking -> CONFIRMED | Seats -> CONFIRMED
          ↓
Digital Ticket & Boarding QR Available
```

### 🌐 Local Webhook Testing via Tunnel
To receive live Razorpay webhooks on localhost during development:
1. Run a tunnel (e.g. ngrok or cloudflared):
   ```bash
   ngrok http 8000
   ```
2. In the Razorpay Dashboard (Test Mode):
   - Go to **Settings → Webhooks → Add New Webhook**.
   - URL: `https://<your-ngrok-subdomain>.ngrok-free.app/api/payments/webhook/razorpay`
   - Secret: Value matching `RAZORPAY_WEBHOOK_SECRET` in `.env`
   - Active Events: `payment_link.paid`, `payment.captured`, `payment.failed`, `payment_link.expired`.

---

## 🤖 Saarthi AI Integration Architecture

Saarthi AI will map voice agent tool calls directly to these clean FastAPI services without touching the database:

| Saarthi AI Voice Intent | Backend API / Service |
|---|---|
| "Find buses from Hyderabad to Bangalore tomorrow" | `search_buses(...)` → `GET /api/buses/search` |
| "What are the details for Garuda AC bus?" | `get_bus_details(...)` → `GET /api/buses/{bus_id}` |
| "Check available seats for this bus" | `get_available_seats(...)` → `GET /api/buses/{bus_id}/seats` |
| "Recommend a lower window sleeper berth within Rs. 1000" | `recommend_seats(...)` → `POST /api/buses/{bus_id}/recommend-seats` |
| "Hold seat L5 for me while I enter details" | `hold_seats(...)` → `POST /api/seats/hold` |
| "Create the booking for Rahul Sharma, age 29" | `create_booking(...)` → `POST /api/bookings` |
| "Generate payment link for booking ST-8F4K92" | `create_payment_link(...)` → `POST /api/payments` |
| "Send payment link to traveler on WhatsApp" | `send_payment_link(...)` → `POST /api/payments/deliver-link` |
| "Check if payment was received" | `check_payment_status(...)` → `GET /api/payments/{id}` |
| "Send me my digital ticket and boarding QR" | `get_ticket(...)` → `GET /api/tickets/{booking_reference}` |

---

## 💻 Frontend Web Pages

- `/` — Home search page with quick popular routes
- `/search` — Bus search results with real-time filters and sorting
- `/bus/[id]` — Interactive seat layout map (Deck tabs for Sleeper, seat metadata badges, Saarthi AI Seat Advisor modal)
- `/booking` — Traveler details input, boarding/dropping selector, and booking creation
- `/payment` — Razorpay Test Mode checkout with hosted Pay Now link and authoritative verification
- `/booking/[id]` — Digital E-Ticket confirmation with dynamic QR code & print capability
- `/dashboard` — Past and upcoming bookings, ticket view, and cancellation
- `/login` — JWT login with 1-click Demo Customer and Admin credentials
- `/register` — Account registration

