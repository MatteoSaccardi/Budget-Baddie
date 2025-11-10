import sqlite3
from datetime import date
import pandas as pd
import json
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "budget.db")

# -------------------------------
# DATABASE INITIALIZATION
# -------------------------------
def init_db():
    """Initialize the database and create all required tables."""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()

        # Categories
        cur.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                recurrent BOOLEAN DEFAULT 0,
                expected_monthly REAL DEFAULT 0.0
            )
        """)

        # Subcategories
        cur.execute("""
            CREATE TABLE IF NOT EXISTS subcategories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                labels TEXT,
                FOREIGN KEY(category_id) REFERENCES categories(id)
            )
        """)

        # Expenses — added 'currency'
        cur.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                category_id INTEGER,
                subcategory_id INTEGER,
                description TEXT,
                expected BOOLEAN DEFAULT 0,
                currency TEXT DEFAULT 'EUR',
                FOREIGN KEY(category_id) REFERENCES categories(id),
                FOREIGN KEY(subcategory_id) REFERENCES subcategories(id)
            )
        """)

        # Income — added 'currency'
        cur.execute("""
            CREATE TABLE IF NOT EXISTS income (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                category_id INTEGER,
                subcategory_id INTEGER,
                description TEXT,
                currency TEXT DEFAULT 'EUR',
                FOREIGN KEY(category_id) REFERENCES categories(id),
                FOREIGN KEY(subcategory_id) REFERENCES subcategories(id)
            )
        """)

        conn.commit()


# -------------------------------
# CATEGORY FUNCTIONS
# -------------------------------
def create_category(name, description="", recurrent=False, expected_monthly=0.0):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO categories (name, description, recurrent, expected_monthly) VALUES (?, ?, ?, ?)",
            (name, description, recurrent, expected_monthly)
        )
        conn.commit()

def update_category(category_id, name, description, recurrent, expected_monthly):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            UPDATE categories 
            SET name=?, description=?, recurrent=?, expected_monthly=? 
            WHERE id=?
        """, (name, description, recurrent, expected_monthly, category_id))
        conn.commit()

def delete_category(category_id):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM subcategories WHERE category_id=?", (category_id,))
        conn.execute("DELETE FROM categories WHERE id=?", (category_id,))
        conn.commit()

def list_categories():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cats = conn.execute("SELECT * FROM categories").fetchall()

        result = []
        for c in cats:
            subs = conn.execute("SELECT * FROM subcategories WHERE category_id=?", (c["id"],)).fetchall()
            result.append({
                "id": c["id"],
                "name": c["name"],
                "description": c["description"],
                "recurrent": bool(c["recurrent"]),
                "expected_monthly": c["expected_monthly"],
                "subcategories": [dict(s) for s in subs]
            })
        return result

# -------------------------------
# SUBCATEGORY FUNCTIONS
# -------------------------------
def create_subcategory(category_id, name, description="", labels=None):
    labels_json = json.dumps(labels or [])
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            INSERT INTO subcategories (category_id, name, description, labels)
            VALUES (?, ?, ?, ?)
        """, (category_id, name, description, labels_json))
        conn.commit()

def update_subcategory(subcategory_id, name, description):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            UPDATE subcategories SET name=?, description=? WHERE id=?
        """, (name, description, subcategory_id))
        conn.commit()

def delete_subcategory(subcategory_id):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM subcategories WHERE id=?", (subcategory_id,))
        conn.commit()

# -------------------------------
# EXPENSE FUNCTIONS
# -------------------------------
def add_expense(exp_date, amount, category_id, subcategory_id, description, expected=False, currency="EUR"):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            INSERT INTO expenses (date, amount, category_id, subcategory_id, description, expected, currency)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (exp_date.isoformat(), amount, category_id, subcategory_id, description, expected, currency))
        conn.commit()


def update_expense(expense_id, exp_date, amount, category_id, subcategory_id, description, expected, currency="EUR"):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            UPDATE expenses 
            SET date=?, amount=?, category_id=?, subcategory_id=?, description=?, expected=?, currency=?
            WHERE id=?
        """, (exp_date.isoformat(), amount, category_id, subcategory_id, description, expected, currency, expense_id))
        conn.commit()

def delete_expense(expense_id):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM expenses WHERE id=?", (expense_id,))
        conn.commit()

def list_recent_expenses(limit=20):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("""
            SELECT e.id, e.date, e.amount, e.currency, c.name as category, s.name as subcategory, e.description, e.expected
            FROM expenses e
            LEFT JOIN categories c ON e.category_id = c.id
            LEFT JOIN subcategories s ON e.subcategory_id = s.id
            ORDER BY e.date DESC
            LIMIT ?
        """, (limit,)).fetchall()
        return [dict(r) for r in rows]

def expenses_frame(year=None, month=None):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        query = """
            SELECT e.date, e.amount, c.name as category, s.name as subcategory, e.description, e.expected
            FROM expenses e
            LEFT JOIN categories c ON e.category_id = c.id
            LEFT JOIN subcategories s ON e.subcategory_id = s.id
        """
        params = []
        if year and month:
            query += " WHERE strftime('%Y', e.date)=? AND strftime('%m', e.date)=?"
            params = [str(year), f"{month:02d}"]
        elif year:
            query += " WHERE strftime('%Y', e.date)=?"
            params = [str(year)]

        df = pd.read_sql_query(query, conn, params=params)
        return df

# -------------------------------
# INCOME FUNCTIONS
# -------------------------------
def add_income(inc_date, amount, category_id, subcategory_id, description, currency="EUR"):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            INSERT INTO income (date, amount, category_id, subcategory_id, description, currency)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (inc_date.isoformat(), amount, category_id, subcategory_id, description, currency))
        conn.commit()


def update_income(income_id, inc_date, amount, category_id, subcategory_id, description, currency="EUR"):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            UPDATE income 
            SET date=?, amount=?, category_id=?, subcategory_id=?, description=?, currency=? 
            WHERE id=?
        """, (inc_date.isoformat(), amount, category_id, subcategory_id, description, currency, income_id))
        conn.commit()

def delete_income(income_id):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM income WHERE id=?", (income_id,))
        conn.commit()

def list_incomes(limit=20):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("""
            SELECT i.id, i.date, i.amount, i.currency, c.name as category, s.name as subcategory, i.description
            FROM income i
            LEFT JOIN categories c ON i.category_id = c.id
            LEFT JOIN subcategories s ON i.subcategory_id = s.id
            ORDER BY i.date DESC
            LIMIT ?
        """, (limit,)).fetchall()
        return [dict(r) for r in rows]

