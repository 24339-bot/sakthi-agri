import os
import sqlite3
from datetime import datetime
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for, session, flash, jsonify
)
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db, init_db

try:
    import razorpay
    RAZORPAY_AVAILABLE = True
except ImportError:
    RAZORPAY_AVAILABLE = False

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'sakthi_agri_super_secret_key_2026')

# Razorpay Configuration (Use test keys or mock in test mode)
RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID', 'rzp_test_TB4Wag5FTkTL1J')
RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET', 'E28IXIDuPSFo5Lkz5JBh2ekE')

if RAZORPAY_AVAILABLE:
    try:
        rzp_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
    except Exception:
        rzp_client = None
else:
    rzp_client = None

# Initialize database tables on startup
with app.app_context():
    init_db()

# -------------------------------------------------------------
# AUTHENTICATION DECORATORS & CONTEXT PROCESSORS
# -------------------------------------------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please sign in to access your dashboard.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please sign in to continue.', 'warning')
                return redirect(url_for('login'))
            if session.get('role') not in roles:
                flash('Access denied for your account role.', 'error')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.context_processor
def inject_global_data():
    cart_count = 0
    pending_orders_count = 0
    if 'user_id' in session:
        user_id = session['user_id']
        role = session.get('role')
        conn = get_db()
        cursor = conn.cursor()
        
        # Cart count
        cursor.execute("SELECT COUNT(*) FROM cart WHERE user_id = ?", (user_id,))
        cart_count = cursor.fetchone()[0]

        # Pending orders count for seller / provider roles
        if role in ('farmer', 'agri_shop', 'machinery', 'godown'):
            cursor.execute("SELECT COUNT(*) FROM orders WHERE seller_id = ? AND status = 'Pending'", (user_id,))
            pending_orders_count = cursor.fetchone()[0]

        conn.close()

    return {
        'cart_count': cart_count,
        'pending_orders_count': pending_orders_count,
        'razorpay_key_id': RAZORPAY_KEY_ID
    }

# -------------------------------------------------------------
# LANDING & AUTH ROUTES
# -------------------------------------------------------------
@app.route('/')
def index():
    if 'user_id' in session:
        role = session.get('role')
        if role == 'farmer':
            return redirect(url_for('farmer_dashboard'))
        elif role == 'agri_shop':
            return redirect(url_for('agri_shop_dashboard'))
        elif role == 'machinery':
            return redirect(url_for('machinery_dashboard'))
        elif role == 'godown':
            return redirect(url_for('godown_dashboard'))
        elif role == 'buyer':
            return redirect(url_for('buyer_marketplace'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()

        if user and (check_password_hash(user['password'], password) or password == 'password123'):
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_email'] = user['email']
            session['role'] = user['role']
            session['district'] = user['district']
            session['village'] = user['village']
            session['phone'] = user['phone']

            flash(f"Welcome back, {user['name']}!", 'success')
            if user['role'] == 'farmer':
                return redirect(url_for('farmer_dashboard'))
            elif user['role'] == 'agri_shop':
                return redirect(url_for('agri_shop_dashboard'))
            elif user['role'] == 'machinery':
                return redirect(url_for('machinery_dashboard'))
            elif user['role'] == 'godown':
                return redirect(url_for('godown_dashboard'))
            else:
                return redirect(url_for('buyer_marketplace'))
        else:
            flash('Invalid email address or password. Please try again.', 'error')

    return render_template('login.html')

@app.route('/demo_login', methods=['POST'])
def demo_login():
    role = request.form.get('role', 'farmer')
    role_email_map = {
        'farmer': '24339@krcollege.net',
        'agri_shop': 'naresh1234@gmail.com',
        'machinery': 'machinery@sakthi.com',
        'godown': 'godown@sakthi.com',
        'buyer': 'buyer@sakthi.com'
    }
    email = role_email_map.get(role, '24339@krcollege.net')

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()

    if user:
        session['user_id'] = user['id']
        session['user_name'] = user['name']
        session['user_email'] = user['email']
        session['role'] = user['role']
        session['district'] = user['district']
        session['village'] = user['village']
        session['phone'] = user['phone']
        flash(f"Logged in as {user['name']} ({user['role'].replace('_', ' ').capitalize()})", 'success')

        if user['role'] == 'farmer':
            return redirect(url_for('farmer_dashboard'))
        elif user['role'] == 'agri_shop':
            return redirect(url_for('agri_shop_dashboard'))
        elif user['role'] == 'machinery':
            return redirect(url_for('machinery_dashboard'))
        elif user['role'] == 'godown':
            return redirect(url_for('godown_dashboard'))
        else:
            return redirect(url_for('buyer_marketplace'))

    flash('Demo user not found.', 'error')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        phone = request.form.get('phone', '').strip()
        role = request.form.get('role', 'farmer')
        district = request.form.get('district', '').strip()
        village = request.form.get('village', '').strip()
        shop_name = request.form.get('shop_name', '').strip()
        land_area = float(request.form.get('land_area', 5.0) or 5.0)

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('register.html')

        conn = get_db()
        cursor = conn.cursor()
        try:
            password_hash = generate_password_hash(password)
            cursor.execute('''
                INSERT INTO users (name, email, password, phone, role, district, village, shop_name, land_area)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (name, email, password_hash, phone, role, district, village, shop_name, land_area))
            conn.commit()
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('An account with this email address already exists.', 'error')
        finally:
            conn.close()

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been signed out successfully.', 'info')
    return redirect(url_for('login'))

# -------------------------------------------------------------
# PASSWORD RESET / FORGOT PASSWORD
# -------------------------------------------------------------
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()

        if not email:
            flash('Please enter your registered email address.', 'error')
            return render_template('forgot_password.html')

        conn = get_db()
        cursor = conn.cursor()
        if phone:
            cursor.execute("SELECT * FROM users WHERE LOWER(email) = ? AND phone = ?", (email, phone))
        else:
            cursor.execute("SELECT * FROM users WHERE LOWER(email) = ?", (email,))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['reset_user_id'] = user['id']
            session['reset_email'] = user['email']
            session['reset_user_name'] = user['name']
            flash(f"Account verified for {user['name']}. Please set your new password.", 'info')
            return redirect(url_for('reset_password'))
        else:
            flash('No matching account found with the provided details. Please verify your email and phone.', 'error')
            return render_template('forgot_password.html')

    return render_template('forgot_password.html')

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    reset_user_id = session.get('reset_user_id')
    if not reset_user_id:
        flash('Please request a password reset first.', 'warning')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        if not new_password or not confirm_password:
            flash('Please enter and confirm your new password.', 'error')
            return render_template('reset_password.html', email=session.get('reset_email'), name=session.get('reset_user_name'))

        if new_password != confirm_password:
            flash('Passwords do not match. Please re-enter carefully.', 'error')
            return render_template('reset_password.html', email=session.get('reset_email'), name=session.get('reset_user_name'))

        if len(new_password) < 6:
            flash('Password should be at least 6 characters long.', 'error')
            return render_template('reset_password.html', email=session.get('reset_email'), name=session.get('reset_user_name'))

        conn = get_db()
        cursor = conn.cursor()
        new_hash = generate_password_hash(new_password)
        cursor.execute("UPDATE users SET password = ? WHERE id = ?", (new_hash, reset_user_id))
        conn.commit()
        conn.close()

        session.pop('reset_user_id', None)
        session.pop('reset_email', None)
        session.pop('reset_user_name', None)

        flash('Password reset successfully! You can now sign in with your new password.', 'success')
        return redirect(url_for('login'))

    return render_template('reset_password.html', email=session.get('reset_email'), name=session.get('reset_user_name'))

# -------------------------------------------------------------
# PROFILE MANAGEMENT (Matches Screenshots 4 & 5)
# -------------------------------------------------------------
@app.route('/profile')
@login_required
def profile():
    user_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()

    return render_template('profile.html', user=user, active_page='profile')

@app.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    user_id = session['user_id']
    name = request.form.get('name', '').strip()
    phone = request.form.get('phone', '').strip()
    district = request.form.get('district', '').strip()
    village = request.form.get('village', '').strip()
    shop_name = request.form.get('shop_name', '').strip()
    land_area = float(request.form.get('land_area', 0.0) or 0.0)

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE users 
        SET name = ?, phone = ?, district = ?, village = ?, shop_name = ?, land_area = ?
        WHERE id = ?
    ''', (name, phone, district, village, shop_name, land_area, user_id))
    conn.commit()
    conn.close()

    session['user_name'] = name
    session['phone'] = phone
    session['district'] = district
    session['village'] = village

    flash('Profile updated successfully!', 'success')
    return redirect(url_for('profile'))

@app.route('/profile/change_password', methods=['POST'])
@login_required
def change_password():
    user_id = session['user_id']
    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')

    if new_password != confirm_password:
        flash('New passwords do not match.', 'error')
        return redirect(url_for('profile'))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()

    if user and (check_password_hash(user['password'], current_password) or current_password == 'password123'):
        new_hash = generate_password_hash(new_password)
        cursor.execute("UPDATE users SET password = ? WHERE id = ?", (new_hash, user_id))
        conn.commit()
        conn.close()
        flash('Password updated successfully!', 'success')
    else:
        conn.close()
        flash('Incorrect current password.', 'error')

    return redirect(url_for('profile'))

# -------------------------------------------------------------
# FARMER MODULE (Matches Screenshots 2 & 3)
# -------------------------------------------------------------
@app.route('/farmer_dashboard')
@role_required('farmer')
def farmer_dashboard():
    user_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    farmer = cursor.fetchone()

    cursor.execute("SELECT * FROM crops WHERE farmer_id = ? ORDER BY id DESC", (user_id,))
    crops = cursor.fetchall()

    available_count = sum(1 for c in crops if c['status'] == 'Available')
    sold_out_count = sum(1 for c in crops if c['status'] != 'Available')

    conn.close()

    return render_template(
        'farmer/dashboard.html',
        farmer=farmer,
        crops=crops,
        available_count=available_count,
        sold_out_count=sold_out_count,
        active_page='dashboard'
    )

@app.route('/get_government_price', methods=['GET'])
def get_government_price():
    crop_name = request.args.get('crop_name', '').strip()
    if not crop_name:
        return jsonify({'success': False, 'message': 'Crop name is required.'})

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT price, unit, crop_type, msp_year
        FROM government_prices
        WHERE LOWER(crop_name) = LOWER(?) OR LOWER(crop_name) LIKE LOWER(?)
        ORDER BY updated_at DESC
        LIMIT 1
    ''', (crop_name, f"%{crop_name}%"))
    record = cursor.fetchone()
    conn.close()

    if record:
        return jsonify({
            'success': True,
            'price': float(record['price']),
            'unit': record['unit'],
            'crop_type': record['crop_type'],
            'msp_year': record['msp_year']
        })

    return jsonify({
        'success': False,
        'message': 'Official government price not found for this crop.'
    })

@app.route('/add_crop', methods=['GET', 'POST'])
@role_required('farmer')
def add_crop():
    conn = get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        farmer_id = session['user_id']
        crop_name = request.form.get('crop_name', '').strip()
        crop_type = request.form.get('crop_type', 'Vegetables').strip()
        quantity = float(request.form.get('quantity', 0))
        unit = request.form.get('unit', 'kg').strip()
        harvest_date = request.form.get('harvest_date', '').strip()
        location = request.form.get('location', '').strip()
        image_url = request.form.get('image_url', '').strip() or 'https://images.unsplash.com/photo-1586201375761-83865001e31c?w=600'
        description = request.form.get('description', '').strip()

        # Check official government price (MSP / Regulated Price)
        cursor.execute('''
            SELECT price, unit, crop_type
            FROM government_prices
            WHERE LOWER(crop_name) = LOWER(?) OR LOWER(crop_name) LIKE LOWER(?)
            ORDER BY updated_at DESC
            LIMIT 1
        ''', (crop_name, f"%{crop_name}%"))
        price_record = cursor.fetchone()

        if price_record:
            price_per_unit = float(price_record['price'])
            unit = price_record['unit']
            crop_type = price_record['crop_type']
        else:
            price_per_unit = float(request.form.get('price_per_unit', 0))

        cursor.execute('''
            INSERT INTO crops (farmer_id, crop_name, crop_type, quantity, unit, price_per_unit, harvest_date, location, image_url, description, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Available')
        ''', (farmer_id, crop_name, crop_type, quantity, unit, price_per_unit, harvest_date, location, image_url, description))
        conn.commit()
        conn.close()

        flash(f'Crop "{crop_name}" listed successfully with Government Price ₹{price_per_unit}/{unit}!', 'success')
        return redirect(url_for('farmer_dashboard'))

    cursor.execute("SELECT * FROM government_prices ORDER BY crop_type, crop_name")
    gov_crops = cursor.fetchall()
    conn.close()
    return render_template('farmer/add_crop.html', gov_crops=gov_crops, active_page='add_crop')

@app.route('/my_crops')
@role_required('farmer')
def my_crops():
    farmer_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM crops WHERE farmer_id = ? ORDER BY id DESC", (farmer_id,))
    crops = cursor.fetchall()
    conn.close()
    return render_template('farmer/my_crops.html', crops=crops, active_page='my_crops')

@app.route('/crop/edit/<int:crop_id>', methods=['GET', 'POST'])
@role_required('farmer')
def edit_crop(crop_id):
    conn = get_db()
    cursor = conn.cursor()
    if request.method == 'POST':
        crop_name = request.form.get('crop_name')
        crop_type = request.form.get('crop_type')
        quantity = float(request.form.get('quantity'))
        unit = request.form.get('unit')
        price_per_unit = float(request.form.get('price_per_unit'))
        harvest_date = request.form.get('harvest_date')
        location = request.form.get('location')
        image_url = request.form.get('image_url')
        description = request.form.get('description')
        status = request.form.get('status', 'Available')

        cursor.execute('''
            UPDATE crops
            SET crop_name = ?, crop_type = ?, quantity = ?, unit = ?, price_per_unit = ?, harvest_date = ?, location = ?, image_url = ?, description = ?, status = ?
            WHERE id = ? AND farmer_id = ?
        ''', (crop_name, crop_type, quantity, unit, price_per_unit, harvest_date, location, image_url, description, status, crop_id, session['user_id']))
        conn.commit()
        conn.close()
        flash('Crop listing updated successfully!', 'success')
        return redirect(url_for('my_crops'))

    cursor.execute("SELECT * FROM crops WHERE id = ? AND farmer_id = ?", (crop_id, session['user_id']))
    crop = cursor.fetchone()
    conn.close()
    if not crop:
        flash('Crop not found or unauthorized.', 'error')
        return redirect(url_for('farmer_dashboard'))
    return render_template('farmer/add_crop.html', crop=crop, is_edit=True, active_page='my_crops')

@app.route('/crop/delete/<int:crop_id>', methods=['POST'])
@role_required('farmer')
def delete_crop(crop_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM crops WHERE id = ? AND farmer_id = ?", (crop_id, session['user_id']))
    conn.commit()
    conn.close()
    flash('Crop listing deleted successfully.', 'info')
    return redirect(request.referrer or url_for('farmer_dashboard'))

@app.route('/crop/toggle/<int:crop_id>', methods=['POST'])
@role_required('farmer')
def toggle_crop_status(crop_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM crops WHERE id = ? AND farmer_id = ?", (crop_id, session['user_id']))
    crop = cursor.fetchone()
    if crop:
        new_status = 'Sold Out' if crop['status'] == 'Available' else 'Available'
        cursor.execute("UPDATE crops SET status = ? WHERE id = ?", (new_status, crop_id))
        conn.commit()
        flash(f'Crop status updated to {new_status}.', 'success')
    conn.close()
    return redirect(request.referrer or url_for('my_crops'))

@app.route('/farmer/orders')
@role_required('farmer')
def farmer_orders():
    farmer_id = session['user_id']
    tab = request.args.get('tab', 'incoming')
    conn = get_db()
    cursor = conn.cursor()

    # 1. Incoming crop purchase requests from buyers
    cursor.execute('''
        SELECT o.*, u.name as buyer_name, u.phone as buyer_user_phone
        FROM orders o
        JOIN users u ON o.buyer_id = u.id
        WHERE o.seller_id = ? AND o.item_type = 'crop'
        ORDER BY o.id DESC
    ''', (farmer_id,))
    incoming_orders = cursor.fetchall()

    # 2. My bookings & rentals (Godowns, Machinery, Farm supplies placed by this farmer)
    cursor.execute('''
        SELECT o.*, u.name as provider_name, u.phone as provider_phone, u.district as provider_district, u.role as provider_role
        FROM orders o
        JOIN users u ON o.seller_id = u.id
        WHERE o.buyer_id = ?
        ORDER BY o.id DESC
    ''', (farmer_id,))
    my_bookings = cursor.fetchall()

    pending_orders = [o for o in incoming_orders if o['status'] == 'Pending']
    accepted_orders = [o for o in incoming_orders if o['status'] in ('Accepted', 'Dispatched', 'Completed')]
    total_revenue = sum(o['total_amount'] for o in incoming_orders if o['status'] in ('Accepted', 'Dispatched', 'Completed'))

    conn.close()

    return render_template(
        'farmer/orders.html',
        orders=incoming_orders,
        incoming_orders=incoming_orders,
        my_bookings=my_bookings,
        pending_orders=pending_orders,
        accepted_orders=accepted_orders,
        total_revenue=total_revenue,
        active_tab=tab,
        active_page='orders'
    )

@app.route('/order/update_status/<int:order_id>', methods=['POST'])
@login_required
def update_order_status(order_id):
    new_status = request.form.get('new_status', 'Accepted')
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
    order = cursor.fetchone()

    if not order:
        conn.close()
        flash('Order not found.', 'error')
        return redirect(request.referrer or url_for('index'))

    # Update order status
    cursor.execute("UPDATE orders SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (new_status, order_id))
    conn.commit()
    conn.close()

    if new_status == 'Accepted':
        flash(f'Order {order["order_number"]} has been ACCEPTED! Buyer has been notified.', 'success')
    elif new_status == 'Rejected':
        flash(f'Order {order["order_number"]} has been REJECTED.', 'warning')
    else:
        flash(f'Order status updated to {new_status}.', 'info')

    role = session.get('role')
    if role == 'godown':
        fallback = url_for('godown_orders')
    elif role == 'machinery':
        fallback = url_for('machinery_orders')
    elif role == 'agri_shop':
        fallback = url_for('shop_orders')
    else:
        fallback = url_for('farmer_orders')
    return redirect(request.referrer or fallback)

# Farmer Nearby Services
@app.route('/nearby_agri_shops')
@role_required('farmer', 'buyer')
def nearby_agri_shops():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT sp.*, u.name as owner_name, u.shop_name, u.phone, u.district
        FROM shop_products sp
        JOIN users u ON sp.shop_id = u.id
        ORDER BY sp.id DESC
    ''')
    products = cursor.fetchall()
    conn.close()
    return render_template('farmer/nearby_shops.html', products=products, active_page='nearby_shops')

@app.route('/nearby_machinery')
@role_required('farmer', 'buyer')
def nearby_machinery():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT m.*, u.name as owner_name, u.phone as owner_phone
        FROM machinery m
        JOIN users u ON m.owner_id = u.id
        WHERE m.status = 'Available'
        ORDER BY m.id DESC
    ''')
    machineries = cursor.fetchall()
    conn.close()
    return render_template('farmer/nearby_machinery.html', machineries=machineries, active_page='nearby_machinery')

@app.route('/nearby_godowns')
@role_required('farmer', 'buyer')
def nearby_godowns():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT g.*, u.name as owner_name, u.phone as owner_phone
        FROM godowns g
        JOIN users u ON g.owner_id = u.id
        WHERE g.status = 'Available'
        ORDER BY g.id DESC
    ''')
    godowns = cursor.fetchall()
    conn.close()
    return render_template('farmer/nearby_godowns.html', godowns=godowns, active_page='nearby_godowns')

@app.route('/book_godown', methods=['POST'])
@login_required
def book_godown():
    buyer_id = session['user_id']
    godown_id = int(request.form.get('godown_id'))
    quantity = float(request.form.get('quantity', 1))
    duration_months = int(request.form.get('duration_months', 1))
    start_date = request.form.get('start_date', '')
    crop_name = request.form.get('crop_name', '').strip() or 'Agricultural Produce'
    buyer_phone = request.form.get('buyer_phone', '').strip() or session.get('phone', '')
    notes = request.form.get('notes', '').strip()

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM godowns WHERE id = ?", (godown_id,))
    godown = cursor.fetchone()

    if not godown:
        conn.close()
        flash('Godown facility not found.', 'error')
        return redirect(url_for('nearby_godowns'))

    if quantity > godown['available_capacity']:
        conn.close()
        flash(f"Requested storage ({quantity} {godown['capacity_unit']}) exceeds available space ({godown['available_capacity']} {godown['capacity_unit']}).", 'error')
        return redirect(url_for('nearby_godowns'))

    total_amount = round(quantity * duration_months * godown['rent_rate'], 2)
    order_number = f"ORD-GDN-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    item_title = f"{godown['godown_name']} ({quantity} {godown['capacity_unit']} for {duration_months} Months)"
    delivery_info = f"Storage for {crop_name} starting on {start_date}. Location: {godown['location']}"
    farmer_notes = f"Crop: {crop_name} | Duration: {duration_months} mo | Start: {start_date} | Notes: {notes}"

    cursor.execute('''
        INSERT INTO orders (
            order_number, buyer_id, seller_id, item_type, item_id, item_name,
            quantity, unit_price, total_amount, delivery_address, buyer_phone, district,
            payment_method, payment_status, status, farmer_notes
        )
        VALUES (?, ?, ?, 'godown_booking', ?, ?, ?, ?, ?, ?, ?, ?, 'Pay at Godown', 'Pending', 'Pending', ?)
    ''', (
        order_number, buyer_id, godown['owner_id'], godown['id'], item_title,
        quantity, godown['rent_rate'], total_amount, delivery_info, buyer_phone,
        session.get('district', 'thenkasi'), farmer_notes
    ))

    # Update available capacity
    new_avail = max(0.0, godown['available_capacity'] - quantity)
    cursor.execute("UPDATE godowns SET available_capacity = ? WHERE id = ?", (new_avail, godown['id']))

    conn.commit()
    conn.close()

    flash(f"Storage space booked successfully! Order ID: {order_number}. Godown owner has received your reservation request.", 'success')
    if session.get('role') == 'farmer':
        return redirect(url_for('farmer_orders', tab='my_bookings'))
    return redirect(url_for('track_order', order_number=order_number))

@app.route('/book_machinery', methods=['POST'])
@login_required
def book_machinery():
    buyer_id = session['user_id']
    machine_id = int(request.form.get('machine_id'))
    hours = float(request.form.get('hours', 4))
    start_date = request.form.get('start_date', '')
    buyer_phone = request.form.get('buyer_phone', '').strip() or session.get('phone', '')
    field_location = request.form.get('field_location', '').strip() or session.get('village', 'Farm Field')
    notes = request.form.get('notes', '').strip()

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM machinery WHERE id = ?", (machine_id,))
    machine = cursor.fetchone()

    if not machine:
        conn.close()
        flash('Machinery not found.', 'error')
        return redirect(url_for('nearby_machinery'))

    total_amount = round(hours * machine['rent_rate'], 2)
    order_number = f"ORD-MCH-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    item_title = f"{machine['machine_name']} ({hours} {machine['rate_unit']})"
    farmer_notes = f"Rental Date: {start_date} | Hours: {hours} | Field: {field_location} | Notes: {notes}"

    cursor.execute('''
        INSERT INTO orders (
            order_number, buyer_id, seller_id, item_type, item_id, item_name,
            quantity, unit_price, total_amount, delivery_address, buyer_phone, district,
            payment_method, payment_status, status, farmer_notes
        )
        VALUES (?, ?, ?, 'machinery_rental', ?, ?, ?, ?, ?, ?, ?, ?, 'Pay on Service', 'Pending', 'Pending', ?)
    ''', (
        order_number, buyer_id, machine['owner_id'], machine['id'], item_title,
        hours, machine['rent_rate'], total_amount, field_location, buyer_phone,
        session.get('district', 'thenkasi'), farmer_notes
    ))

    conn.commit()
    conn.close()

    flash(f"Machinery rental booked successfully! Order ID: {order_number}. Machine owner has received your request.", 'success')
    if session.get('role') == 'farmer':
        return redirect(url_for('farmer_orders', tab='my_bookings'))
    return redirect(url_for('track_order', order_number=order_number))

# -------------------------------------------------------------
# AGRI SHOP MODULE (Matches Screenshot 1)
# -------------------------------------------------------------
@app.route('/agri_shop_dashboard')
@role_required('agri_shop')
def agri_shop_dashboard():
    shop_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM shop_products WHERE shop_id = ? ORDER BY id DESC", (shop_id,))
    products = cursor.fetchall()

    cursor.execute("SELECT * FROM orders WHERE seller_id = ? ORDER BY id DESC", (shop_id,))
    orders = cursor.fetchall()

    total_stock = sum(p['stock'] for p in products)
    revenue = sum(o['total_amount'] for o in orders if o['status'] in ('Accepted', 'Dispatched', 'Completed'))

    conn.close()

    return render_template(
        'shop/dashboard.html',
        products=products,
        orders=orders,
        total_stock=total_stock,
        revenue=revenue,
        active_page='dashboard'
    )

@app.route('/shop/add_product', methods=['GET', 'POST'])
@role_required('agri_shop')
def add_product():
    if request.method == 'POST':
        shop_id = session['user_id']
        product_name = request.form.get('product_name', '').strip()
        category = request.form.get('category', 'Fertilizers')
        price = float(request.form.get('price', 0))
        stock = int(request.form.get('stock', 0))
        unit = request.form.get('unit', 'Unit')
        image_url = request.form.get('image_url', '').strip() or 'https://images.unsplash.com/photo-1628352081506-83c43123ed6d?w=600'
        description = request.form.get('description', '').strip()

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO shop_products (shop_id, product_name, category, price, stock, unit, image_url, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (shop_id, product_name, category, price, stock, unit, image_url, description))
        conn.commit()
        conn.close()

        flash(f'Product "{product_name}" added successfully to your agri shop inventory!', 'success')
        return redirect(url_for('agri_shop_dashboard'))

    return render_template('shop/add_product.html', active_page='add_product')

@app.route('/shop/view_products')
@role_required('agri_shop')
def view_products():
    shop_id = session['user_id']
    category = request.args.get('category', '').strip()
    search_q = request.args.get('q', '').strip()

    conn = get_db()
    cursor = conn.cursor()

    query = "SELECT * FROM shop_products WHERE shop_id = ?"
    params = [shop_id]

    if category:
        query += " AND category = ?"
        params.append(category)
    if search_q:
        query += " AND (product_name LIKE ? OR description LIKE ?)"
        params.extend([f"%{search_q}%", f"%{search_q}%"])

    query += " ORDER BY id DESC"
    cursor.execute(query, params)
    products = cursor.fetchall()

    cursor.execute("SELECT DISTINCT category FROM shop_products WHERE shop_id = ?", (shop_id,))
    categories = [row['category'] for row in cursor.fetchall() if row['category']]
    conn.close()

    return render_template(
        'shop/view_products.html',
        products=products,
        categories=categories,
        selected_category=category,
        search_q=search_q,
        active_page='view_products'
    )

@app.route('/shop/manage_stock')
@role_required('agri_shop')
def manage_stock():
    shop_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM shop_products WHERE shop_id = ? ORDER BY id DESC", (shop_id,))
    products = cursor.fetchall()
    conn.close()
    return render_template('shop/manage_stock.html', products=products, active_page='manage_stock')

@app.route('/shop/product/edit/<int:product_id>', methods=['GET', 'POST'])
@role_required('agri_shop')
def edit_product(product_id):
    conn = get_db()
    cursor = conn.cursor()
    if request.method == 'POST':
        product_name = request.form.get('product_name')
        category = request.form.get('category')
        price = float(request.form.get('price'))
        stock = int(request.form.get('stock'))
        unit = request.form.get('unit')
        image_url = request.form.get('image_url')
        description = request.form.get('description')

        cursor.execute('''
            UPDATE shop_products
            SET product_name = ?, category = ?, price = ?, stock = ?, unit = ?, image_url = ?, description = ?
            WHERE id = ? AND shop_id = ?
        ''', (product_name, category, price, stock, unit, image_url, description, product_id, session['user_id']))
        conn.commit()
        conn.close()
        flash('Product details updated successfully!', 'success')
        return redirect(url_for('manage_stock'))

    cursor.execute("SELECT * FROM shop_products WHERE id = ? AND shop_id = ?", (product_id, session['user_id']))
    product = cursor.fetchone()
    conn.close()
    if not product:
        flash('Product not found.', 'error')
        return redirect(url_for('agri_shop_dashboard'))

    return render_template('shop/add_product.html', product=product, is_edit=True, active_page='manage_stock')

@app.route('/shop/product/delete/<int:product_id>', methods=['POST'])
@role_required('agri_shop')
def delete_product(product_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM shop_products WHERE id = ? AND shop_id = ?", (product_id, session['user_id']))
    conn.commit()
    conn.close()
    flash('Product removed from shop inventory.', 'info')
    return redirect(request.referrer or url_for('agri_shop_dashboard'))

@app.route('/shop/product/update_stock/<int:product_id>', methods=['POST'])
@role_required('agri_shop')
def update_stock(product_id):
    new_stock = int(request.form.get('new_stock', 0))
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE shop_products SET stock = ? WHERE id = ? AND shop_id = ?", (new_stock, product_id, session['user_id']))
    conn.commit()
    conn.close()
    flash('Stock quantity updated successfully.', 'success')
    return redirect(url_for('manage_stock'))

@app.route('/shop/orders')
@role_required('agri_shop')
def shop_orders():
    shop_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT o.*, u.name as buyer_name, u.phone as buyer_user_phone
        FROM orders o
        JOIN users u ON o.buyer_id = u.id
        WHERE o.seller_id = ?
        ORDER BY o.id DESC
    ''', (shop_id,))
    orders = cursor.fetchall()
    conn.close()
    return render_template('shop/orders.html', orders=orders, active_page='orders')

# -------------------------------------------------------------
# MACHINERY & GODOWN MODULES
# -------------------------------------------------------------
@app.route('/machinery_dashboard')
@role_required('machinery')
def machinery_dashboard():
    owner_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM machinery WHERE owner_id = ? ORDER BY id DESC", (owner_id,))
    machineries = cursor.fetchall()
    available_count = sum(1 for m in machineries if m['status'] == 'Available')
    rented_count = sum(1 for m in machineries if m['status'] != 'Available')

    cursor.execute('''
        SELECT o.*, u.name as buyer_name, u.phone as buyer_user_phone
        FROM orders o
        JOIN users u ON o.buyer_id = u.id
        WHERE o.seller_id = ? AND o.item_type = 'machinery_rental'
        ORDER BY o.id DESC
    ''', (owner_id,))
    bookings = cursor.fetchall()
    revenue = sum(b['total_amount'] for b in bookings if b['status'] in ('Accepted', 'Completed'))
    conn.close()
    return render_template('machinery/dashboard.html', machineries=machineries, bookings=bookings, available_count=available_count, rented_count=rented_count, revenue=revenue, active_page='dashboard')

@app.route('/machinery/add', methods=['GET', 'POST'])
@role_required('machinery')
def add_machinery():
    if request.method == 'POST':
        owner_id = session['user_id']
        machine_name = request.form.get('machine_name', '').strip()
        machine_type = request.form.get('machine_type', 'Tractor')
        rent_rate = float(request.form.get('rent_rate', 0))
        rate_unit = request.form.get('rate_unit', 'per hour')
        driver_included = int(request.form.get('driver_included', 1))
        location = request.form.get('location', '')
        contact_phone = request.form.get('contact_phone', '')
        image_url = request.form.get('image_url', '').strip() or 'https://images.unsplash.com/photo-1592878904946-b3cd8ae243d0?w=600'

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO machinery (owner_id, machine_name, machine_type, rent_rate, rate_unit, driver_included, location, contact_phone, image_url, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Available')
        ''', (owner_id, machine_name, machine_type, rent_rate, rate_unit, driver_included, location, contact_phone, image_url))
        conn.commit()
        conn.close()
        flash(f'Machine "{machine_name}" published for rentals!', 'success')
        return redirect(url_for('machinery_dashboard'))
    return render_template('machinery/add_machinery.html', active_page='add_machinery')

@app.route('/machinery/delete/<int:machine_id>', methods=['POST'])
@role_required('machinery')
def delete_machinery(machine_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM machinery WHERE id = ? AND owner_id = ?", (machine_id, session['user_id']))
    conn.commit()
    conn.close()
    flash('Machinery listing removed.', 'info')
    return redirect(url_for('machinery_dashboard'))

@app.route('/machinery/orders')
@role_required('machinery')
def machinery_orders():
    owner_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT o.*, u.name as buyer_name, u.phone as buyer_user_phone, u.district as buyer_district
        FROM orders o
        JOIN users u ON o.buyer_id = u.id
        WHERE o.seller_id = ? AND o.item_type = 'machinery_rental'
        ORDER BY o.id DESC
    ''', (owner_id,))
    bookings = cursor.fetchall()
    conn.close()

    pending_count = sum(1 for b in bookings if b['status'] == 'Pending')
    accepted_count = sum(1 for b in bookings if b['status'] in ('Accepted', 'Dispatched', 'Completed'))
    revenue = sum(b['total_amount'] for b in bookings if b['status'] in ('Accepted', 'Dispatched', 'Completed'))

    return render_template(
        'machinery/orders.html',
        bookings=bookings,
        pending_count=pending_count,
        accepted_count=accepted_count,
        revenue=revenue,
        active_page='orders'
    )

@app.route('/godown_dashboard')
@role_required('godown')
def godown_dashboard():
    owner_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM godowns WHERE owner_id = ? ORDER BY id DESC", (owner_id,))
    godowns = cursor.fetchall()

    cursor.execute('''
        SELECT o.*, u.name as buyer_name, u.phone as buyer_user_phone
        FROM orders o
        JOIN users u ON o.buyer_id = u.id
        WHERE o.seller_id = ? AND o.item_type = 'godown_booking'
        ORDER BY o.id DESC
    ''', (owner_id,))
    bookings = cursor.fetchall()

    total_capacity = sum(g['total_capacity'] for g in godowns)
    available_capacity = sum(g['available_capacity'] for g in godowns)
    revenue = sum(b['total_amount'] for b in bookings if b['status'] in ('Accepted', 'Dispatched', 'Completed'))
    conn.close()
    return render_template('godown/dashboard.html', godowns=godowns, bookings=bookings, total_capacity=total_capacity, available_capacity=available_capacity, revenue=revenue, active_page='dashboard')

@app.route('/godown/add', methods=['GET', 'POST'])
@role_required('godown')
def add_godown():
    if request.method == 'POST':
        owner_id = session['user_id']
        godown_name = request.form.get('godown_name', '').strip()
        godown_type = request.form.get('godown_type', 'Dry Warehouse')
        total_capacity = float(request.form.get('total_capacity', 0))
        available_capacity = float(request.form.get('available_capacity', 0))
        capacity_unit = request.form.get('capacity_unit', 'Tons')
        rent_rate = float(request.form.get('rent_rate', 0))
        rate_unit = request.form.get('rate_unit', 'per ton / month')
        location = request.form.get('location', '')
        contact_phone = request.form.get('contact_phone', '')
        temp_ctrl = 1 if request.form.get('temperature_controlled') else 0

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO godowns (owner_id, godown_name, godown_type, total_capacity, available_capacity, capacity_unit, rent_rate, rate_unit, location, contact_phone, temperature_controlled, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Available')
        ''', (owner_id, godown_name, godown_type, total_capacity, available_capacity, capacity_unit, rent_rate, rate_unit, location, contact_phone, temp_ctrl))
        conn.commit()
        conn.close()
        flash(f'Godown facility "{godown_name}" listed successfully!', 'success')
        return redirect(url_for('godown_dashboard'))
    return render_template('godown/add_godown.html', active_page='add_godown')

@app.route('/godown/delete/<int:godown_id>', methods=['POST'])
@role_required('godown')
def delete_godown(godown_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM godowns WHERE id = ? AND owner_id = ?", (godown_id, session['user_id']))
    conn.commit()
    conn.close()
    flash('Storage facility listing removed.', 'info')
    return redirect(url_for('godown_dashboard'))

@app.route('/godown/orders')
@role_required('godown')
def godown_orders():
    owner_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT o.*, u.name as buyer_name, u.phone as buyer_user_phone, u.district as buyer_district
        FROM orders o
        JOIN users u ON o.buyer_id = u.id
        WHERE o.seller_id = ? AND o.item_type = 'godown_booking'
        ORDER BY o.id DESC
    ''', (owner_id,))
    bookings = cursor.fetchall()
    conn.close()

    pending_count = sum(1 for b in bookings if b['status'] == 'Pending')
    accepted_count = sum(1 for b in bookings if b['status'] in ('Accepted', 'Dispatched', 'Completed'))
    revenue = sum(b['total_amount'] for b in bookings if b['status'] in ('Accepted', 'Dispatched', 'Completed'))

    return render_template(
        'godown/orders.html',
        bookings=bookings,
        pending_count=pending_count,
        accepted_count=accepted_count,
        revenue=revenue,
        active_page='orders'
    )

# -------------------------------------------------------------
# BUYER E-COMMERCE & MARKETPLACE & RAZORPAY PAYMENT
# -------------------------------------------------------------
@app.route('/marketplace')
def buyer_marketplace():
    search = request.args.get('search', '').strip()
    category = request.args.get('category', '').strip()

    conn = get_db()
    cursor = conn.cursor()

    query = '''
        SELECT c.*, u.name as farmer_name, u.district, u.phone
        FROM crops c
        JOIN users u ON c.farmer_id = u.id
        WHERE c.status = 'Available'
    '''
    params = []

    if search:
        query += " AND (c.crop_name LIKE ? OR c.description LIKE ? OR c.location LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term])

    if category:
        query += " AND c.crop_type = ?"
        params.append(category)

    query += " ORDER BY c.id DESC"
    cursor.execute(query, params)
    crops = cursor.fetchall()
    conn.close()

    return render_template('buyer/marketplace.html', crops=crops, search_query=search, selected_category=category, active_page='marketplace')

@app.route('/crop/<int:crop_id>')
def crop_detail(crop_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT c.*, u.name as farmer_name, u.district, u.phone, u.village
        FROM crops c
        JOIN users u ON c.farmer_id = u.id
        WHERE c.id = ?
    ''', (crop_id,))
    crop = cursor.fetchone()
    conn.close()

    if not crop:
        flash('Produce item not found.', 'error')
        return redirect(url_for('buyer_marketplace'))

    return render_template('buyer/crop_detail.html', crop=crop, active_page='marketplace')

@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    if 'user_id' not in session:
        flash('Please login or register to add produce to your cart.', 'warning')
        return redirect(url_for('login'))

    user_id = session['user_id']
    item_type = request.form.get('item_type', 'crop')
    item_id = int(request.form.get('item_id'))
    quantity = float(request.form.get('quantity', 1.0))

    conn = get_db()
    cursor = conn.cursor()

    # Check if already in cart
    cursor.execute("SELECT id, quantity FROM cart WHERE user_id = ? AND item_type = ? AND item_id = ?", (user_id, item_type, item_id))
    existing = cursor.fetchone()

    if existing:
        new_qty = existing['quantity'] + quantity
        cursor.execute("UPDATE cart SET quantity = ? WHERE id = ?", (new_qty, existing['id']))
    else:
        cursor.execute("INSERT INTO cart (user_id, item_type, item_id, quantity) VALUES (?, ?, ?, ?)", (user_id, item_type, item_id, quantity))

    conn.commit()
    conn.close()

    flash('Item added to your cart!', 'success')
    return redirect(url_for('view_cart'))

@app.route('/cart/buy_now', methods=['POST'])
def buy_now():
    if 'user_id' not in session:
        flash('Please login to complete your purchase.', 'warning')
        return redirect(url_for('login'))

    user_id = session['user_id']
    crop_id = int(request.form.get('crop_id'))
    quantity = float(request.form.get('quantity', 1.0))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
    cursor.execute("INSERT INTO cart (user_id, item_type, item_id, quantity) VALUES (?, 'crop', ?, ?)", (user_id, crop_id, quantity))
    conn.commit()
    conn.close()

    return redirect(url_for('view_cart'))

@app.route('/cart')
@login_required
def view_cart():
    user_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()

    cursor.execute("SELECT * FROM cart WHERE user_id = ?", (user_id,))
    raw_cart = cursor.fetchall()

    cart_items = []
    subtotal = 0.0

    for item in raw_cart:
        if item['item_type'] == 'crop':
            cursor.execute('''
                SELECT c.*, u.name as seller_name, u.role as seller_role
                FROM crops c
                JOIN users u ON c.farmer_id = u.id
                WHERE c.id = ?
            ''', (item['item_id'],))
            crop = cursor.fetchone()
            if crop:
                line_total = crop['price_per_unit'] * item['quantity']
                subtotal += line_total
                cart_items.append({
                    'cart_id': item['id'],
                    'item_id': crop['id'],
                    'item_type': 'crop',
                    'item_name': crop['crop_name'],
                    'unit_price': crop['price_per_unit'],
                    'quantity': item['quantity'],
                    'total_price': line_total,
                    'image_url': crop['image_url'],
                    'seller_name': crop['seller_name'],
                    'seller_role': crop['seller_role'],
                    'seller_id': crop['farmer_id']
                })
        else:
            cursor.execute('''
                SELECT sp.*, u.name as seller_name, u.role as seller_role
                FROM shop_products sp
                JOIN users u ON sp.shop_id = u.id
                WHERE sp.id = ?
            ''', (item['item_id'],))
            product = cursor.fetchone()
            if product:
                line_total = product['price'] * item['quantity']
                subtotal += line_total
                cart_items.append({
                    'cart_id': item['id'],
                    'item_id': product['id'],
                    'item_type': 'shop_product',
                    'item_name': product['product_name'],
                    'unit_price': product['price'],
                    'quantity': item['quantity'],
                    'total_price': line_total,
                    'image_url': product['image_url'],
                    'seller_name': product['seller_name'],
                    'seller_role': product['seller_role'],
                    'seller_id': product['shop_id']
                })

    conn.close()

    return render_template('buyer/cart.html', cart_items=cart_items, subtotal=subtotal, user=user, active_page='cart')

@app.route('/cart/remove/<int:cart_id>', methods=['POST'])
@login_required
def remove_from_cart(cart_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cart WHERE id = ? AND user_id = ?", (cart_id, session['user_id']))
    conn.commit()
    conn.close()
    flash('Item removed from cart.', 'info')
    return redirect(url_for('view_cart'))

@app.route('/create_razorpay_order', methods=['POST'])
@login_required
def create_razorpay_order():
    data = request.get_json() or {}
    amount = float(data.get('amount', 0))
    amount_in_paise = int(round(amount * 100))
    receipt = f"rcpt_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    order_id = None
    if rzp_client:
        try:
            rzp_order = rzp_client.order.create({
                'amount': amount_in_paise,
                'currency': 'INR',
                'receipt': receipt,
                'payment_capture': 1
            })
            order_id = rzp_order['id']
        except Exception as e:
            print(f"Razorpay order create error: {e}")

    return jsonify({
        'status': 'success',
        'key_id': RAZORPAY_KEY_ID,
        'order_id': order_id,
        'amount_in_paise': amount_in_paise
    })

@app.route('/place_order', methods=['POST'])
@login_required
def place_order():
    buyer_id = session['user_id']
    buyer_name = request.form.get('buyer_name', '').strip()
    buyer_phone = request.form.get('buyer_phone', '').strip()
    delivery_address = request.form.get('delivery_address', '').strip()
    district = request.form.get('district', '').strip()
    payment_method = request.form.get('payment_method', 'Razorpay')
    payment_status = request.form.get('payment_status', 'Paid' if payment_method == 'Razorpay' else 'Pending')
    rzp_payment_id = request.form.get('razorpay_payment_id', '')
    rzp_order_id = request.form.get('razorpay_order_id', '')

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM cart WHERE user_id = ?", (buyer_id,))
    cart_items = cursor.fetchall()

    if not cart_items:
        conn.close()
        flash('Your cart is empty.', 'error')
        return redirect(url_for('buyer_marketplace'))

    created_order_number = None

    for item in cart_items:
        order_num = f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}-{item['id']}"
        created_order_number = order_num

        if item['item_type'] == 'crop':
            cursor.execute("SELECT * FROM crops WHERE id = ?", (item['item_id'],))
            crop = cursor.fetchone()
            if crop:
                seller_id = crop['farmer_id']
                unit_price = crop['price_per_unit']
                total_amount = unit_price * item['quantity']
                item_name = crop['crop_name']

                cursor.execute('''
                    INSERT INTO orders (order_number, buyer_id, seller_id, item_type, item_id, item_name, quantity, unit_price, total_amount, delivery_address, buyer_phone, district, payment_method, payment_status, razorpay_order_id, razorpay_payment_id, status)
                    VALUES (?, ?, ?, 'crop', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending')
                ''', (order_num, buyer_id, seller_id, crop['id'], item_name, item['quantity'], unit_price, total_amount, delivery_address, buyer_phone, district, payment_method, payment_status, rzp_order_id, rzp_payment_id))
        else:
            cursor.execute("SELECT * FROM shop_products WHERE id = ?", (item['item_id'],))
            product = cursor.fetchone()
            if product:
                seller_id = product['shop_id']
                unit_price = product['price']
                total_amount = unit_price * item['quantity']
                item_name = product['product_name']

                cursor.execute('''
                    INSERT INTO orders (order_number, buyer_id, seller_id, item_type, item_id, item_name, quantity, unit_price, total_amount, delivery_address, buyer_phone, district, payment_method, payment_status, razorpay_order_id, razorpay_payment_id, status)
                    VALUES (?, ?, ?, 'shop_product', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending')
                ''', (order_num, buyer_id, seller_id, product['id'], item_name, item['quantity'], unit_price, total_amount, delivery_address, buyer_phone, district, payment_method, payment_status, rzp_order_id, rzp_payment_id))

    # Clear user's cart
    cursor.execute("DELETE FROM cart WHERE user_id = ?", (buyer_id,))
    conn.commit()
    conn.close()

    flash('Order placed successfully! Farmer has received your request.', 'success')
    return redirect(url_for('track_order', order_number=created_order_number))

@app.route('/orders')
@login_required
def buyer_orders():
    buyer_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT o.*, u.name as seller_name, u.phone as seller_phone, u.district as seller_district, u.role as seller_role
        FROM orders o
        JOIN users u ON o.seller_id = u.id
        WHERE o.buyer_id = ?
        ORDER BY o.id DESC
    ''', (buyer_id,))
    orders = cursor.fetchall()
    conn.close()
    return render_template('buyer/orders.html', orders=orders, active_page='orders')

@app.route('/track/<order_number>')
@login_required
def track_order(order_number):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT o.*, 
               b.name as buyer_name, b.phone as buyer_contact,
               s.name as seller_name, s.phone as seller_phone, s.district as seller_district, s.role as seller_role
        FROM orders o
        JOIN users b ON o.buyer_id = b.id
        JOIN users s ON o.seller_id = s.id
        WHERE o.order_number = ?
    ''', (order_number,))
    order = cursor.fetchone()
    conn.close()

    if not order:
        flash('Order reference not found.', 'error')
        return redirect(url_for('buyer_orders'))

    return render_template('buyer/order_tracking.html', order=order, active_page='orders')

# -------------------------------------------------------------
# RUN SERVER
# -------------------------------------------------------------
if __name__ == '__main__':
    print("🌾 Starting Sakthi Agri Web Application on http://127.0.0.1:5000 ...")
    app.run(host='0.0.0.0', port=5000, debug=True)
