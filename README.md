# 🌱 Sakthi Agri - Complete Agricultural Ecosystem

Welcome to the **Sakthi Agri Platform** codebase! Built with Python Flask, MySQL Workbench / SQLite support, and Razorpay payment integration, designed to match the Sakthi Agri dashboard screenshots.

---

## 💻 1. Vera System-ku Copy Pannuvathu Epty? (How to Transfer to Another System)

Neenga intha `sakthi_agri` folder-ai **apdiye copy panni entha system-ku venalum potukalam**, vera path (e.g. `Desktop\sakthi_agri`, `D:\projects\sakthi_agri` or Pen Drive)-la vachukalam. Athu 100% work aagum!

### Simple Steps on New System:
1. Copy the whole `sakthi_agri` folder to your desired location (e.g., `C:\Users\YourName\Desktop\sakthi_agri`).
2. Open Terminal / PowerShell inside that folder:
   ```powershell
   cd path\to\sakthi_agri
   ```
3. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
4. Start the server:
   ```powershell
   python app.py
   ```
5. Open browser:
   👉 **`http://127.0.0.1:5000`**

---

## 🗄️ 2. MySQL Workbench-la Database Poduvathu Epty? (Using MySQL Workbench)

Default-ah project-la zero-configuration **SQLite** database irukku. 
Neenga **MySQL Workbench** use panna virumbinaal, ready-made SQL script ready-ah irukku!

### Steps in MySQL Workbench:
1. Open **MySQL Workbench** and connect to your local MySQL server.
2. Go to **File ➔ Open SQL Script...**
3. Select `sakthi_agri_schema.sql` inside the project folder.
4. Click the **Execute (⚡ Lightning Bolt)** button.
   - Idhu `sakthi_agri` database create pannum.
   - All tables: `users`, `crops`, `shop_products`, `machinery`, `godowns`, `orders`, `cart` create aagum.
   - Dharani, Naresh, and sample listings data insert aagidum!
5. In Python, install MySQL connector:
   ```bash
   pip install mysql-connector-python
   ```
6. Check `database_mysql.py` to enter your MySQL Workbench root password.

---

## 🔐 3. User Logins

Demo login section has been removed from the login page! Standard secure login is active.

### Pre-registered Accounts (Password: `password123`):
* **👨‍🌾 Farmer**: `24339@krcollege.net` (DHARANI - Vilathikulam, thenkasi)
* **🏪 Agri Shop**: `naresh1234@gmail.com` (Naresh - Thenkasi)
* **🛒 Buyer**: `buyer@sakthi.com` (Anand Traders)
* **🚜 Machinery**: `machinery@sakthi.com` (Senthil Kumar)
* **🏢 Godown**: `godown@sakthi.com` (Muthu Vel)

---

## 🌟 Key Application Features

1. **👨‍🌾 Farmer Dashboard (`/farmer_dashboard`)**:
   - Header profile with Dharani's avatar, location, phone, and email.
   - 4 Metric Stat Cards (Land Area, Crops Listed, Available, Sold Out).
   - "My Crops" table with Add Crop, Edit, Delete, and Status toggle.
   - Nearby Agri Shops, Nearby Machinery, and Nearby Godowns cards.
   - **Incoming Orders (`/farmer/orders`)**: Direct **Accept** and **Reject** buttons for buyer crop orders!

2. **🏪 Agri Shop Dashboard (`/agri_shop_dashboard`)**:
   - Total Products, Total Orders, Stock Available, Revenue (₹).
   - Add Product, View Products, Manage Stock with restock controls.

3. **👤 Profile Page (`/profile`)**:
   - User card with role badge.
   - Edit Profile form with "Cannot change" email/role badges.
   - Change Password form.

4. **🛒 Buyer Produce Marketplace (`/marketplace`)**:
   - Agri eCommerce store with categories & search.
   - Add to Cart, Instant Checkout with Razorpay payment.
   - **Live Order Tracking (`/track/<order_number>`)** 4-step progress timeline.
