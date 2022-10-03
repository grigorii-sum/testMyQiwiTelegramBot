import psycopg2

from configparser import ConfigParser

parser = ConfigParser()
parser.read('config.ini')
params = parser.items('postgresql')


"""Return a connection session"""
def connect_to_database():
    conn = psycopg2.connect(
        host=params[0][1],
        database=params[1][1],
        user=params[2][1],
        password=params[3][1])

    return conn


"""Return a new customer_profile instance [tuple]"""
def create_customer_profile(user_id):
    conn = connect_to_database()
    cur = conn.cursor()

    sql = """INSERT INTO customer_profile(telegram_user_id) VALUES(%s) RETURNING *;"""
    cur.execute(sql, (user_id,))

    new_customer_profile = cur.fetchone()
    conn.commit()

    cur.close()
    if conn is not None:
        conn.close()

    return new_customer_profile


"""Return a list of customer_profile instance's fields [tuple]"""
def get_customer_profile_instance(customer_profile_id):
    conn = connect_to_database()
    cur = conn.cursor()

    sql = """SELECT * FROM customer_profile WHERE telegram_user_id=(%s);"""
    cur.execute(sql, (customer_profile_id,))

    customer_profile = cur.fetchone()

    cur.close()
    if conn is not None:
        conn.close()

    return customer_profile


"""Return a list of customer_profile instances [list of tuples]"""
def get_customer_profiles_all():
    conn = connect_to_database()
    cur = conn.cursor()

    sql = """SELECT * FROM customer_profile;"""
    cur.execute(sql)

    all_customer_profile = []
    row = cur.fetchone()
    while row is not None:
        all_customer_profile.append(row)
        row = cur.fetchone()

    cur.close()
    if conn is not None:
        conn.close()

    return all_customer_profile


"""Return a list of banned customer_profile instances [list of int]"""
def get_customer_profiles_is_banned():
    conn = connect_to_database()
    cur = conn.cursor()

    sql = """SELECT telegram_user_id FROM customer_profile WHERE is_banned=true;"""
    cur.execute(sql)

    banned_customer_profile = []
    row = cur.fetchone()
    while row is not None:
        banned_customer_profile += row
        row = cur.fetchone()

    cur.close()
    if conn is not None:
        conn.close()

    return banned_customer_profile


"""Return an updated customer_profile instance [tuple]"""
def change_customer_profile_balance_field(new_balance, customer_profile_id):
    conn = connect_to_database()
    cur = conn.cursor()

    sql = """UPDATE customer_profile SET balance=%s WHERE telegram_user_id=%s RETURNING *;"""
    cur.execute(sql, (new_balance, customer_profile_id))

    updated_customer_profile = cur.fetchone()
    conn.commit()

    cur.close()
    if conn is not None:
        conn.close()

    return updated_customer_profile


"""Return None"""
def change_customer_profile_is_banned_field(customer_profile_id):
    conn = connect_to_database()
    cur = conn.cursor()

    sql = """UPDATE customer_profile SET is_banned=true WHERE telegram_user_id=%s RETURNING *;"""
    cur.execute(sql, (customer_profile_id,))

    updated_customer_profile = cur.fetchone()
    conn.commit()

    cur.close()
    if conn is not None:
        conn.close()
