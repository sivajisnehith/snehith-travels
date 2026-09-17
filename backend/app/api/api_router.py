from fastapi import APIRouter
from app.api.routes import auth, buses, seats, bookings, payments, tickets

api_router = APIRouter(prefix="/api")

api_router.include_router(auth.router)
api_router.include_router(buses.router)
api_router.include_router(seats.router)
api_router.include_router(bookings.router)
api_router.include_router(payments.router)
api_router.include_router(tickets.router)
