-- =======================================================
-- SAKTHI AGRI - MYSQL WORKBENCH DATABASE SCHEMA & SEED DATA
-- Import this file into MySQL Workbench or phpMyAdmin
-- =======================================================

CREATE DATABASE IF NOT EXISTS sakthi_agri CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE sakthi_agri;

-- 1. Users Table
DROP TABLE IF EXISTS cart;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS godowns;
DROP TABLE IF EXISTS machinery;
DROP TABLE IF EXISTS shop_products;
DROP TABLE IF EXISTS crops;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    phone VARCHAR(30) NULL,
    role VARCHAR(50) NOT NULL, -- 'farmer', 'agri_shop', 'machinery', 'godown', 'buyer'
    district VARCHAR(100) NULL,
    village VARCHAR(150) NULL,
    shop_name VARCHAR(150) NULL,
    land_area DECIMAL(8, 2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. Crops Table (Uploaded by Farmers)
CREATE TABLE crops (
    id INT AUTO_INCREMENT PRIMARY KEY,
    farmer_id INT NOT NULL,
    crop_name VARCHAR(200) NOT NULL,
    crop_type VARCHAR(100) NOT NULL, -- 'Grains', 'Vegetables', 'Fruits', 'Pulses', 'Spices'
    quantity DECIMAL(10, 2) NOT NULL,
    unit VARCHAR(50) DEFAULT 'kg',
    price_per_unit DECIMAL(10, 2) NOT NULL,
    harvest_date VARCHAR(50) NULL,
    location VARCHAR(200) NULL,
    image_url TEXT NULL,
    description TEXT NULL,
    status VARCHAR(50) DEFAULT 'Available',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (farmer_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. Agri Shop Products Table
CREATE TABLE shop_products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    shop_id INT NOT NULL,
    product_name VARCHAR(200) NOT NULL,
    category VARCHAR(100) NOT NULL, -- 'Fertilizers', 'Seeds', 'Bio Fertilizers', 'Pesticides', 'Tools & Sprayers'
    price DECIMAL(10, 2) NOT NULL,
    stock INT NOT NULL DEFAULT 0,
    unit VARCHAR(50) DEFAULT 'Unit',
    image_url TEXT NULL,
    description TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (shop_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. Machinery Rentals Table
CREATE TABLE machinery (
    id INT AUTO_INCREMENT PRIMARY KEY,
    owner_id INT NOT NULL,
    machine_name VARCHAR(200) NOT NULL,
    machine_type VARCHAR(100) NOT NULL, -- 'Tractor', 'Harvester', 'Power Tiller', 'Rotavator'
    rent_rate DECIMAL(10, 2) NOT NULL,
    rate_unit VARCHAR(50) DEFAULT 'per hour',
    driver_included TINYINT(1) DEFAULT 1,
    location VARCHAR(200) NOT NULL,
    contact_phone VARCHAR(30) NULL,
    image_url TEXT NULL,
    status VARCHAR(50) DEFAULT 'Available',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. Godowns & Cold Storage Table
CREATE TABLE godowns (
    id INT AUTO_INCREMENT PRIMARY KEY,
    owner_id INT NOT NULL,
    godown_name VARCHAR(200) NOT NULL,
    godown_type VARCHAR(100) NOT NULL, -- 'Cold Storage', 'Dry Warehouse', 'Grain Silo'
    total_capacity DECIMAL(10, 2) NOT NULL,
    available_capacity DECIMAL(10, 2) NOT NULL,
    capacity_unit VARCHAR(50) DEFAULT 'Tons',
    rent_rate DECIMAL(10, 2) NOT NULL,
    rate_unit VARCHAR(50) DEFAULT 'per ton / month',
    location VARCHAR(200) NOT NULL,
    contact_phone VARCHAR(30) NULL,
    temperature_controlled TINYINT(1) DEFAULT 0,
    image_url TEXT NULL,
    status VARCHAR(50) DEFAULT 'Available',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6. Orders Table (With Farmer Accept / Reject Support)
CREATE TABLE orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_number VARCHAR(100) NOT NULL UNIQUE,
    buyer_id INT NOT NULL,
    seller_id INT NOT NULL,
    item_type VARCHAR(50) NOT NULL, -- 'crop', 'shop_product'
    item_id INT NOT NULL,
    item_name VARCHAR(200) NOT NULL,
    quantity DECIMAL(10, 2) NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    delivery_address TEXT NOT NULL,
    buyer_phone VARCHAR(30) NOT NULL,
    district VARCHAR(100) NULL,
    payment_method VARCHAR(50) DEFAULT 'Razorpay',
    payment_status VARCHAR(50) DEFAULT 'Paid',
    razorpay_order_id VARCHAR(150) NULL,
    razorpay_payment_id VARCHAR(150) NULL,
    status VARCHAR(50) DEFAULT 'Pending', -- 'Pending', 'Accepted', 'Rejected', 'Dispatched', 'Completed'
    farmer_notes TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (buyer_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (seller_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 7. Cart Table
CREATE TABLE cart (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    item_type VARCHAR(50) NOT NULL, -- 'crop', 'shop_product'
    item_id INT NOT NULL,
    quantity DECIMAL(10, 2) NOT NULL DEFAULT 1.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 8. Government Fixed Prices Table (MSP / Official Price)
CREATE TABLE government_prices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    crop_name VARCHAR(150) NOT NULL UNIQUE,
    crop_type VARCHAR(100) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    unit VARCHAR(50) DEFAULT 'kg',
    msp_year VARCHAR(50) DEFAULT '2026-27',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO government_prices (crop_name, crop_type, price, unit, msp_year)
VALUES
('Ponni Paddy (Rice)', 'Grains', 1450.00, 'Bags', '2026-27'),
('Paddy (Common / Sona Masoori)', 'Grains', 29.00, 'kg', '2026-27'),
('Country Tomatoes (Thakkali)', 'Vegetables', 28.00, 'kg', '2026-27'),
('Organic Small Onion (Chinna Vengayam)', 'Vegetables', 46.00, 'kg', '2026-27'),
('Nendran Green Banana', 'Fruits', 320.00, 'Bunches', '2026-27'),
('Organic Red Chilli (Guntur Sanam)', 'Spices', 185.00, 'kg', '2026-27'),
('Turmeric (Manjal)', 'Spices', 95.00, 'kg', '2026-27'),
('Cotton (Kapas)', 'Cash Crops', 72.00, 'kg', '2026-27'),
('Black Gram (Urad Dal)', 'Pulses', 74.00, 'kg', '2026-27'),
('Groundnut (Kadalai)', 'Oilseeds', 68.00, 'kg', '2026-27'),
('Maize (Makka Cholam)', 'Grains', 24.00, 'kg', '2026-27'),
('Sugarcane (Karumbu)', 'Cash Crops', 32.00, 'kg', '2026-27'),
('Wheat (Godhumai)', 'Grains', 25.00, 'kg', '2026-27'),
('Green Gram (Moong Dal)', 'Pulses', 86.00, 'kg', '2026-27'),
('Potato (Urulaikilangu)', 'Vegetables', 26.00, 'kg', '2026-27'),
('Carrot', 'Vegetables', 38.00, 'kg', '2026-27');

-- =======================================================
-- SEED DATA (Pre-populates Farmers, Agri Shops & Listings)
-- Passwords: password123
-- =======================================================

-- 1. Insert Users
INSERT INTO users (id, name, email, password, phone, role, district, village, shop_name, land_area, created_at)
VALUES 
(1, 'DHARANI', '24339@krcollege.net', 'scrypt:32768:8:1$m9bXzR7oB2aY1Qp$0ec494a8523c91db0dd70742d4a25997dbeab1264c185121e7d0134b22c7ebbe', '7305371131', 'farmer', 'thenkasi', 'Vilathikulam', NULL, 5.00, '2026-10-06 21:40:00'),
(2, 'Naresh', 'naresh1234@gmail.com', 'scrypt:32768:8:1$m9bXzR7oB2aY1Qp$0ec494a8523c91db0dd70742d4a25997dbeab1264c185121e7d0134b22c7ebbe', '7305371131', 'agri_shop', 'thenkasi', NULL, 'Naresh agri shop', 0.00, '2026-09-30 02:20:00'),
(3, 'Senthil Kumar', 'machinery@sakthi.com', 'scrypt:32768:8:1$m9bXzR7oB2aY1Qp$0ec494a8523c91db0dd70742d4a25997dbeab1264c185121e7d0134b22c7ebbe', '9876543210', 'machinery', 'thenkasi', NULL, 'Senthil Farm Equipments', 0.00, '2026-10-01 10:00:00'),
(4, 'Muthu Vel', 'godown@sakthi.com', 'scrypt:32768:8:1$m9bXzR7oB2aY1Qp$0ec494a8523c91db0dd70742d4a25997dbeab1264c185121e7d0134b22c7ebbe', '9842112345', 'godown', 'thenkasi', NULL, 'Vilathikulam Agro Storage', 0.00, '2026-10-01 11:00:00'),
(5, 'Anand Traders', 'buyer@sakthi.com', 'scrypt:32768:8:1$m9bXzR7oB2aY1Qp$0ec494a8523c91db0dd70742d4a25997dbeab1264c185121e7d0134b22c7ebbe', '9443215678', 'buyer', 'madurai', 'Madurai Central Market', NULL, 0.00, '2026-10-02 09:30:00');

-- 2. Insert Farmer Dharani's Crops
INSERT INTO crops (farmer_id, crop_name, crop_type, quantity, unit, price_per_unit, harvest_date, location, image_url, description, status)
VALUES
(1, 'Ponni Paddy (Rice)', 'Grains', 50.00, 'Bags', 1450.00, '2026-10-25', 'Vilathikulam, thenkasi', 'https://images.unsplash.com/photo-1586201375761-83865001e31c?w=600', 'Freshly harvested premier Ponni raw paddy direct from farm field.', 'Available'),
(1, 'Country Tomatoes (Thakkali)', 'Vegetables', 400.00, 'kg', 28.00, '2026-10-15', 'Vilathikulam, thenkasi', 'https://images.unsplash.com/photo-1592924357228-91a4daadcfea?w=600', 'High quality juicy organic country tomatoes ready for market.', 'Available'),
(1, 'Organic Small Onion (Chinna Vengayam)', 'Vegetables', 250.00, 'kg', 46.00, '2026-10-18', 'Vilathikulam, thenkasi', 'https://images.unsplash.com/photo-1618512496248-a07fe83aa8cb?w=600', 'Authentic pungent Tenkasi small sambar onions sun-dried.', 'Available'),
(1, 'Nendran Green Banana', 'Fruits', 60.00, 'Bunches', 320.00, '2026-10-22', 'Vilathikulam, thenkasi', 'https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?w=600', 'Large healthy Kerala Nendran banana bunches organically grown.', 'Available'),
(1, 'Organic Red Chilli (Guntur Sanam)', 'Spices', 150.00, 'kg', 185.00, '2026-10-10', 'Vilathikulam, thenkasi', 'https://images.unsplash.com/photo-1588252303782-cb80119abd6d?w=600', 'Deep red spicy sun-cured dry chillies with rich aroma.', 'Available');

-- 3. Insert Naresh Agri Shop Products
INSERT INTO shop_products (shop_id, product_name, category, price, stock, unit, image_url, description)
VALUES
(2, 'IFFCO Neem Coated Urea 45kg', 'Fertilizers', 267.00, 120, 'Bag', 'https://images.unsplash.com/photo-1628352081506-83c43123ed6d?w=600', 'Subsidized premier quality agricultural nitrogen fertilizer for all crops.'),
(2, 'DAP Fertilizer 50kg (Di-Ammonium Phosphate)', 'Fertilizers', 1350.00, 65, 'Bag', 'https://images.unsplash.com/photo-1585314062340-f1a5a7c9328d?w=600', 'Essential basal fertilizer rich in Phosphorus and Nitrogen.'),
(2, 'Certified CR 1009 Sub 1 Paddy Seeds 10kg', 'Seeds', 680.00, 40, 'Packet', 'https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?w=600', 'Flood tolerant high yield certified paddy seeds for Samba season.'),
(2, 'Pure Cold Pressed Neem Oil Bio-Pesticide 1L', 'Bio Fertilizers', 380.00, 75, 'Bottle', 'https://images.unsplash.com/photo-1608571423902-eed4a5ad8108?w=600', 'Organic repellent against whiteflies, aphids, mites and bollworms.'),
(2, 'Agrimate 16L 12V Battery Knapsack Sprayer', 'Tools & Sprayers', 2350.00, 18, 'Unit', 'https://images.unsplash.com/photo-1590682680695-43b964a3ae17?w=600', 'Heavy duty double motor sprayer with brass telescopic lance and nozzle kit.');

-- 4. Insert Machinery Rentals
INSERT INTO machinery (owner_id, machine_name, machine_type, rent_rate, rate_unit, driver_included, location, contact_phone, image_url, status)
VALUES
(3, 'Mahindra 575 DI Tractor (45 HP) with Rotavator', 'Tractor', 850.00, 'per hour', 1, 'Vilathikulam, thenkasi', '9876543210', 'https://images.unsplash.com/photo-1592878904946-b3cd8ae243d0?w=600', 'Available'),
(3, 'Kubota DC-68G Track Combine Harvester', 'Harvester', 2400.00, 'per hour', 1, 'Thenkasi Highway', '9876543210', 'https://images.unsplash.com/photo-1544161515-4ab6ce6db874?w=600', 'Available'),
(3, 'VST Shakti 130 DI Power Tiller (13 HP)', 'Power Tiller', 480.00, 'per hour', 1, 'Vilathikulam', '9876543210', 'https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=600', 'Available');

-- 5. Insert Godowns
INSERT INTO godowns (owner_id, godown_name, godown_type, total_capacity, available_capacity, capacity_unit, rent_rate, rate_unit, location, contact_phone, temperature_controlled, image_url, status)
VALUES
(4, 'Sakthi Modern Cold Storage Warehouse', 'Cold Storage', 600.00, 420.00, 'Tons', 140.00, 'per ton / month', 'Vilathikulam Main Road, thenkasi', '9842112345', 1, 'https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?w=600', 'Available'),
(4, 'Vilathikulam Central Grain Godown', 'Dry Warehouse', 1200.00, 850.00, 'Tons', 85.00, 'per ton / month', 'Vilathikulam, thenkasi', '9842112345', 0, 'https://images.unsplash.com/photo-1553413077-190dd305871c?w=600', 'Available');

-- 6. Insert Sample Orders
INSERT INTO orders (order_number, buyer_id, seller_id, item_type, item_id, item_name, quantity, unit_price, total_amount, delivery_address, buyer_phone, district, payment_method, payment_status, razorpay_order_id, razorpay_payment_id, status, farmer_notes, created_at)
VALUES
('ORD-20261009-001', 5, 1, 'crop', 2, 'Country Tomatoes (Thakkali)', 100.00, 28.00, 2800.00, 'Shop #14, Gandhi Wholesale Market, Madurai', '9443215678', 'madurai', 'Razorpay', 'Paid', 'order_Rz99812A', 'pay_871629831', 'Pending', 'Please dispatch early morning harvest.', '2026-10-09 18:20:00'),
('ORD-20261008-002', 5, 1, 'crop', 1, 'Ponni Paddy (Rice)', 20.00, 1450.00, 29000.00, 'Madurai Central Rice Mill Road', '9443215678', 'madurai', 'Razorpay', 'Paid', 'order_Rz77123B', 'pay_662514820', 'Accepted', 'Vehicle arriving on Saturday morning.', '2026-10-08 14:10:00');
