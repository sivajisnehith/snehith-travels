from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.session import Base, engine, SessionLocal
from app.db.seed import seed_database
from app.api.api_router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure database schema is created
    Base.metadata.create_all(bind=engine)
    # Automatically seed initial demo data if database is fresh
    db = SessionLocal()
    try:
        from app.models.route import Route
        if db.query(Route).count() == 0:
            print("🚀 Initializing & seeding demo data for Snehith Travels...")
            seed_database(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Production-ready REST API for Snehith Travels bus booking platform — designed for human users & Saarthi AI voice integration.",
    version=settings.VERSION,
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(api_router)


@app.get("/")
def root():
    return {
        "message": "Welcome to Snehith Travels API",
        "docs": "/docs",
        "version": settings.VERSION,
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "snehith-travels-backend",
    }