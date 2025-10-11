import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import argparse
from datetime import datetime, date
from app.schema import init_db, create_category, create_subcategory, add_expense, add_income, list_categories, get_category_by_name
from app.db import get_session

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--init-db", action="store_true")
    p.add_argument("--add-cat", nargs=1)
    p.add_argument("--add-subcat", nargs=2, metavar=("CATEGORY", "SUBNAME"))
    p.add_argument("--add-expense", nargs=4, metavar=("DATE", "AMOUNT", "CATEGORY", "EXPECTED"))
    p.add_argument("--add-income", nargs=2, metavar=("DATE","AMOUNT"))
    return p.parse_args()

def main():
    args = parse_args()
    if args.init_db:
        init_db()
        print("DB initialized.")
    if args.add_cat:
        name = args.add_cat[0]
        create_category(name)
        print("Category created:", name)
    if args.add_subcat:
        catname, subname = args.add_subcat
        c = get_category_by_name(catname)
        if not c:
            print("Category not found:", catname)
            return
        create_subcategory(c.id, subname)
        print("Subcategory created:", subname, "in", catname)
    if args.add_expense:
        dstr, amount, catname, expected_str = args.add_expense
        d = datetime.strptime(dstr, "%Y-%m-%d").date()
        amount = float(amount)
        expected = expected_str.lower() in ("1","true","yes","y")
        c = get_category_by_name(catname)
        if not c:
            print("Category not found:", catname)
            return
        add_expense(d, amount, c.id, expected=expected)
        print("Expense added.")
    if args.add_income:
        dstr, amount = args.add_income
        d = datetime.strptime(dstr, "%Y-%m-%d").date()
        amount = float(amount)
        add_income(d, amount)
        print("Income added.")
if __name__ == "__main__":
    main()

