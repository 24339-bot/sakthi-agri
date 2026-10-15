import sqlite3
import os
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), 'sakthi_agri.db')

def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.isolation_level = None
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            phone TEXT,
            role TEXT NOT NULL,
            district TEXT,
            village TEXT,
            shop_name TEXT,
            land_area REAL DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Crops Table (Uploaded by Farmers)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS crops (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            farmer_id INTEGER NOT NULL,
            crop_name TEXT NOT NULL,
            crop_type TEXT NOT NULL,
            quantity REAL NOT NULL,
            unit TEXT DEFAULT 'kg',
            price_per_unit REAL NOT NULL,
            harvest_date TEXT,
            location TEXT,
            image_url TEXT,
            description TEXT,
            status TEXT DEFAULT 'Available',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (farmer_id) REFERENCES users (id)
        )
    ''')

    # Agri Shop Products Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS shop_products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shop_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER NOT NULL,
            unit TEXT DEFAULT 'Unit',
            image_url TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (shop_id) REFERENCES users (id)
        )
    ''')

    # Machinery Rental Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS machinery (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER NOT NULL,
            machine_name TEXT NOT NULL,
            machine_type TEXT NOT NULL,
            rent_rate REAL NOT NULL,
            rate_unit TEXT DEFAULT 'per hour',
            driver_included INTEGER DEFAULT 1,
            location TEXT NOT NULL,
            contact_phone TEXT,
            image_url TEXT,
            status TEXT DEFAULT 'Available',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (owner_id) REFERENCES users (id)
        )
    ''')

    # Godowns / Warehouse Storage Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS godowns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER NOT NULL,
            godown_name TEXT NOT NULL,
            godown_type TEXT NOT NULL,
            total_capacity REAL NOT NULL,
            available_capacity REAL NOT NULL,
            capacity_unit TEXT DEFAULT 'Tons',
            rent_rate REAL NOT NULL,
            rate_unit TEXT DEFAULT 'per ton / month',
            location TEXT NOT NULL,
            contact_phone TEXT,
            temperature_controlled INTEGER DEFAULT 0,
            image_url TEXT,
            status TEXT DEFAULT 'Available',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (owner_id) REFERENCES users (id)
        )
    ''')

    # Orders Table (Farmer crop orders, shop product orders, rentals)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number TEXT UNIQUE NOT NULL,
            buyer_id INTEGER NOT NULL,
            seller_id INTEGER NOT NULL,
            item_type TEXT NOT NULL,
            item_id INTEGER NOT NULL,
            item_name TEXT NOT NULL,
            quantity REAL NOT NULL,
            unit_price REAL NOT NULL,
            total_amount REAL NOT NULL,
            delivery_address TEXT NOT NULL,
            buyer_phone TEXT NOT NULL,
            district TEXT,
            payment_method TEXT DEFAULT 'Razorpay',
            payment_status TEXT DEFAULT 'Paid',
            razorpay_order_id TEXT,
            razorpay_payment_id TEXT,
            status TEXT DEFAULT 'Pending',
            farmer_notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (buyer_id) REFERENCES users (id),
            FOREIGN KEY (seller_id) REFERENCES users (id)
        )
    ''')

    # Cart Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            item_type TEXT NOT NULL,
            item_id INTEGER NOT NULL,
            quantity REAL NOT NULL DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Government Fixed Prices Table (MSP / Official Regulated Price)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS government_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            crop_name TEXT NOT NULL UNIQUE,
            crop_type TEXT NOT NULL,
            price REAL NOT NULL,
            unit TEXT DEFAULT 'kg',
            msp_year TEXT DEFAULT '2026-27',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()

    # Check if government prices exist, if not seed them
    cursor.execute("SELECT COUNT(*) FROM government_prices")
    gov_count = cursor.fetchone()[0]
    if gov_count == 0:
        seed_government_prices(conn)

    # Check if seed data exists
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]

    if count == 0:
        seed_data(conn)

    conn.close()

def seed_government_prices(conn):
    cursor = conn.cursor()
    gov_prices = [
        ('Ponni Paddy (Rice)', 'Grains', 1450.0, 'Bags', '2026-27'),
        ('Paddy (Common / Sona Masoori)', 'Grains', 29.0, 'kg', '2026-27'),
        ('Country Tomatoes (Thakkali)', 'Vegetables', 28.0, 'kg', '2026-27'),
        ('Organic Small Onion (Chinna Vengayam)', 'Vegetables', 46.0, 'kg', '2026-27'),
        ('Nendran Green Banana', 'Fruits', 320.0, 'Bunches', '2026-27'),
        ('Organic Red Chilli (Guntur Sanam)', 'Spices', 185.0, 'kg', '2026-27'),
        ('Turmeric (Manjal)', 'Spices', 95.0, 'kg', '2026-27'),
        ('Cotton (Kapas)', 'Cash Crops', 72.0, 'kg', '2026-27'),
        ('Black Gram (Urad Dal)', 'Pulses', 74.0, 'kg', '2026-27'),
        ('Groundnut (Kadalai)', 'Oilseeds', 68.0, 'kg', '2026-27'),
        ('Maize (Makka Cholam)', 'Grains', 24.0, 'kg', '2026-27'),
        ('Sugarcane (Karumbu)', 'Cash Crops', 32.0, 'kg', '2026-27'),
        ('Wheat (Godhumai)', 'Grains', 25.0, 'kg', '2026-27'),
        ('Green Gram (Moong Dal)', 'Pulses', 86.0, 'kg', '2026-27'),
        ('Potato (Urulaikilangu)', 'Vegetables', 26.0, 'kg', '2026-27'),
        ('Carrot', 'Vegetables', 38.0, 'kg', '2026-27')
    ]
    cursor.executemany('''
        INSERT OR IGNORE INTO government_prices (crop_name, crop_type, price, unit, msp_year)
        VALUES (?, ?, ?, ?, ?)
    ''', gov_prices)
    conn.commit()

def seed_data(conn):
    cursor = conn.cursor()
    password_hash = generate_password_hash('password123')

    # 1. Farmer Dharani (from screenshot)
    cursor.execute('''
        INSERT INTO users (name, email, password, phone, role, district, village, land_area, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', ('DHARANI', '24339@krcollege.net', password_hash, '7305371131', 'farmer', 'thenkasi', 'Vilathikulam', 5.00, '2026-10-06 21:40:00'))
    farmer_id = cursor.lastrowid

    # 2. Agri Shop Naresh (from screenshot)
    cursor.execute('''
        INSERT INTO users (name, email, password, phone, role, district, shop_name, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', ('Naresh', 'naresh1234@gmail.com', password_hash, '7305371131', 'agri_shop', 'thenkasi', 'Naresh agri shop', '2026-09-30 02:20:00'))
    shop_id = cursor.lastrowid

    # 3. Machinery Owner Senthil
    cursor.execute('''
        INSERT INTO users (name, email, password, phone, role, district, shop_name, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', ('Senthil Kumar', 'machinery@sakthi.com', password_hash, '9876543210', 'machinery', 'thenkasi', 'Senthil Farm Equipments', '2026-10-01 10:00:00'))
    machinery_id = cursor.lastrowid

    # 4. Godown Owner Muthu Vel
    cursor.execute('''
        INSERT INTO users (name, email, password, phone, role, district, shop_name, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', ('Muthu Vel', 'godown@sakthi.com', password_hash, '9842112345', 'godown', 'thenkasi', 'Vilathikulam Agro Storage', '2026-10-01 11:00:00'))
    godown_id = cursor.lastrowid

    # 5. Buyer Anand Traders
    cursor.execute('''
        INSERT INTO users (name, email, password, phone, role, district, village, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', ('Anand Traders', 'buyer@sakthi.com', password_hash, '9443215678', 'buyer', 'madurai', 'Madurai Central Market', '2026-10-02 09:30:00'))
    buyer_id = cursor.lastrowid

    # Seed Dharani's Crops
    crops = [
        (farmer_id, 'Ponni Paddy (Rice)', 'Grains', 50.0, 'Bags', 1450.0, '2026-10-25', 'Vilathikulam, thenkasi', 'https://images.unsplash.com/photo-1586201375761-83865001e31c?w=600&auto=format&fit=crop&q=60', 'Freshly harvested premier Ponni raw paddy direct from farm field.', 'Available'),
        (farmer_id, 'Country Tomatoes (Thakkali)', 'Vegetables', 400.0, 'kg', 28.0, '2026-10-15', 'Vilathikulam, thenkasi', 'https://images.unsplash.com/photo-1592924357228-91a4daadcfea?w=600&auto=format&fit=crop&q=60', 'High quality juicy organic country tomatoes ready for market.', 'Available'),
        (farmer_id, 'Organic Small Onion (Chinna Vengayam)', 'Vegetables', 250.0, 'kg', 46.0, '2026-10-18', 'Vilathikulam, thenkasi', 'https://images.unsplash.com/photo-1618512496248-a07fe83aa8cb?w=600&auto=format&fit=crop&q=60', 'Authentic pungent Tenkasi small sambar onions sun-dried.', 'Available'),
        (farmer_id, 'Nendran Green Banana', 'Fruits', 60.0, 'Bunches', 320.0, '2026-10-22', 'Vilathikulam, thenkasi', 'https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?w=600&auto=format&fit=crop&q=60', 'Large healthy Kerala Nendran banana bunches organically grown.', 'Available'),
        (farmer_id, 'Organic Red Chilli (Guntur Sanam)', 'Spices', 150.0, 'kg', 185.0, '2026-10-10', 'Vilathikulam, thenkasi', 'https://images.unsplash.com/photo-1588252303782-cb80119abd6d?w=600&auto=format&fit=crop&q=60', 'Deep red spicy sun-cured dry chillies with rich aroma.', 'Available')
    ]
    cursor.executemany('''
        INSERT INTO crops (farmer_id, crop_name, crop_type, quantity, unit, price_per_unit, harvest_date, location, image_url, description, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', crops)
    crop1_id = cursor.lastrowid - 4
    crop2_id = cursor.lastrowid - 3

    # Seed Naresh Agri Shop Products
    products = [
        (shop_id, 'IFFCO Neem Coated Urea 45kg', 'Fertilizers', 267.0, 120, 'Bag', 'https://images.unsplash.com/photo-1628352081506-83c43123ed6d?w=600&auto=format&fit=crop&q=60', 'Subsidized premier quality agricultural nitrogen fertilizer for all crops.'),
        (shop_id, 'DAP Fertilizer 50kg (Di-Ammonium Phosphate)', 'Fertilizers', 1350.0, 65, 'Bag', 'https://images.unsplash.com/photo-1585314062340-f1a5a7c9328d?w=600&auto=format&fit=crop&q=60', 'Essential basal fertilizer rich in Phosphorus and Nitrogen.'),
        (shop_id, 'Certified CR 1009 Sub 1 Paddy Seeds 10kg', 'Seeds', 680.0, 40, 'Packet', 'https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?w=600&auto=format&fit=crop&q=60', 'Flood tolerant high yield certified paddy seeds for Samba season.'),
        (shop_id, 'Pure Cold Pressed Neem Oil Bio-Pesticide 1L', 'Bio Fertilizers', 380.0, 75, 'Bottle', 'https://images.unsplash.com/photo-1608571423902-eed4a5ad8108?w=600&auto=format&fit=crop&q=60', 'Organic repellent against whiteflies, aphids, mites and bollworms.'),
        (shop_id, 'Agrimate 16L 12V Battery Knapsack Sprayer', 'Tools & Sprayers', 2350.0, 18, 'Unit', 'https://images.unsplash.com/photo-1590682680695-43b964a3ae17?w=600&auto=format&fit=crop&q=60', 'Heavy duty double motor sprayer with brass telescopic lance and nozzle kit.')
    ]
    cursor.executemany('''
        INSERT INTO shop_products (shop_id, product_name, category, price, stock, unit, image_url, description)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', products)

    # Seed Machinery Rentals
    machineries = [
        (machinery_id, 'Mahindra 575 DI Tractor (45 HP) with Rotavator', 'Tractor', 850.0, 'per hour', 1, 'Vilathikulam, thenkasi', '9876543210', 'https://images.unsplash.com/photo-1592878904946-b3cd8ae243d0?w=600&auto=format&fit=crop&q=60', 'Available'),
        (machinery_id, 'Kubota DC-68G Track Combine Harvester', 'Harvester', 2400.0, 'per hour', 1, 'Thenkasi Highway', '9876543210', 'https://images.unsplash.com/photo-1544161515-4ab6ce6db874?w=600&auto=format&fit=crop&q=60', 'Available'),
        (machinery_id, 'VST Shakti 130 DI Power Tiller (13 HP)', 'Power Tiller', 480.0, 'per hour', 1, 'Vilathikulam', '9876543210', 'https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=600&auto=format&fit=crop&q=60', 'Available')
    ]
    cursor.executemany('''
        INSERT INTO machinery (owner_id, machine_name, machine_type, rent_rate, rate_unit, driver_included, location, contact_phone, image_url, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', machineries)

    # Seed Godowns
    godowns = [
        (godown_id, 'Sakthi Modern Cold Storage Warehouse', 'Cold Storage', 600.0, 420.0, 'Tons', 140.0, 'per ton / month', 'Vilathikulam Main Road, thenkasi', '9842112345', 1, 'https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?w=600&auto=format&fit=crop&q=60', 'Available'),
        (godown_id, 'Vilathikulam Central Grain Godown', 'Dry Warehouse', 1200.0, 850.0, 'Tons', 85.0, 'per ton / month', 'Vilathikulam, thenkasi', '9842112345', 0, 'https://images.unsplash.com/photo-1553413077-190dd305871c?w=600&auto=format&fit=crop&q=60', 'Available')
    ]
    cursor.executemany('''
        INSERT INTO godowns (owner_id, godown_name, godown_type, total_capacity, available_capacity, capacity_unit, rent_rate, rate_unit, location, contact_phone, temperature_controlled, image_url, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', godowns)

    # Seed Sample Orders for Dharani to showcase Accept/Reject and tracking!
    orders = [
        ('ORD-20261009-001', buyer_id, farmer_id, 'crop', crop2_id, 'Country Tomatoes (Thakkali)', 100.0, 28.0, 2800.0, 'Shop #14, Gandhi Wholesale Market, Madurai', '9443215678', 'madurai', 'Razorpay', 'Paid', 'order_Rz99812A', 'pay_871629831', 'Pending', 'Please dispatch early morning harvest.', '2026-10-09 18:20:00'),
        ('ORD-20261008-002', buyer_id, farmer_id, 'crop', crop1_id, 'Ponni Paddy (Rice)', 20.0, 1450.0, 29000.0, 'Madurai Central Rice Mill Road', '9443215678', 'madurai', 'Razorpay', 'Paid', 'order_Rz77123B', 'pay_662514820', 'Accepted', 'Vehicle arriving on Saturday morning.', '2026-10-08 14:10:00')
    ]
    cursor.executemany('''
        INSERT INTO orders (order_number, buyer_id, seller_id, item_type, item_id, item_name, quantity, unit_price, total_amount, delivery_address, buyer_phone, district, payment_method, payment_status, razorpay_order_id, razorpay_payment_id, status, farmer_notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', orders)

    conn.commit()

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully!")
