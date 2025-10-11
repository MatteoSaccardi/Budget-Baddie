import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.db import engine, get_session
from app.models import Base, Category, Subcategory, Expense, Income, MonthlyBudget
from sqlalchemy import func, extract, and_
from datetime import date, datetime
import pandas as pd
from typing import Optional, List

def init_db():
    Base.metadata.create_all(bind=engine)

# Category helpers
def create_category(name: str, description: str = "") -> Category:
    s = get_session()
    c = Category(name=name.strip(), description=description)
    s.add(c)
    s.commit()
    s.refresh(c)
    s.close()
    return c

def create_subcategory(category_id: int, name: str, description: str = "", labels: Optional[List[str]] = None) -> Subcategory:
    s = get_session()
    sc = Subcategory(category_id=category_id, name=name.strip(), description=description, labels=",".join(labels or []))
    s.add(sc)
    s.commit()
    s.refresh(sc)
    s.close()
    return sc

def list_categories():
    s = get_session()
    cats = s.query(Category).all()
    s.close()
    return cats

def get_category_by_name(name: str):
    s = get_session()
    c = s.query(Category).filter(func.lower(Category.name) == name.lower()).first()
    s.close()
    return c

# Expense / Income
def add_expense(d: date, amount: float, category_id: int, subcategory_id: Optional[int] = None,
                description: str = "", expected: bool = False) -> Expense:
    s = get_session()
    e = Expense(date=d, amount=amount, category_id=category_id, subcategory_id=subcategory_id,
                description=description, expected=expected)
    s.add(e)
    s.commit()
    s.refresh(e)
    s.close()
    return e

def add_income(d: date, amount: float, description: str = "") -> Income:
    s = get_session()
    inc = Income(date=d, amount=amount, description=description)
    s.add(inc)
    s.commit()
    s.refresh(inc)
    s.close()
    return inc

# Monthly queries
def expenses_frame(year: int, month: int, include_expected: bool = True, include_real: bool = True) -> pd.DataFrame:
    s = get_session()
    q = s.query(Expense, Category.name.label("category"), Subcategory.name.label("subcategory")).join(Category).outerjoin(Subcategory)
    q = q.filter(extract("year", Expense.date) == year, extract("month", Expense.date) == month)
    df = pd.DataFrame(
        [{
            "id": e.Expense.id,
            "date": e.Expense.date,
            "amount": e.Expense.amount,
            "description": e.Expense.description,
            "category": e.category,
            "subcategory": e.subcategory,
            "expected": e.Expense.expected
        } for e in q]
    )
    s.close()
    return df

def monthly_summary(year: int, month: int) -> dict:
    s = get_session()
    # incomes
    incomes = s.query(func.sum(Income.amount)).filter(extract("year", Income.date) == year, extract("month", Income.date) == month).scalar() or 0.0
    # expenses real
    real = s.query(func.sum(Expense.amount)).filter(extract("year", Expense.date) == year, extract("month", Expense.date) == month, Expense.expected == False).scalar() or 0.0
    expected = s.query(func.sum(Expense.amount)).filter(extract("year", Expense.date) == year, extract("month", Expense.date) == month, Expense.expected == True).scalar() or 0.0
    # breakdown by category (real + expected)
    cat_q = s.query(Category.name, func.sum(Expense.amount).label("total"), Expense.expected).join(Expense).filter(extract("year", Expense.date) == year, extract("month", Expense.date) == month).group_by(Category.name, Expense.expected).all()
    breakdown = {}
    for name, total, exp_flag in cat_q:
        if name not in breakdown: breakdown[name] = {"real": 0.0, "expected": 0.0}
        if exp_flag:
            breakdown[name]["expected"] = float(total)
        else:
            breakdown[name]["real"] = float(total)
    s.close()
    return {"incomes": float(incomes), "real_expenses": float(real), "expected_expenses": float(expected), "by_category": breakdown}

def category_expected_for_month(year: int, month: int):
    s = get_session()
    rows = s.query(MonthlyBudget, Category.name).join(Category).filter(MonthlyBudget.year==year, MonthlyBudget.month==month).all()
    s.close()
    return [{"category": r[1], "expected": r[0].expected_amount} for r in rows]

# Utility exports
def export_month_csv(year: int, month: int, path: str):
    df = expenses_frame(year, month)
    df.to_csv(path, index=False)
    return path

