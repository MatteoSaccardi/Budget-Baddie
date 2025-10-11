import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.db import engine, get_session
from app.models import Base, Category, Subcategory, Expense, Income, MonthlyBudget
from sqlalchemy import func, extract
from sqlalchemy.orm import joinedload, aliased
from datetime import date
import pandas as pd
from typing import Optional, List

def init_db():
    Base.metadata.create_all(bind=engine)

# -------------------------------
# Category helpers
# -------------------------------

def create_category(name: str, description: str = "", recurrent: bool = False, expected_monthly: float = 0.0) -> Category:
    s = get_session()
    c = Category(name=name.strip(), description=description, recurrent=recurrent, expected_monthly=expected_monthly)
    s.add(c)
    s.commit()
    s.refresh(c)
    s.close()
    return c

def update_category(category_id: int, name: str = None, description: str = None,
                    recurrent: bool = None, expected_monthly: float = None):
    s = get_session()
    c = s.query(Category).get(category_id)
    if not c:
        s.close()
        return False
    if name is not None:
        c.name = name.strip()
    if description is not None:
        c.description = description
    if recurrent is not None:
        c.recurrent = recurrent
    if expected_monthly is not None:
        c.expected_monthly = expected_monthly
    s.commit()
    s.close()
    return True

def create_subcategory(category_id: int, name: str, description: str = "", labels: Optional[List[str]] = None) -> Subcategory:
    s = get_session()
    sc = Subcategory(category_id=category_id, name=name.strip(), description=description, labels=",".join(labels or []))
    s.add(sc)
    s.commit()
    s.refresh(sc)
    s.close()
    return sc

def list_categories():
    with get_session() as s:
        cats = s.query(Category).options(joinedload(Category.subcategories)).all()
        return [
            {
                "id": c.id,
                "name": c.name,
                "description": c.description,
                "recurrent": c.recurrent,
                "expected_monthly": c.expected_monthly,
                "subcategories": [
                    {
                        "id": sc.id,
                        "name": sc.name,
                        "description": sc.description,
                        "labels": sc.labels,
                    }
                    for sc in c.subcategories
                ],
            }
            for c in cats
        ]

# -------------------------------
# Expense / Income
# -------------------------------

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

def update_subcategory(subcategory_id: int, name: str = None, description: str = None, labels: list = None):
    s = get_session()
    sc = s.query(Subcategory).get(subcategory_id)
    if not sc:
        s.close()
        return False
    if name is not None:
        sc.name = name.strip()
    if description is not None:
        sc.description = description
    if labels is not None:
        sc.labels = ",".join(labels)
    s.commit()
    s.close()
    return True

# -------------------------------
# Monthly / Summary
# -------------------------------

def expenses_frame(year: int, month: int) -> pd.DataFrame:
    s = get_session()
    Cat = aliased(Category)
    Sub = aliased(Subcategory)
    q = (
        s.query(
            Expense,
            Cat.name.label("category"),
            Sub.name.label("subcategory")
        )
        .join(Cat, Expense.category_id == Cat.id)
        .outerjoin(Sub, Expense.subcategory_id == Sub.id)
        .filter(extract("year", Expense.date) == year, extract("month", Expense.date) == month)
    )
    df = pd.DataFrame([{
        "id": e.Expense.id,
        "date": e.Expense.date,
        "amount": e.Expense.amount,
        "description": e.Expense.description,
        "category": e.category,
        "subcategory": e.subcategory,
        "expected": e.Expense.expected
    } for e in q])
    s.close()
    return df

def list_recent_expenses(limit: int = 10, include_expected: bool = True):
    s = get_session()
    from sqlalchemy.orm import aliased

    Cat = aliased(Category)
    Sub = aliased(Subcategory)

    q = s.query(
        Expense,
        Cat.name.label("category"),
        Sub.name.label("subcategory")
    ).select_from(Expense) \
     .join(Cat, Expense.category_id == Cat.id) \
     .outerjoin(Sub, Expense.subcategory_id == Sub.id) \
     .order_by(Expense.date.desc(), Expense.id.desc())

    if not include_expected:
        q = q.filter(Expense.expected == False)

    q = q.limit(limit)
    result = [{
        "id": e.Expense.id,
        "date": e.Expense.date,
        "amount": e.Expense.amount,
        "description": e.Expense.description,
        "category": e.category,
        "subcategory": e.subcategory,
        "expected": e.Expense.expected
    } for e in q]
    s.close()
    return result

