import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent))

import streamlit as st
from datetime import date, datetime
from app.schema import init_db, list_categories, create_category, create_subcategory, add_expense, add_income, monthly_summary, expenses_frame, category_expected_for_month, export_month_csv
from app.models import Category, Subcategory
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Budget Dashboard", layout="wide")
init_db()

st.title("💸 Personal Budget Dashboard")

with st.sidebar:
    st.header("Quick actions")
    page = st.radio("Go to", ["Overview", "Add expense", "Add income", "Manage categories", "Export"])
    st.markdown("---")
    st.write("Tip: expected = planned (bills you know about). Real = actual spending.")

# --- Overview ---
if page == "Overview":
    today = date.today()
    year = st.number_input("Year", value=today.year, min_value=2000, max_value=2100)
    month = st.number_input("Month", value=today.month, min_value=1, max_value=12)
    if st.button("Load summary"):
        s = monthly_summary(year, month)
        st.metric("Incomes", f"€ {s['incomes']:.2f}")
        st.metric("Real expenses", f"€ {s['real_expenses']:.2f}")
        st.metric("Expected (planned)", f"€ {s['expected_expenses']:.2f}")
        balance = s['incomes'] - s['real_expenses']
        st.subheader(f"Net (income - real): € {balance:.2f}")
        # breakdown by category
        df = pd.DataFrame([
            {"category": k, "real": v.get("real", 0.0), "expected": v.get("expected", 0.0)}
            for k, v in s["by_category"].items()
        ])
        if not df.empty:
            st.subheader("Category breakdown")
            st.dataframe(df)
            # simple bar plot: real vs expected
            fig, ax = plt.subplots(figsize=(8,4))
            x = df['category']
            ax.bar(x, df['real'], label="real")
            ax.bar(x, df['expected'], bottom=df['real'], label="expected (stacked)")
            ax.set_ylabel("€")
            ax.set_xticklabels(x, rotation=45, ha="right")
            ax.legend()
            st.pyplot(fig)
        else:
            st.info("No expenses recorded this month.")

# --- Add expense ---
elif page == "Add expense":
    st.header("Add a new expense")
    d = st.date_input("Date", value=date.today())
    cats = list_categories()
    cat_map = {c.name: c for c in cats}
    cat_options = ["-- add new category --"] + [c.name for c in cats]
    cat_choice = st.selectbox("Category", cat_options)
    if cat_choice == "-- add new category --":
        new_name = st.text_input("New category name")
        new_desc = st.text_area("Description (optional)")
        if st.button("Create category"):
            if new_name.strip():
                create_category(new_name, new_desc)
                st.success("Category created. Reload the page in the sidebar to see it.")
    else:
        selected_cat = cat_map[cat_choice]
        # load subcategories
        subcats = selected_cat.subcategories
        sc_options = ["(none)"] + [sc.name for sc in subcats]
        sc_choice = st.selectbox("Subcategory (optional)", sc_options)
        if sc_choice == "(none)":
            subcat_id = None
        else:
            subcat_id = next((sc.id for sc in subcats if sc.name == sc_choice), None)
        amount = st.number_input("Amount (€)", min_value=0.0, value=0.0, format="%.2f")
        description = st.text_area("Description")
        exp_flag = st.checkbox("Expected (planned) expense?", value=False)
        if st.button("Add expense"):
            add_expense(d, float(amount), selected_cat.id, subcategory_id=subcat_id, description=description, expected=exp_flag)
            st.success("Expense added.")

# --- Add income ---
elif page == "Add income":
    st.header("Add income (salary, freelancing)")
    d = st.date_input("Date", value=date.today())
    amount = st.number_input("Amount (€)", min_value=0.0, value=0.0, format="%.2f")
    description = st.text_input("Description")
    if st.button("Add income"):
        add_income(d, float(amount), description)
        st.success("Income added.")

# --- Manage categories ---
elif page == "Manage categories":
    st.header("Categories & subcategories")
    cats = list_categories()
    for c in cats:
        with st.expander(c.name):
            st.write(c.description)
            subnames = [f"- {sc.name} (labels: {sc.labels})" for sc in c.subcategories] or ["(no subcategories)"]
            st.write("\n".join(subnames))
    st.subheader("Create new subcategory")
    new_cat = st.selectbox("Parent category", [c.name for c in cats])
    sc_name = st.text_input("Subcategory name")
    sc_labels = st.text_input("Labels (comma separated) — NOTE: labels only apply to subcategories")
    if st.button("Create subcategory"):
        parent = next((c for c in cats if c.name == new_cat), None)
        if parent:
            create_subcategory(parent.id, sc_name, labels=[l.strip() for l in sc_labels.split(",") if l.strip()])
            st.success("Subcategory created.")

# --- Export ---
elif page == "Export":
    st.header("Export & downloads")
    today = date.today()
    year = st.number_input("Year", value=today.year, min_value=2000, max_value=2100, key="exp_year")
    month = st.number_input("Month", value=today.month, min_value=1, max_value=12, key="exp_month")
    if st.button("Export CSV for month"):
        path = export_month_csv(year, month, f"expenses_{year}_{month:02d}.csv")
        with open(path, "rb") as f:
            st.download_button(label="Download CSV", data=f, file_name=f"expenses_{year}_{month:02d}.csv")
        st.success("CSV generated.")

