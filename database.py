import config
import mysql.connector as mc


class DB:
    def __init__(self):
        self.conn = self.connect()
        self.EscortUsers: EscortUsers = EscortUsers(self)
        self.Subscriptions: Subscriptions = Subscriptions(self)
        self.Models: Models = Models(self)
        self.Feedbacks: Feedbacks = Feedbacks(self)
        self.Workers: Workers = Workers(self)
        self.TopUp: TopUp = TopUp(self)
        self.ETopUp: ETopUp = ETopUp(self)

    @staticmethod
    def connect():
        return mc.connect(
            host=config.HOST,
            user=config.USER,
            password=config.PASSWORD,
            database=config.DATABASE
        )

    def get_cursor(self):
        return self.conn.cursor()


class EscortUsers:
    def __init__(self, db: DB):
        self.db = db

    def get_user_data(self, id_telegram: int) -> tuple:
        self.db.conn.close()
        self.db.conn = self.db.connect()
        cur = self.db.get_cursor()

        cur.execute("""
            SELECT balance, reg_date, subscription, currency, min_dep FROM escort_users WHERE id_telegram = %d;
        """ % id_telegram)
        data = cur.fetchone()
        cur.close()

        return data

    def get_user_mamont(self, id_telegram: int) -> tuple:
        self.db.conn.close()
        self.db.conn = self.db.connect()
        cur = self.db.get_cursor()

        cur.execute("""
            SELECT ref_code FROM escort_users WHERE id_telegram = %d;
        """ % id_telegram)
        ref_code = cur.fetchone()[0]

        if ref_code is None:
            return "Отсутствует", ""

        cur.execute("""
            SELECT nickname FROM users WHERE referal_code = "%s";
        """ % ref_code)
        worker = cur.fetchone()[0]
        cur.close()

        return "@" + worker, ref_code

    def get_ref_code(self, id_telegram: int) -> str:
        self.db.conn.close()
        self.db.conn = self.db.connect()
        cur = self.db.get_cursor()

        cur.execute("""
            SELECT ref_code FROM escort_users WHERE id_telegram = %d;
        """ % id_telegram)
        ref_code = cur.fetchone()[0]
        cur.close()

        return ref_code

    def is_user_exist(self, id_telegram: int) -> bool:
        self.db.conn.close()
        self.db.conn = self.db.connect()
        cur = self.db.get_cursor()

        cur.execute("""
            SELECT COUNT(*) FROM escort_users WHERE id_telegram = %d;
        """ % id_telegram)
        count = cur.fetchone()[0]
        cur.close()

        return True if count else False

    def is_higher_subscription(self, id_telegram: int, active_sub: int) -> bool:
        self.db.conn.close()
        self.db.conn = self.db.connect()
        cur = self.db.get_cursor()

        cur.execute("""
            SELECT subscription FROM escort_users WHERE id_telegram = %d;
        """ % id_telegram)
        subscription = cur.fetchone()[0]
        cur.close()

        return True if subscription >= active_sub else False

    def insert_user(self, id_telegram: int, ref_code: str = None):
        self.db.conn.close()
        self.db.conn = self.db.connect()
        cur = self.db.get_cursor()

        cur.execute("""
            INSERT INTO escort_users (id_telegram, ref_code)
            SELECT %s, %s
            FROM dual
            WHERE NOT EXISTS (SELECT 1 FROM escort_users WHERE id_telegram = %s);
        """, (id_telegram, ref_code, id_telegram))
        self.db.conn.commit()
        cur.close()

    def change_currency(self, id_telegram: int, currency: str):
        self.db.conn.close()
        self.db.conn = self.db.connect()
        cur = self.db.get_cursor()

        cur.execute("""
            UPDATE escort_users SET currency = "%s" WHERE id_telegram = %d;
        """ % (currency, id_telegram))
        self.db.conn.commit()
        cur.close()

    def change_subscription(self, id_telegram: int, new_balance: float, subscription: int):
        self.db.conn.close()
        self.db.conn = self.db.connect()
        cur = self.db.get_cursor()

        cur.execute("""
            UPDATE escort_users SET balance = %d, subscription = %d WHERE id_telegram = %d;
        """ % (new_balance, subscription, id_telegram))
        self.db.conn.commit()
        cur.close()

    def set_subscription(self, id_telegram: int, subscription: int):
        self.db.conn.close()
        self.db.conn = self.db.connect()
        cur = self.db.get_cursor()

        cur.execute("""
            UPDATE escort_users SET subscription = %s WHERE id_telegram = %s;
        """, (subscription, id_telegram))
        self.db.conn.commit()
        cur.close()

    def change_balance(self, id_telegram: int, new_balance: float):
        self.db.conn.close()
        self.db.conn = self.db.connect()
        cur = self.db.get_cursor()

        cur.execute("""
            UPDATE escort_users SET balance = balance - %d WHERE id_telegram = %d;
        """ % (new_balance, id_telegram))
        self.db.conn.commit()
        cur.close()

    def update_balance(self, id_telegram: int, balance: float):
        self.db.conn.close()
        self.db.conn = self.db.connect()
        cur = self.db.get_cursor()

        cur.execute("""
            UPDATE escort_users SET balance = balance + %d WHERE id_telegram = %d;
        """ % (balance, id_telegram))
        self.db.conn.commit()
        cur.close()

    def new_balance(self, id_telegram: int, balance: float):
        self.db.conn.close()
        self.db.conn = self.db.connect()
        cur = self.db.get_cursor()

        cur.execute("""
            UPDATE escort_users SET balance = %f WHERE id_telegram = %d;
        """ % (balance, id_telegram))
        self.db.conn.commit()
        cur.close()

    def set_ref_code(self, id_telegram: int, ref_code: str):
        self.db.conn.close()
        self.db.conn = self.db.connect()
        cur = self.db.get_cursor()

        cur.execute("""
            UPDATE escort_users SET ref_code = "%s" WHERE id_telegram = %d;
        """ % (ref_code, id_telegram))
        self.db.conn.commit()
        cur.close()

    def delete_user(self, id_telegram: int):
        self.db.conn.close()
        self.db.conn = self.db.connect()
        cur = self.db.get_cursor()

        cur.execute("""
            DELETE FROM escort_users WHERE id_telegram = %d;
        """ % id_telegram)
        self.db.conn.commit()
        cur.close()


class Workers:
    def __init__(self, db: DB):
        self.db = db

    def get_ref_codes(self) -> list:
        self.db.conn.close()
        self.db.conn = self.db.connect()
        cur = self.db.get_cursor()

        cur.execute("""
            SELECT referal_code FROM users;
        """)
        ref_codes = [ref_code[0] for ref_code in cur.fetchall()]
        cur.close()

        return ref_codes

    def get_id(self, ref_code: str) -> int:
        self.db.conn.close()
        self.db.conn = self.db.connect()
        cur = self.db.get_cursor()

        cur.execute("""
            SELECT id_telegram FROM users WHERE referal_code = "%s";
        """ % ref_code)
        id_telegram = cur.fetchone()[0]
        cur.close()

        return id_telegram

    def get_ids(self) -> list:
        self.db.conn.close()
        self.db.conn = self.db.connect()
        cur = self.db.get_cursor()

        cur.execute("""
            SELECT id_telegram FROM users;
        """)
        ids = [id_telegram[0] for id_telegram in cur.fetchall()]
        cur.close()

        return ids

    def get_mamonts(self, id_telegram: int) -> list:
        self.db.conn.close()
        self.db.conn = self.db.connect()
        cur = self.db.get_cursor()

        cur.execute("""
            SELECT referal_code FROM users WHERE id_telegram = %d;
        """ % id_telegram)
        ref_code = cur.fetchone()[0]

        cur.execute("""
            SELECT id_telegram, reg_date FROM escort_users WHERE ref_code = "%s";
        """ % ref_code)
        mamonts = cur.fetchall()
        cur.close()

        return mamonts


class Subscriptions:
    def __init__(self, db: DB):
        self.db = db

    def get_amount(self, sub: str):
        self.db.conn.close()
        self.db.conn = self.db.connect()
        cur = self.db.get_cursor()

        cur.execute("""
            SELECT %s FROM subscriptions;
        """ % sub)
        amount = cur.fetchone()[0]
        cur.close()

        return amount


class Models:
    def __init__(self, db: DB):
        self.db = db

    def get_worker_models(self, id_telegram: int) -> list:
        self.db.conn.close()
        self.db.conn = self.db.connect()
        cur = self.db.get_cursor()

        cur.execute("""
            SELECT id, name, age, city FROM models WHERE worker_id = %d;
        """ % id_telegram)
        models = cur.fetchall()
        cur.close()

        return models

    def get_model_data(self, model_id: str) -> tuple:
        self.db.conn.close()
        self.db.conn = self.db.connect()
        cur = self.db.get_cursor()

        cur.execute("""
            SELECT name, age, height, boobs_size, city, main_cost, add_cost, photo_one, photo_two, photo_three, 
            photo_four, photo_five, id
            FROM models WHERE id = "%s"; 
        """ % model_id)
        data = cur.fetchone()
        cur.close()

        return data

    def get_active_models(self, city: str) -> dict:
        self.db.conn.close()
        self.db.conn = self.db.connect()
        cur = self.db.get_cursor()

        cur.execute("""
            SELECT id, name, age FROM models WHERE city = "%s" AND is_active = true;
        """ % city)
        data = cur.fetchall()
        models = {model[0]: "%s (%d)" % (model[1], model[2]) for model in data}
        cur.close()

        return models

    def get_model_city(self, model_id: str) -> str:
        self.db.conn.close()
        self.db.conn = self.db.connect()
        cur = self.db.get_cursor()

        cur.execute("""
            SELECT city FROM models WHERE id = "%s";
        """ % model_id)
        city = cur.fetchone()[0]
        cur.close()

        return city

    def insert_new_model(self, data: list):
        self.db.conn.close()
        self.db.conn = self.db.connect()
        cur = self.db.get_cursor()

        model_id = data[0]
        name = data[1]
        age = int(data[2])
        height = int(data[3])
        boobs_size = int(data[4])
        city = data[5]
        main_cost = data[6]
        add_cost = data[7]
        photo_one = data[8]
        photo_two = data[9]
        photo_three = data[10]
        photo_four = data[11]
        photo_five = data[12]
        worker_id = data[13]

        cur.execute("""
            INSERT INTO models (id, name, age, height, boobs_size, city, main_cost, add_cost, photo_one, photo_two, photo_three, photo_four, photo_five, worker_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """, (model_id, name, age, height, boobs_size, city, main_cost, add_cost, photo_one, photo_two,
              photo_three, photo_four, photo_five, worker_id))
        self.db.conn.commit()
        cur.close()

    def delete_model(self, model_code: str):
        self.db.conn.close()
        self.db.conn = self.db.connect()
        cur = self.db.get_cursor()

        cur.execute("""
            DELETE FROM models WHERE id = "%s";
        """ % model_code)
        self.db.conn.commit()
        cur.close()


class Feedbacks:
    def __init__(self, db: DB):
        self.db = db

    def get_feedbacks(self) -> dict:
        self.db.conn.close()
        self.db.conn = self.db.connect()
        cur = self.db.get_cursor()

        cur.execute("""
            SELECT * FROM feedbacks;
        """)
        data = cur.fetchall()
        cur.close()

        return {feedback[1]: feedback[0] for feedback in data}

    def create_feedback(self, photo: str, text: str):
        self.db.conn.close()
        self.db.conn = self.db.connect()
        cur = self.db.get_cursor()

        cur.execute("""
            INSERT INTO feedbacks (photo, model)
            VALUES (%s, %s)
        """, (photo, text))
        self.db.conn.commit()
        cur.close()


class TopUp:
    def __init__(self, db: DB):
        self.db = db

    def get_data(self, unique_id: str) -> tuple:
        self.db.conn.close()
        self.db.conn = self.db.connect()
        cur = self.db.get_cursor()

        cur.execute("""
            SELECT mamont_id, requisite, amount FROM escort_topup WHERE unique_id = "%s";
        """ % unique_id)
        data = cur.fetchone()
        cur.close()

        return data

    def get_all_data(self, unique_id: str) -> tuple:
        self.db.conn.close()
        self.db.conn = self.db.connect()
        cur = self.db.get_cursor()

        cur.execute("""
            SELECT mamont_id, amount, is_complete FROM escort_topup WHERE unique_id = "%s";
        """ % unique_id)
        data = cur.fetchone()
        cur.close()

        return data

    def insert_new_application(self, unique_id: int, mamont_id: int, method: str, requisite: str, amount: float,
                               username: str):
        cur = self.db.get_cursor()

        cur.execute("""
            INSERT INTO escort_topup (unique_id, mamont_id, method, requisite, amount, nickname)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (unique_id, mamont_id, method, requisite, amount, username))
        self.db.conn.commit()
        cur.close()


class ETopUp:
    def __init__(self, db: DB):
        self.db = db

    def accept(self, unique_id: str):
        self.db.conn.close()
        self.db.conn = self.db.connect()
        cur = self.db.get_cursor()

        cur.execute("""
            UPDATE escort_topup SET is_complete = 1 WHERE unique_id = %s;
        """, (unique_id,))
        self.db.conn.commit()

        cur.close()

    def cancel(self, unique_id: str):
        self.db.conn.close()
        self.db.conn = self.db.connect()
        cur = self.db.get_cursor()

        cur.execute("""
            UPDATE escort_topup SET is_complete = 2 WHERE unique_id = %s;
        """, (unique_id,))
        self.db.conn.commit()

        cur.close()
