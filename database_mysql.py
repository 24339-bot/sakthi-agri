"""
========================================================================
SAKTHI AGRI - MYSQL WORKBENCH DATABASE CONNECTOR & CONFIGURATION
========================================================================

How to use with MySQL Workbench:
1. Open MySQL Workbench.
2. File -> Open SQL Script -> Select 'sakthi_agri_schema.sql'.
3. Click the Lightning Bolt (⚡) button to execute and create all tables.
4. Install MySQL Python connector:
   pip install mysql-connector-python
5. Update your MySQL password below in MYSQL_CONFIG.
"""

import os

# Enter your MySQL Workbench credentials here:
MYSQL_CONFIG = {
    'host': os.environ.get('MYSQL_HOST', 'localhost'),
    'user': os.environ.get('MYSQL_USER', 'root'),
    'password': os.environ.get('MYSQL_PASSWORD', '1234'), # Set your MySQL password
    'database': os.environ.get('MYSQL_DB', 'sakthi_agri'),
    'port': int(os.environ.get('MYSQL_PORT', 3306))
}

def get_mysql_connection():
    try:
        import mysql.connector
        conn = mysql.connector.connect(
            host=MYSQL_CONFIG['host'],
            user=MYSQL_CONFIG['user'],
            password=MYSQL_CONFIG['password'],
            database=MYSQL_CONFIG['database'],
            port=MYSQL_CONFIG['port'],
            autocommit=True
        )
        return conn
    except ImportError:
        raise ImportError("MySQL connector is required. Run: pip install mysql-connector-python")
    except Exception as e:
        print(f"Error connecting to MySQL: {e}")
        raise e

def test_mysql_connection():
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) AS total_users FROM users")
        result = cursor.fetchone()
        print(f"✅ Connected to MySQL successfully! Total users in database: {result['total_users']}")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ MySQL Connection failed: {e}")
        return False

if __name__ == '__main__':
    test_mysql_connection()
