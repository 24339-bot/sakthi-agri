import unittest
from app import app
from database import get_db, init_db

class TestSakthiAgri(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()
        with app.app_context():
            init_db()

    def test_01_landing_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Sakthi Agri', response.data)

    def test_02_farmer_login_and_dashboard(self):
        # Demo login as farmer
        response = self.client.post('/demo_login', data={'role': 'farmer'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        # Check Dharani profile details match screenshot 2 & 3
        self.assertIn(b'DHARANI', response.data)
        self.assertIn(b'Vilathikulam, thenkasi', response.data)
        self.assertIn(b'7305371131', response.data)
        self.assertIn(b'24339@krcollege.net', response.data)
        self.assertIn(b'Land Area (Acres)', response.data)
        self.assertIn(b'My Crops', response.data)
        self.assertIn(b'Nearby Agri Shops', response.data)
        self.assertIn(b'Nearby Machinery', response.data)
        self.assertIn(b'Nearby Godowns', response.data)

    def test_03_agri_shop_dashboard(self):
        # Demo login as agri_shop
        response = self.client.post('/demo_login', data={'role': 'agri_shop'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        # Check Agri Shop dashboard matches screenshot 1
        self.assertIn(b'Agri Shop Dashboard', response.data)
        self.assertIn(b'Total Products', response.data)
        self.assertIn(b'Total Orders', response.data)
        self.assertIn(b'Stock Available', response.data)
        self.assertIn(b'Revenue', response.data)
        self.assertIn(b'Add Product', response.data)

    def test_04_profile_page(self):
        # Profile page matches screenshots 4 & 5
        self.client.post('/demo_login', data={'role': 'agri_shop'}, follow_redirects=True)
        response = self.client.get('/profile')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'My Profile', response.data)
        self.assertIn(b'Naresh', response.data)
        self.assertIn(b'naresh1234@gmail.com', response.data)
        self.assertIn(b'Edit Profile', response.data)
        self.assertIn(b'Change Password', response.data)
        self.assertIn(b'Cannot change', response.data)

    def test_05_farmer_add_crop_and_order_flow(self):
        # Farmer logs in and adds a new crop
        self.client.post('/demo_login', data={'role': 'farmer'}, follow_redirects=True)
        crop_data = {
            'crop_name': 'Organic Red Guava',
            'crop_type': 'Fruits',
            'quantity': 100,
            'unit': 'kg',
            'price_per_unit': 60,
            'harvest_date': '2026-10-25',
            'location': 'Vilathikulam, thenkasi',
            'description': 'Sweet organic red guavas tree fresh.'
        }
        res = self.client.post('/add_crop', data=crop_data, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Organic Red Guava', res.data)

        # Buyer logs in and views marketplace
        self.client.post('/demo_login', data={'role': 'buyer'}, follow_redirects=True)
        res_market = self.client.get('/marketplace')
        self.assertEqual(res_market.status_code, 200)
        self.assertIn(b'Organic Red Guava', res_market.data)

        # Buyer adds to cart and places order
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM crops WHERE crop_name = 'Organic Red Guava'")
        crop_id = cursor.fetchone()['id']
        conn.close()

        self.client.post('/cart/add', data={'item_type': 'crop', 'item_id': crop_id, 'quantity': 10}, follow_redirects=True)
        
        # Place order with Razorpay
        order_res = self.client.post('/place_order', data={
            'buyer_name': 'Anand Traders',
            'buyer_phone': '9443215678',
            'delivery_address': 'Shop 42, Central Market, Madurai',
            'district': 'madurai',
            'payment_method': 'Razorpay',
            'payment_status': 'Paid',
            'razorpay_payment_id': 'pay_test123456789'
        }, follow_redirects=True)
        self.assertEqual(order_res.status_code, 200)
        self.assertIn(b'Live Order Tracking', order_res.data)

        # Farmer checks incoming orders and accepts request
        self.client.post('/demo_login', data={'role': 'farmer'}, follow_redirects=True)
        orders_page = self.client.get('/farmer/orders')
        self.assertEqual(orders_page.status_code, 200)
        self.assertIn(b'Organic Red Guava', orders_page.data)
        self.assertIn(b'Pending Approval', orders_page.data)
        self.assertIn(b'Accept Order', orders_page.data)
        self.assertIn(b'Reject Request', orders_page.data)

    def test_06_farmer_accept_and_reject_order_status(self):
        # 1. Place a new order
        self.client.post('/demo_login', data={'role': 'buyer'}, follow_redirects=True)
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, farmer_id, price_per_unit FROM crops WHERE status = 'Available' LIMIT 1")
        crop = cursor.fetchone()
        conn.close()

        self.client.post('/cart/add', data={'item_type': 'crop', 'item_id': crop['id'], 'quantity': 5}, follow_redirects=True)
        order_res = self.client.post('/place_order', data={
            'buyer_name': 'Anand Traders',
            'buyer_phone': '9443215678',
            'delivery_address': 'Shop 10, Market Road, Madurai',
            'district': 'madurai',
            'payment_method': 'Razorpay',
            'payment_status': 'Paid',
            'razorpay_payment_id': 'pay_order_test_99'
        }, follow_redirects=True)
        self.assertEqual(order_res.status_code, 200)

        # 2. Get latest order id
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, order_number, status FROM orders ORDER BY id DESC LIMIT 1")
        latest_order = cursor.fetchone()
        order_id = latest_order['id']
        order_num = latest_order['order_number']
        self.assertEqual(latest_order['status'], 'Pending')
        conn.close()

        # 3. Farmer logs in and ACCEPTS order
        self.client.post('/demo_login', data={'role': 'farmer'}, follow_redirects=True)
        accept_res = self.client.post(f'/order/update_status/{order_id}', data={'new_status': 'Accepted'}, follow_redirects=True)
        self.assertEqual(accept_res.status_code, 200)
        self.assertIn(b'Order Accepted', accept_res.data)

        # 4. Buyer checks tracking - status shows Accepted
        self.client.post('/demo_login', data={'role': 'buyer'}, follow_redirects=True)
        track_res = self.client.get(f'/track/{order_num}')
        self.assertEqual(track_res.status_code, 200)
        self.assertIn(b'Accepted by Farmer', track_res.data)

    def test_07_nearby_services_and_shop_features(self):
        # Farmer views nearby shops, machinery, godowns
        self.client.post('/demo_login', data={'role': 'farmer'}, follow_redirects=True)
        
        shops_res = self.client.get('/nearby_agri_shops')
        self.assertEqual(shops_res.status_code, 200)
        self.assertIn(b'Nearby Agri Shops', shops_res.data)
        self.assertIn(b'IFFCO Neem Coated Urea', shops_res.data)

        machinery_res = self.client.get('/nearby_machinery')
        self.assertEqual(machinery_res.status_code, 200)
        self.assertIn(b'Nearby Machinery', machinery_res.data)
        self.assertIn(b'Mahindra 575 DI Tractor', machinery_res.data)

        godowns_res = self.client.get('/nearby_godowns')
        self.assertEqual(godowns_res.status_code, 200)
        self.assertIn(b'Nearby Godowns', godowns_res.data)
        self.assertIn(b'Sakthi Modern Cold Storage', godowns_res.data)

if __name__ == '__main__':
    unittest.main()
