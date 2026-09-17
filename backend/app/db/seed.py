import os
import random
from datetime import datetime, date, timedelta, timezone
from sqlalchemy.orm import Session
from app.db.session import SessionLocal, Base, engine
from app.core.security import hash_password
from app.models.role import Role
from app.models.user import User
from app.models.route import Route
from app.models.bus import Bus
from app.models.seat import Seat
from app.models.booking import Booking
from app.models.booking_seat import BookingSeat
from app.models.passenger import Passenger
from app.models.payment import Payment


def seed_database(db: Session = None) -> None:
    close_db = False
    if db is None:
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        close_db = True

    try:
        print("[*] Seeding database...")

        # 1. Roles
        roles_data = [
            ("admin", "System Administrator with full management access"),
            ("customer", "Customer with booking access"),
        ]
        role_map = {}
        for r_name, r_desc in roles_data:
            role = db.query(Role).filter(Role.name == r_name).first()
            if not role:
                role = Role(name=r_name, description=r_desc)
                db.add(role)
                db.commit()
                db.refresh(role)
            role_map[r_name] = role
        print("  [+] Roles created")

        # 2. Users (Admin + Demo Customer)
        admin_email = "admin@snehithtravels.com"
        admin_user = db.query(User).filter(User.email == admin_email).first()
        if not admin_user:
            admin_user = User(
                name="Snehith Admin",
                email=admin_email,
                phone="9876543210",
                hashed_password=hash_password("AdminPassword123!"),
                role_id=role_map["admin"].id,
            )
            db.add(admin_user)

        demo_email = "demo@snehithtravels.com"
        demo_user = db.query(User).filter(User.email == demo_email).first()
        if not demo_user:
            demo_user = User(
                name="Rahul Sharma",
                email=demo_email,
                phone="9123456780",
                hashed_password=hash_password("DemoPassword123!"),
                role_id=role_map["customer"].id,
            )
            db.add(demo_user)
        db.commit()
        db.refresh(demo_user)
        print("  [+] Users created (admin: admin@snehithtravels.com, demo: demo@snehithtravels.com)")

        # 3. Routes
        routes_data = [
            ("Hyderabad", "Vijayawada", 275.0, 5.5),
            ("Vijayawada", "Hyderabad", 275.0, 5.5),
            ("Hyderabad", "Bangalore", 570.0, 9.0),
            ("Bangalore", "Hyderabad", 570.0, 9.0),
            ("Chennai", "Bangalore", 350.0, 6.0),
            ("Bangalore", "Chennai", 350.0, 6.0),
            ("Hyderabad", "Chennai", 630.0, 11.0),
            ("Chennai", "Hyderabad", 630.0, 11.0),
            ("Hyderabad", "Visakhapatnam", 620.0, 11.5),
            ("Visakhapatnam", "Hyderabad", 620.0, 11.5),
            ("Bangalore", "Vijayawada", 640.0, 11.0),
            ("Vijayawada", "Bangalore", 640.0, 11.0),
        ]

        route_objs = {}
        for orig, dest, dist, dur in routes_data:
            route = db.query(Route).filter(Route.origin == orig, Route.destination == dest).first()
            if not route:
                route = Route(
                    origin=orig,
                    destination=dest,
                    distance_km=dist,
                    estimated_duration_hours=dur,
                    is_active=True,
                )
                db.add(route)
                db.commit()
                db.refresh(route)
            route_objs[(orig, dest)] = route
        print(f"  [+] {len(route_objs)} Routes created")

        # 4. Buses & Layouts (AbhiBus/RedBus realistic 24-hour fleet)
        buses_config = [
            # --- Hyderabad -> Vijayawada ---
            {
                "route": ("Hyderabad", "Vijayawada"), "operator": "Krishnaveni Travels",
                "bus_name": "Krishnaveni Morning Superfast", "bus_type": "Semi-sleeper",
                "is_ac": True, "is_sleeper": False, "dep": "05:30", "arr": "11:00", "dur": "5h 30m",
                "price": 549.0, "rating": 4.5,
                "amenities": ["AC", "Charging Port", "Water Bottle"],
                "boarding": ["Miyapur (05:00)", "Ameerpet (05:30)", "LB Nagar (06:15)"],
                "dropping": ["Gollapudi (10:45)", "Benz Circle (11:00)"],
            },
            {
                "route": ("Hyderabad", "Vijayawada"), "operator": "Snehith Travels",
                "bus_name": "Snehith Express AC Seater", "bus_type": "AC Seater",
                "is_ac": True, "is_sleeper": False, "dep": "07:15", "arr": "12:45", "dur": "5h 30m",
                "price": 499.0, "rating": 4.7,
                "amenities": ["AC", "Charging Port", "Water Bottle", "Reading Light"],
                "boarding": ["KPHB (06:45)", "Lakdikapool (07:15)", "LB Nagar (08:00)"],
                "dropping": ["Bhavanipuram (12:30)", "Bus Stand (12:45)"],
            },
            {
                "route": ("Hyderabad", "Vijayawada"), "operator": "APSRTC Amaravathi",
                "bus_name": "Amaravathi Multi-Axle AC", "bus_type": "AC Seater",
                "is_ac": True, "is_sleeper": False, "dep": "09:00", "arr": "14:30", "dur": "5h 30m",
                "price": 599.0, "rating": 4.6,
                "amenities": ["AC", "Live Tracking", "Emergency Exit", "Water Bottle"],
                "boarding": ["MGBS (09:00)", "LB Nagar (09:40)"],
                "dropping": ["Pandit Nehru Bus Station (14:30)"],
            },
            {
                "route": ("Hyderabad", "Vijayawada"), "operator": "Orange Tours & Travels",
                "bus_name": "Orange InterCity AC Sleeper", "bus_type": "AC Sleeper",
                "is_ac": True, "is_sleeper": True, "dep": "12:30", "arr": "18:00", "dur": "5h 30m",
                "price": 799.0, "rating": 4.8,
                "amenities": ["WiFi", "AC", "Blanket", "Charging Port", "Water Bottle"],
                "boarding": ["Gachibowli (11:45)", "Ameerpet (12:30)", "Dilsukhnagar (13:15)"],
                "dropping": ["Benz Circle (17:45)", "Ramavarappadu (18:00)"],
            },
            {
                "route": ("Hyderabad", "Vijayawada"), "operator": "Morning Star Travels",
                "bus_name": "Morning Star Day Express", "bus_type": "Semi-sleeper",
                "is_ac": True, "is_sleeper": False, "dep": "14:15", "arr": "19:45", "dur": "5h 30m",
                "price": 550.0, "rating": 4.4,
                "amenities": ["AC", "Charging Port", "Movie Screen"],
                "boarding": ["SR Nagar (14:15)", "LB Nagar (15:00)"],
                "dropping": ["Varadhi (19:30)", "Benz Circle (19:45)"],
            },
            {
                "route": ("Hyderabad", "Vijayawada"), "operator": "TSRTC Rajadhani",
                "bus_name": "Rajadhani AC Express", "bus_type": "AC Seater",
                "is_ac": True, "is_sleeper": False, "dep": "16:30", "arr": "22:00", "dur": "5h 30m",
                "price": 620.0, "rating": 4.5,
                "amenities": ["AC", "Charging Port", "Water Bottle"],
                "boarding": ["JBS (15:45)", "MGBS (16:30)", "LB Nagar (17:15)"],
                "dropping": ["Bhavanipuram (21:45)", "PNBS (22:00)"],
            },
            {
                "route": ("Hyderabad", "Vijayawada"), "operator": "Kaveri Travels",
                "bus_name": "Kaveri Twilight AC Sleeper", "bus_type": "AC Sleeper",
                "is_ac": True, "is_sleeper": True, "dep": "18:00", "arr": "23:30", "dur": "5h 30m",
                "price": 850.0, "rating": 4.7,
                "amenities": ["WiFi", "AC", "Blanket", "Pillow", "Charging Port"],
                "boarding": ["Kukatpally (17:15)", "Ameerpet (18:00)", "LB Nagar (18:45)"],
                "dropping": ["Benz Circle (23:15)", "Autonagar (23:30)"],
            },
            {
                "route": ("Hyderabad", "Vijayawada"), "operator": "IntrCity SmartBus",
                "bus_name": "IntrCity SmartBus Electric AC", "bus_type": "AC Sleeper",
                "is_ac": True, "is_sleeper": True, "dep": "19:30", "arr": "01:00", "dur": "5h 30m",
                "price": 899.0, "rating": 4.9,
                "amenities": ["WiFi", "AC", "Smart Lounge Access", "Blanket", "Water Bottle"],
                "boarding": ["Hitec City (18:45)", "Lakdikapool (19:30)", "LB Nagar (20:15)"],
                "dropping": ["Benz Circle (00:45)", "PNBS (01:00)"],
            },
            {
                "route": ("Hyderabad", "Vijayawada"), "operator": "Zingbus Plus",
                "bus_name": "Zingbus Volvo 9600 Multi-Axle", "bus_type": "AC Sleeper",
                "is_ac": True, "is_sleeper": True, "dep": "21:00", "arr": "02:45", "dur": "5h 45m",
                "price": 999.0, "rating": 4.8,
                "amenities": ["WiFi", "Premium Blanket", "Snacks", "Live Tracking", "Emergency SOS"],
                "boarding": ["Gachibowli (20:15)", "Ameerpet (21:00)", "LB Nagar (21:45)"],
                "dropping": ["Benz Circle (02:30)", "Bus Stand (02:45)"],
            },
            {
                "route": ("Hyderabad", "Vijayawada"), "operator": "Snehith Travels",
                "bus_name": "Garuda AC Sleeper", "bus_type": "AC Sleeper",
                "is_ac": True, "is_sleeper": True, "dep": "22:30", "arr": "04:30", "dur": "6h 00m",
                "price": 899.0, "rating": 4.8,
                "amenities": ["WiFi", "AC", "Blanket", "Charging Port", "Water Bottle", "Reading Light"],
                "boarding": ["Ameerpet (22:30)", "Gachibowli (22:45)", "Lakdikapool (23:15)", "LB Nagar (23:45)"],
                "dropping": ["Benz Circle (04:15)", "Bus Stand (04:30)"],
            },
            {
                "route": ("Hyderabad", "Vijayawada"), "operator": "Snehith Travels",
                "bus_name": "Express Non-AC Sleeper", "bus_type": "Non-AC Sleeper",
                "is_ac": False, "is_sleeper": True, "dep": "23:15", "arr": "05:15", "dur": "6h 00m",
                "price": 649.0, "rating": 4.2,
                "amenities": ["Charging Port", "Water Bottle"],
                "boarding": ["Kukatpally (22:45)", "SR Nagar (23:15)", "Dilsukhnagar (23:55)"],
                "dropping": ["Bhavanipuram (05:00)", "Bus Stand (05:15)"],
            },
            {
                "route": ("Hyderabad", "Vijayawada"), "operator": "Snehith Travels",
                "bus_name": "Snehith Platinum Class Multi-Axle", "bus_type": "AC Sleeper",
                "is_ac": True, "is_sleeper": True, "dep": "23:55", "arr": "05:30", "dur": "5h 35m",
                "price": 1099.0, "rating": 4.9,
                "amenities": ["WiFi", "AC", "Luxury Blanket", "Pillow", "Snack Pack", "Charging Port"],
                "boarding": ["Miyapur (22:45)", "Ameerpet (23:30)", "LB Nagar (00:15)"],
                "dropping": ["Benz Circle (05:15)", "Gollapudi (05:30)"],
            },

            # --- Vijayawada -> Hyderabad ---
            {
                "route": ("Vijayawada", "Hyderabad"), "operator": "Krishnaveni Travels",
                "bus_name": "Krishnaveni Dawn Express", "bus_type": "Semi-sleeper",
                "is_ac": True, "is_sleeper": False, "dep": "06:00", "arr": "11:30", "dur": "5h 30m",
                "price": 549.0, "rating": 4.5,
                "amenities": ["AC", "Charging Port", "Water Bottle"],
                "boarding": ["Benz Circle (06:00)", "Gollapudi (06:20)"],
                "dropping": ["LB Nagar (10:45)", "Ameerpet (11:30)"],
            },
            {
                "route": ("Vijayawada", "Hyderabad"), "operator": "APSRTC Amaravathi",
                "bus_name": "Amaravathi Capital Express", "bus_type": "AC Seater",
                "is_ac": True, "is_sleeper": False, "dep": "08:30", "arr": "14:00", "dur": "5h 30m",
                "price": 599.0, "rating": 4.6,
                "amenities": ["AC", "Charging Port", "Water Bottle"],
                "boarding": ["PNBS (08:30)", "Varadhi (08:45)"],
                "dropping": ["LB Nagar (13:15)", "MGBS (14:00)"],
            },
            {
                "route": ("Vijayawada", "Hyderabad"), "operator": "Snehith Travels",
                "bus_name": "Amaravathi AC Seater", "bus_type": "AC Seater",
                "is_ac": True, "is_sleeper": False, "dep": "14:30", "arr": "20:00", "dur": "5h 30m",
                "price": 549.0, "rating": 4.4,
                "amenities": ["AC", "Charging Port", "Movie Screen"],
                "boarding": ["Benz Circle (14:30)", "Varadhi (14:45)"],
                "dropping": ["LB Nagar (19:30)", "Ameerpet (20:00)"],
            },
            {
                "route": ("Vijayawada", "Hyderabad"), "operator": "Orange Tours & Travels",
                "bus_name": "Orange Evening AC Sleeper", "bus_type": "AC Sleeper",
                "is_ac": True, "is_sleeper": True, "dep": "17:45", "arr": "23:15", "dur": "5h 30m",
                "price": 799.0, "rating": 4.8,
                "amenities": ["WiFi", "AC", "Blanket", "Charging Port", "Water Bottle"],
                "boarding": ["Ramavarappadu (17:30)", "Benz Circle (17:45)"],
                "dropping": ["LB Nagar (22:30)", "Ameerpet (23:15)"],
            },
            {
                "route": ("Vijayawada", "Hyderabad"), "operator": "Snehith Travels",
                "bus_name": "Rajadhani AC Sleeper", "bus_type": "AC Sleeper",
                "is_ac": True, "is_sleeper": True, "dep": "23:00", "arr": "05:00", "dur": "6h 00m",
                "price": 899.0, "rating": 4.7,
                "amenities": ["WiFi", "AC", "Blanket", "Charging Port", "Water Bottle"],
                "boarding": ["Benz Circle (23:00)", "Old Bus Stand (23:20)"],
                "dropping": ["LB Nagar (04:30)", "Lakdikapool (04:50)", "Ameerpet (05:00)"],
            },
            {
                "route": ("Vijayawada", "Hyderabad"), "operator": "Zingbus Plus",
                "bus_name": "Zingbus Midnight Multi-Axle", "bus_type": "AC Sleeper",
                "is_ac": True, "is_sleeper": True, "dep": "23:45", "arr": "05:15", "dur": "5h 30m",
                "price": 950.0, "rating": 4.9,
                "amenities": ["WiFi", "Luxury Blanket", "Pillow", "Charging Port"],
                "boarding": ["Benz Circle (23:45)", "Bhavanipuram (00:05)"],
                "dropping": ["LB Nagar (04:45)", "Gachibowli (05:15)"],
            },

            # --- Hyderabad -> Bangalore ---
            {
                "route": ("Hyderabad", "Bangalore"), "operator": "IntrCity SmartBus",
                "bus_name": "IntrCity Daytime Executive", "bus_type": "AC Seater",
                "is_ac": True, "is_sleeper": False, "dep": "06:30", "arr": "15:30", "dur": "9h 00m",
                "price": 899.0, "rating": 4.7,
                "amenities": ["WiFi", "Charging Port", "Water Bottle", "Smart Bus Lounge Access"],
                "boarding": ["Gachibowli (06:00)", "Mehdipatnam (06:30)", "Shamshabad (07:15)"],
                "dropping": ["Hebbal (14:45)", "Majestic (15:15)", "Silk Board (15:30)"],
            },
            {
                "route": ("Hyderabad", "Bangalore"), "operator": "VRL Travels",
                "bus_name": "VRL I-Shift Multi-Axle AC Sleeper", "bus_type": "AC Sleeper",
                "is_ac": True, "is_sleeper": True, "dep": "14:00", "arr": "23:00", "dur": "9h 00m",
                "price": 1150.0, "rating": 4.6,
                "amenities": ["WiFi", "AC", "Blanket", "Charging Port", "Reading Light"],
                "boarding": ["KPHB (13:15)", "Ameerpet (14:00)", "Aramghar (14:45)"],
                "dropping": ["Yelahanka (22:15)", "Majestic (22:45)", "Electronic City (23:15)"],
            },
            {
                "route": ("Hyderabad", "Bangalore"), "operator": "Orange Tours & Travels",
                "bus_name": "Orange Scania Multi-Axle AC Sleeper", "bus_type": "AC Sleeper",
                "is_ac": True, "is_sleeper": True, "dep": "18:30", "arr": "04:00", "dur": "9h 30m",
                "price": 1250.0, "rating": 4.8,
                "amenities": ["WiFi", "AC", "Blanket", "Pillow", "Snack Pack", "Charging Port"],
                "boarding": ["Miyapur (17:45)", "Ameerpet (18:30)", "Shamshabad (19:30)"],
                "dropping": ["Hebbal (03:15)", "Majestic (03:45)", "Silk Board (04:00)"],
            },
            {
                "route": ("Hyderabad", "Bangalore"), "operator": "Kaveri Travels",
                "bus_name": "Kaveri BharatBenz AC Sleeper", "bus_type": "AC Sleeper",
                "is_ac": True, "is_sleeper": True, "dep": "20:00", "arr": "05:30", "dur": "9h 30m",
                "price": 1200.0, "rating": 4.7,
                "amenities": ["WiFi", "AC", "Blanket", "Charging Port", "Water Bottle"],
                "boarding": ["Hitec City (19:15)", "Mehdipatnam (20:00)", "Aramghar (20:45)"],
                "dropping": ["Yelahanka (04:45)", "Majestic (05:15)", "Silk Board (05:30)"],
            },
            {
                "route": ("Hyderabad", "Bangalore"), "operator": "Snehith Travels",
                "bus_name": "Deccan Royal AC Sleeper", "bus_type": "AC Sleeper",
                "is_ac": True, "is_sleeper": True, "dep": "21:00", "arr": "06:30", "dur": "9h 30m",
                "price": 1299.0, "rating": 4.9,
                "amenities": ["WiFi", "AC", "Blanket", "Pillow", "Snack Pack", "Charging Port"],
                "boarding": ["Gachibowli (20:30)", "Mehdipatnam (21:00)", "Shamshabad (21:45)"],
                "dropping": ["Hebbal (05:45)", "Majestic (06:15)", "Silk Board (06:30)"],
            },
            {
                "route": ("Hyderabad", "Bangalore"), "operator": "TSRTC Garuda Plus",
                "bus_name": "Garuda Plus Volvo B11R", "bus_type": "AC Sleeper",
                "is_ac": True, "is_sleeper": True, "dep": "21:45", "arr": "07:00", "dur": "9h 15m",
                "price": 1199.0, "rating": 4.7,
                "amenities": ["AC", "Blanket", "Water Bottle", "Live GPS"],
                "boarding": ["MGBS (21:45)", "Shamshabad (22:30)"],
                "dropping": ["Hebbal (06:15)", "Kempegowda BS (07:00)"],
            },
            {
                "route": ("Hyderabad", "Bangalore"), "operator": "Snehith Travels",
                "bus_name": "Cyberliner Semi-Sleeper", "bus_type": "Semi-sleeper",
                "is_ac": True, "is_sleeper": False, "dep": "22:00", "arr": "07:30", "dur": "9h 30m",
                "price": 899.0, "rating": 4.6,
                "amenities": ["AC", "Charging Port", "Blanket", "Water Bottle"],
                "boarding": ["KPHB (21:15)", "Ameerpet (22:00)", "Aramghar (22:45)"],
                "dropping": ["Yelahanka (06:45)", "Majestic (07:15)", "Electronic City (07:45)"],
            },
            {
                "route": ("Hyderabad", "Bangalore"), "operator": "Jabbar Travels",
                "bus_name": "Jabbar Luxury AC Sleeper", "bus_type": "AC Sleeper",
                "is_ac": True, "is_sleeper": True, "dep": "22:30", "arr": "07:45", "dur": "9h 15m",
                "price": 1099.0, "rating": 4.5,
                "amenities": ["AC", "Charging Port", "Blanket"],
                "boarding": ["Lakdikapool (22:30)", "Aramghar (23:15)"],
                "dropping": ["Hebbal (07:00)", "Majestic (07:30)", "Madiwala (07:45)"],
            },
            {
                "route": ("Hyderabad", "Bangalore"), "operator": "Greenline Travels",
                "bus_name": "Greenline Electric AC Sleeper", "bus_type": "Electric AC Luxury",
                "is_ac": True, "is_sleeper": True, "dep": "23:15", "arr": "08:15", "dur": "9h 00m",
                "price": 1399.0, "rating": 4.9,
                "amenities": ["Zero Emission", "WiFi", "AC", "Luxury Blanket", "Pillow", "Charging Port"],
                "boarding": ["Gachibowli (22:45)", "Shamshabad (23:45)"],
                "dropping": ["Hebbal (07:30)", "Silk Board (08:15)"],
            },
            {
                "route": ("Hyderabad", "Bangalore"), "operator": "Snehith Travels",
                "bus_name": "Snehith Gold Class Volvo 9600", "bus_type": "AC Sleeper",
                "is_ac": True, "is_sleeper": True, "dep": "23:55", "arr": "08:45", "dur": "8h 50m",
                "price": 1450.0, "rating": 5.0,
                "amenities": ["WiFi", "AC", "Luxury Bedding", "Hot Beverage", "Individual TV Screens", "Charging Port"],
                "boarding": ["Miyapur (22:45)", "Ameerpet (23:30)", "Shamshabad (00:25)"],
                "dropping": ["Hebbal (07:55)", "Majestic (08:20)", "Silk Board (08:45)"],
            },

            # --- Bangalore -> Hyderabad ---
            {
                "route": ("Bangalore", "Hyderabad"), "operator": "IntrCity SmartBus",
                "bus_name": "IntrCity Morning Express", "bus_type": "AC Seater",
                "is_ac": True, "is_sleeper": False, "dep": "07:00", "arr": "16:00", "dur": "9h 00m",
                "price": 899.0, "rating": 4.7,
                "amenities": ["WiFi", "Charging Port", "Water Bottle"],
                "boarding": ["Silk Board (06:30)", "Majestic (07:00)", "Hebbal (07:30)"],
                "dropping": ["Shamshabad (14:45)", "Ameerpet (15:30)", "Gachibowli (16:00)"],
            },
            {
                "route": ("Bangalore", "Hyderabad"), "operator": "VRL Travels",
                "bus_name": "VRL Afternoon AC Sleeper", "bus_type": "AC Sleeper",
                "is_ac": True, "is_sleeper": True, "dep": "15:00", "arr": "00:30", "dur": "9h 30m",
                "price": 1150.0, "rating": 4.6,
                "amenities": ["WiFi", "AC", "Blanket", "Charging Port"],
                "boarding": ["Electronic City (14:15)", "Majestic (15:00)", "Hebbal (15:30)"],
                "dropping": ["Shamshabad (23:30)", "Ameerpet (00:30)"],
            },
            {
                "route": ("Bangalore", "Hyderabad"), "operator": "Orange Tours & Travels",
                "bus_name": "Orange Twilight Multi-Axle", "bus_type": "AC Sleeper",
                "is_ac": True, "is_sleeper": True, "dep": "19:30", "arr": "05:00", "dur": "9h 30m",
                "price": 1250.0, "rating": 4.8,
                "amenities": ["WiFi", "AC", "Blanket", "Pillow", "Charging Port"],
                "boarding": ["Silk Board (18:45)", "Majestic (19:30)", "Hebbal (20:00)"],
                "dropping": ["Shamshabad (04:15)", "Mehdipatnam (05:00)"],
            },
            {
                "route": ("Bangalore", "Hyderabad"), "operator": "Snehith Travels",
                "bus_name": "Silicon Express AC Sleeper", "bus_type": "AC Sleeper",
                "is_ac": True, "is_sleeper": True, "dep": "21:30", "arr": "07:00", "dur": "9h 30m",
                "price": 1299.0, "rating": 4.8,
                "amenities": ["WiFi", "AC", "Blanket", "Pillow", "Charging Port"],
                "boarding": ["Electronic City (20:30)", "Silk Board (21:00)", "Majestic (21:30)", "Hebbal (22:00)"],
                "dropping": ["Shamshabad (06:00)", "Aramghar (06:30)", "Mehdipatnam (07:00)"],
            },
            {
                "route": ("Bangalore", "Hyderabad"), "operator": "Kaveri Travels",
                "bus_name": "Kaveri Night Queen AC Sleeper", "bus_type": "AC Sleeper",
                "is_ac": True, "is_sleeper": True, "dep": "22:15", "arr": "07:30", "dur": "9h 15m",
                "price": 1200.0, "rating": 4.7,
                "amenities": ["AC", "Blanket", "Charging Port", "Water Bottle"],
                "boarding": ["Madiwala (21:30)", "Majestic (22:15)", "Yelahanka (23:00)"],
                "dropping": ["Aramghar (06:45)", "Ameerpet (07:30)"],
            },
            {
                "route": ("Bangalore", "Hyderabad"), "operator": "Zingbus Plus",
                "bus_name": "Zingbus Platinum Sleeper", "bus_type": "AC Sleeper",
                "is_ac": True, "is_sleeper": True, "dep": "23:30", "arr": "08:15", "dur": "8h 45m",
                "price": 1350.0, "rating": 4.9,
                "amenities": ["WiFi", "Premium Bedding", "Snacks", "Live GPS"],
                "boarding": ["Silk Board (22:45)", "Majestic (23:30)", "Hebbal (00:05)"],
                "dropping": ["Shamshabad (07:15)", "Gachibowli (08:15)"],
            },

            # --- Bangalore -> Chennai ---
            {
                "route": ("Bangalore", "Chennai"), "operator": "Snehith Travels",
                "bus_name": "Garden City AC Seater", "bus_type": "AC Seater",
                "is_ac": True, "is_sleeper": False, "dep": "06:00", "arr": "12:00", "dur": "6h 00m",
                "price": 599.0, "rating": 4.5,
                "amenities": ["AC", "Charging Port", "Water Bottle"],
                "boarding": ["Majestic (06:00)", "Indiranagar (06:25)", "Hosur (07:30)"],
                "dropping": ["Poonamallee (11:15)", "Koyambedu (12:00)"],
            },
            {
                "route": ("Bangalore", "Chennai"), "operator": "IntrCity SmartBus",
                "bus_name": "IntrCity SmartBus Day Liner", "bus_type": "AC Seater",
                "is_ac": True, "is_sleeper": False, "dep": "10:30", "arr": "16:30", "dur": "6h 00m",
                "price": 650.0, "rating": 4.8,
                "amenities": ["WiFi", "AC", "Smart Lounge Access", "Water Bottle"],
                "boarding": ["Electronic City (10:00)", "Hosur (10:45)"],
                "dropping": ["Guindy (16:00)", "Koyambedu (16:30)"],
            },
            {
                "route": ("Bangalore", "Chennai"), "operator": "Snehith Travels",
                "bus_name": "Garden City Afternoon Seater", "bus_type": "AC Seater",
                "is_ac": True, "is_sleeper": False, "dep": "14:00", "arr": "20:00", "dur": "6h 00m",
                "price": 649.0, "rating": 4.5,
                "amenities": ["AC", "Charging Port", "Water Bottle"],
                "boarding": ["Majestic (14:00)", "Indiranagar (14:25)", "Hosur (15:30)"],
                "dropping": ["Poonamallee (19:15)", "Koyambedu (20:00)"],
            },
            {
                "route": ("Bangalore", "Chennai"), "operator": "Orange Tours & Travels",
                "bus_name": "Orange Executive AC Sleeper", "bus_type": "AC Sleeper",
                "is_ac": True, "is_sleeper": True, "dep": "19:00", "arr": "01:00", "dur": "6h 00m",
                "price": 899.0, "rating": 4.7,
                "amenities": ["WiFi", "AC", "Blanket", "Charging Port"],
                "boarding": ["Madiwala (18:15)", "Electronic City (19:00)"],
                "dropping": ["Sriperumbudur (00:15)", "Koyambedu (01:00)"],
            },
            {
                "route": ("Bangalore", "Chennai"), "operator": "Kaveri Travels",
                "bus_name": "Kaveri Night AC Sleeper", "bus_type": "AC Sleeper",
                "is_ac": True, "is_sleeper": True, "dep": "22:30", "arr": "04:45", "dur": "6h 15m",
                "price": 949.0, "rating": 4.8,
                "amenities": ["AC", "Blanket", "Pillow", "Charging Port"],
                "boarding": ["Majestic (22:30)", "Silk Board (23:00)", "Hosur (23:45)"],
                "dropping": ["Poonamallee (04:15)", "Koyambedu (04:45)"],
            },
            {
                "route": ("Bangalore", "Chennai"), "operator": "Zingbus Plus",
                "bus_name": "Zingbus Midnight Star AC Sleeper", "bus_type": "AC Sleeper",
                "is_ac": True, "is_sleeper": True, "dep": "23:45", "arr": "05:45", "dur": "6h 00m",
                "price": 999.0, "rating": 4.9,
                "amenities": ["WiFi", "Luxury Bedding", "Emergency SOS"],
                "boarding": ["Electronic City (23:15)", "Hosur (00:05)"],
                "dropping": ["Guindy (05:15)", "Koyambedu (05:45)"],
            },

            # --- Chennai -> Bangalore ---
            {
                "route": ("Chennai", "Bangalore"), "operator": "Snehith Travels",
                "bus_name": "Coromandel Morning AC Seater", "bus_type": "AC Seater",
                "is_ac": True, "is_sleeper": False, "dep": "06:30", "arr": "12:30", "dur": "6h 00m",
                "price": 599.0, "rating": 4.6,
                "amenities": ["AC", "Charging Port", "Water Bottle"],
                "boarding": ["Koyambedu (06:30)", "Poonamallee (07:00)"],
                "dropping": ["Hosur (11:30)", "Majestic (12:30)"],
            },
            {
                "route": ("Chennai", "Bangalore"), "operator": "IntrCity SmartBus",
                "bus_name": "IntrCity Afternoon SmartBus", "bus_type": "AC Seater",
                "is_ac": True, "is_sleeper": False, "dep": "14:00", "arr": "20:00", "dur": "6h 00m",
                "price": 649.0, "rating": 4.8,
                "amenities": ["WiFi", "AC", "Smart Lounge", "Water Bottle"],
                "boarding": ["Guindy (13:30)", "Koyambedu (14:00)"],
                "dropping": ["Electronic City (19:15)", "Majestic (20:00)"],
            },
            {
                "route": ("Chennai", "Bangalore"), "operator": "Orange Tours & Travels",
                "bus_name": "Orange Evening Sleeper", "bus_type": "AC Sleeper",
                "is_ac": True, "is_sleeper": True, "dep": "18:30", "arr": "00:45", "dur": "6h 15m",
                "price": 899.0, "rating": 4.7,
                "amenities": ["WiFi", "AC", "Blanket", "Charging Port"],
                "boarding": ["Koyambedu (18:30)", "Sriperumbudur (19:15)"],
                "dropping": ["Hosur (23:45)", "Electronic City (00:15)", "Majestic (00:45)"],
            },
            {
                "route": ("Chennai", "Bangalore"), "operator": "Snehith Travels",
                "bus_name": "Coromandel AC Sleeper", "bus_type": "AC Sleeper",
                "is_ac": True, "is_sleeper": True, "dep": "23:00", "arr": "05:30", "dur": "6h 30m",
                "price": 949.0, "rating": 4.7,
                "amenities": ["AC", "Blanket", "Charging Port", "Water Bottle"],
                "boarding": ["Koyambedu (22:30)", "Guindy (23:00)", "Sriperumbudur (23:45)"],
                "dropping": ["Hosur (04:45)", "Electronic City (05:10)", "Majestic (05:30)"],
            },
            {
                "route": ("Chennai", "Bangalore"), "operator": "Kaveri Travels",
                "bus_name": "Kaveri Midnight Express Sleeper", "bus_type": "AC Sleeper",
                "is_ac": True, "is_sleeper": True, "dep": "23:45", "arr": "06:00", "dur": "6h 15m",
                "price": 999.0, "rating": 4.8,
                "amenities": ["WiFi", "AC", "Blanket", "Pillow"],
                "boarding": ["Koyambedu (23:45)", "Poonamallee (00:15)"],
                "dropping": ["Electronic City (05:30)", "Majestic (06:00)"],
            },

            # --- Hyderabad -> Chennai ---
            {
                "route": ("Hyderabad", "Chennai"), "operator": "Snehith Travels",
                "bus_name": "Coastal Queen AC Sleeper", "bus_type": "AC Sleeper",
                "is_ac": True, "is_sleeper": True, "dep": "19:00", "arr": "06:30", "dur": "11h 30m",
                "price": 1399.0, "rating": 4.8,
                "amenities": ["WiFi", "AC", "Blanket", "Pillow", "Snack Pack", "Charging Port"],
                "boarding": ["KPHB (18:15)", "Ameerpet (19:00)", "LB Nagar (19:45)"],
                "dropping": ["Madhavaram (05:45)", "Koyambedu (06:30)"],
            },
            {
                "route": ("Hyderabad", "Chennai"), "operator": "Orange Tours & Travels",
                "bus_name": "Orange Chennai Express Multi-Axle", "bus_type": "AC Sleeper",
                "is_ac": True, "is_sleeper": True, "dep": "20:15", "arr": "07:30", "dur": "11h 15m",
                "price": 1450.0, "rating": 4.9,
                "amenities": ["WiFi", "AC", "Blanket", "Pillow", "Charging Port", "Water Bottle"],
                "boarding": ["Gachibowli (19:30)", "Ameerpet (20:15)", "LB Nagar (21:00)"],
                "dropping": ["Madhavaram (06:45)", "Koyambedu (07:30)"],
            },
            {
                "route": ("Hyderabad", "Chennai"), "operator": "Kaveri Travels",
                "bus_name": "Kaveri Grand AC Sleeper", "bus_type": "AC Sleeper",
                "is_ac": True, "is_sleeper": True, "dep": "21:30", "arr": "08:45", "dur": "11h 15m",
                "price": 1350.0, "rating": 4.7,
                "amenities": ["AC", "Blanket", "Charging Port"],
                "boarding": ["Miyapur (20:45)", "Lakdikapool (21:30)", "LB Nagar (22:15)"],
                "dropping": ["Koyambedu (08:45)"],
            },

            # --- Chennai -> Hyderabad ---
            {
                "route": ("Chennai", "Hyderabad"), "operator": "Snehith Travels",
                "bus_name": "Coastal King AC Sleeper", "bus_type": "AC Sleeper",
                "is_ac": True, "is_sleeper": True, "dep": "19:30", "arr": "07:00", "dur": "11h 30m",
                "price": 1399.0, "rating": 4.8,
                "amenities": ["WiFi", "AC", "Blanket", "Pillow", "Charging Port"],
                "boarding": ["Koyambedu (19:30)", "Madhavaram (20:15)"],
                "dropping": ["LB Nagar (05:45)", "Ameerpet (06:30)", "KPHB (07:00)"],
            },
            {
                "route": ("Chennai", "Hyderabad"), "operator": "Orange Tours & Travels",
                "bus_name": "Orange Hyderabad Scania Sleeper", "bus_type": "AC Sleeper",
                "is_ac": True, "is_sleeper": True, "dep": "21:00", "arr": "08:15", "dur": "11h 15m",
                "price": 1450.0, "rating": 4.9,
                "amenities": ["WiFi", "AC", "Blanket", "Pillow", "Charging Port"],
                "boarding": ["Koyambedu (21:00)", "Madhavaram (21:40)"],
                "dropping": ["LB Nagar (07:00)", "Ameerpet (07:45)", "Gachibowli (08:15)"],
            },

            # --- Hyderabad -> Visakhapatnam ---
            {
                "route": ("Hyderabad", "Visakhapatnam"), "operator": "Snehith Travels",
                "bus_name": "Vizag Bay Express AC Sleeper", "bus_type": "AC Sleeper",
                "is_ac": True, "is_sleeper": True, "dep": "18:30", "arr": "06:00", "dur": "11h 30m",
                "price": 1350.0, "rating": 4.8,
                "amenities": ["WiFi", "AC", "Blanket", "Pillow", "Charging Port"],
                "boarding": ["Miyapur (17:45)", "Ameerpet (18:30)", "LB Nagar (19:15)"],
                "dropping": ["Gajuwaka (05:15)", "RTC Complex Vizag (06:00)"],
            },
            {
                "route": ("Hyderabad", "Visakhapatnam"), "operator": "Orange Tours & Travels",
                "bus_name": "Orange Vizag Volvo Multi-Axle", "bus_type": "AC Sleeper",
                "is_ac": True, "is_sleeper": True, "dep": "20:00", "arr": "07:30", "dur": "11h 30m",
                "price": 1450.0, "rating": 4.9,
                "amenities": ["WiFi", "AC", "Luxury Blanket", "Pillow", "Snacks"],
                "boarding": ["Gachibowli (19:15)", "Lakdikapool (20:00)", "LB Nagar (20:45)"],
                "dropping": ["NAD Junction (06:45)", "RTC Complex (07:30)"],
            },
            {
                "route": ("Hyderabad", "Visakhapatnam"), "operator": "Morning Star Travels",
                "bus_name": "Morning Star Vizag Classic", "bus_type": "Semi-sleeper",
                "is_ac": True, "is_sleeper": False, "dep": "21:15", "arr": "08:45", "dur": "11h 30m",
                "price": 899.0, "rating": 4.4,
                "amenities": ["AC", "Charging Port", "Water Bottle"],
                "boarding": ["KPHB (20:30)", "Ameerpet (21:15)", "LB Nagar (22:00)"],
                "dropping": ["Gajuwaka (08:00)", "RTC Complex (08:45)"],
            },

            # --- Visakhapatnam -> Hyderabad ---
            {
                "route": ("Visakhapatnam", "Hyderabad"), "operator": "Snehith Travels",
                "bus_name": "Deccan Bay Express AC Sleeper", "bus_type": "AC Sleeper",
                "is_ac": True, "is_sleeper": True, "dep": "19:00", "arr": "06:30", "dur": "11h 30m",
                "price": 1350.0, "rating": 4.8,
                "amenities": ["WiFi", "AC", "Blanket", "Pillow", "Charging Port"],
                "boarding": ["RTC Complex (19:00)", "NAD Junction (19:30)", "Gajuwaka (20:00)"],
                "dropping": ["LB Nagar (05:15)", "Ameerpet (06:00)", "Miyapur (06:30)"],
            },
            {
                "route": ("Visakhapatnam", "Hyderabad"), "operator": "Orange Tours & Travels",
                "bus_name": "Orange Hyderabad Luxury Multi-Axle", "bus_type": "AC Sleeper",
                "is_ac": True, "is_sleeper": True, "dep": "20:30", "arr": "08:00", "dur": "11h 30m",
                "price": 1450.0, "rating": 4.9,
                "amenities": ["WiFi", "AC", "Luxury Blanket", "Pillow", "Charging Port"],
                "boarding": ["RTC Complex (20:30)", "Gajuwaka (21:15)"],
                "dropping": ["LB Nagar (06:45)", "Ameerpet (07:30)", "Gachibowli (08:00)"],
            },
        ]

        created_buses = []
        for b_cfg in buses_config:
            route_obj = route_objs.get(b_cfg["route"])
            if not route_obj:
                continue
            bus = db.query(Bus).filter(
                Bus.bus_name == b_cfg["bus_name"],
                Bus.route_id == route_obj.id,
                Bus.departure_time == b_cfg["dep"],
            ).first()
            if not bus:
                bus = Bus(
                    route_id=route_obj.id,
                    operator=b_cfg.get("operator", "Snehith Travels"),
                    bus_name=b_cfg["bus_name"],
                    bus_type=b_cfg["bus_type"],
                    is_ac=b_cfg["is_ac"],
                    is_sleeper=b_cfg["is_sleeper"],
                    departure_time=b_cfg["dep"],
                    arrival_time=b_cfg["arr"],
                    duration=b_cfg["dur"],
                    starting_price=b_cfg["price"],
                    amenities=b_cfg["amenities"],
                    rating=b_cfg["rating"],
                    total_seats=30 if b_cfg["is_sleeper"] else 32,
                    boarding_points=b_cfg["boarding"],
                    dropping_points=b_cfg["dropping"],
                )
                db.add(bus)
                db.commit()
                db.refresh(bus)

                # Generate seats for this bus
                generate_bus_seats(db, bus)

            created_buses.append(bus)

        print(f"  [+] {len(created_buses)} Buses and their full Seat layouts created")

        # 5. Seed some realistic occupied bookings for today and next 7 days
        today = date.today()
        seed_sample_bookings(db, created_buses, demo_user, today)
        print("  [+] Realistic occupied seats and demo bookings generated")

        print("[SUCCESS] Database seeding completed successfully!")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Error while seeding database: {e}")
        raise
    finally:
        if close_db:
            db.close()


def generate_bus_seats(db: Session, bus: Bus) -> None:
    seats_to_add = []
    
    if bus.is_sleeper:
        # 30 seats: 15 Lower Deck (L1..L15) and 15 Upper Deck (U1..U15)
        # 5 rows: 1 single berth (Col 1), aisle (Col 2), 2 double berths (Col 3, Col 4)
        for deck, deck_name in [("L", "lower"), ("U", "upper")]:
            seat_num = 1
            for r in range(1, 6):
                # Front/Middle/Rear classification
                pos = "front" if r <= 2 else ("middle" if r <= 4 else "rear")
                
                # Single berth (Col 1 - Window)
                seats_to_add.append(
                    Seat(
                        bus_id=bus.id,
                        seat_number=f"{deck}{seat_num}",
                        row=r,
                        column=1,
                        seat_type="sleeper",
                        window=True,
                        aisle=False,
                        upper_lower=deck_name,
                        front_rear=pos,
                        base_price=bus.starting_price + (100 if deck_name == "lower" else 0) + (50 if pos == "front" else 0),
                        is_active=True,
                    )
                )
                seat_num += 1

                # Double berth aisle (Col 3)
                seats_to_add.append(
                    Seat(
                        bus_id=bus.id,
                        seat_number=f"{deck}{seat_num}",
                        row=r,
                        column=3,
                        seat_type="sleeper",
                        window=False,
                        aisle=True,
                        upper_lower=deck_name,
                        front_rear=pos,
                        base_price=bus.starting_price + (50 if deck_name == "lower" else 0),
                        is_active=True,
                    )
                )
                seat_num += 1

                # Double berth window (Col 4)
                seats_to_add.append(
                    Seat(
                        bus_id=bus.id,
                        seat_number=f"{deck}{seat_num}",
                        row=r,
                        column=4,
                        seat_type="sleeper",
                        window=True,
                        aisle=False,
                        upper_lower=deck_name,
                        front_rear=pos,
                        base_price=bus.starting_price + (100 if deck_name == "lower" else 0) + (50 if pos == "front" else 0),
                        is_active=True,
                    )
                )
                seat_num += 1
    else:
        # Seater / Semi-Sleeper: 8 rows of 4 seats (2+2 layout) -> 32 seats
        seat_num = 1
        for r in range(1, 9):
            pos = "front" if r <= 2 else ("middle" if r <= 6 else "rear")
            
            # Col 1: Window
            seats_to_add.append(
                Seat(
                    bus_id=bus.id,
                    seat_number=f"S{seat_num}",
                    row=r,
                    column=1,
                    seat_type="seater",
                    window=True,
                    aisle=False,
                    upper_lower="seater",
                    front_rear=pos,
                    base_price=bus.starting_price + (30 if pos == "front" else 0),
                    is_active=True,
                )
            )
            seat_num += 1

            # Col 2: Aisle
            seats_to_add.append(
                Seat(
                    bus_id=bus.id,
                    seat_number=f"S{seat_num}",
                    row=r,
                    column=2,
                    seat_type="seater",
                    window=False,
                    aisle=True,
                    upper_lower="seater",
                    front_rear=pos,
                    base_price=bus.starting_price,
                    is_active=True,
                )
            )
            seat_num += 1

            # Col 3: Aisle
            seats_to_add.append(
                Seat(
                    bus_id=bus.id,
                    seat_number=f"S{seat_num}",
                    row=r,
                    column=3,
                    seat_type="seater",
                    window=False,
                    aisle=True,
                    upper_lower="seater",
                    front_rear=pos,
                    base_price=bus.starting_price,
                    is_active=True,
                )
            )
            seat_num += 1

            # Col 4: Window
            seats_to_add.append(
                Seat(
                    bus_id=bus.id,
                    seat_number=f"S{seat_num}",
                    row=r,
                    column=4,
                    seat_type="seater",
                    window=True,
                    aisle=False,
                    upper_lower="seater",
                    front_rear=pos,
                    base_price=bus.starting_price + (30 if pos == "front" else 0),
                    is_active=True,
                )
            )
            seat_num += 1

    db.add_all(seats_to_add)
    db.commit()


def seed_sample_bookings(db: Session, buses: list, user: User, base_date: date) -> None:
    # Seed realistic bookings for 3 dates (today, tomorrow, +2 days)
    demo_passengers = [
        ("Venkatesh Rao", 34, "M"),
        ("Sunita Reddy", 30, "F"),
        ("Anil Kumar", 28, "M"),
        ("Pooja Nair", 25, "F"),
    ]

    for day_offset in range(4):
        target_date = (base_date + timedelta(days=day_offset)).strftime("%Y-%m-%d")
        for bus in buses[:4]:  # seed on first few buses
            seats = db.query(Seat).filter(Seat.bus_id == bus.id).all()
            if len(seats) < 4:
                continue

            # Pick 2-4 seats to be booked on this date
            booked_sample = seats[:2]
            booking_ref = f"ST-DEMO{day_offset}{bus.id}"
            
            existing = db.query(Booking).filter(Booking.booking_reference == booking_ref).first()
            if existing:
                continue

            total = sum(s.base_price for s in booked_sample)
            b = Booking(
                booking_reference=booking_ref,
                user_id=user.id,
                bus_id=bus.id,
                journey_date=target_date,
                boarding_point=bus.boarding_points[0] if bus.boarding_points else "Main Boarding",
                dropping_point=bus.dropping_points[0] if bus.dropping_points else "Main Dropping",
                total_amount=total,
                status="CONFIRMED",
            )
            db.add(b)
            db.flush()

            for i, s in enumerate(booked_sample):
                p_name, p_age, p_gender = demo_passengers[i % len(demo_passengers)]
                bs = BookingSeat(
                    booking_id=b.id,
                    seat_id=s.id,
                    price_paid=s.base_price,
                )
                db.add(bs)

                p = Passenger(
                    booking_id=b.id,
                    seat_id=s.id,
                    name=p_name,
                    age=p_age,
                    gender=p_gender,
                )
                db.add(p)

            pay = Payment(
                booking_id=b.id,
                amount=total,
                payment_method="MOCK_UPI",
                transaction_reference=f"TXN-DEMO-{day_offset}-{bus.id}",
                status="SUCCESS",
            )
            db.add(pay)

    db.commit()


if __name__ == "__main__":
    seed_database()
