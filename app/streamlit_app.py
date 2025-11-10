import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
import calendar
import requests
import os
import shutil

from app.schema import (
    init_db, list_categories, create_category, update_category, delete_category,
    create_subcategory, update_subcategory, delete_subcategory,
    add_expense, add_income, delete_expense, delete_income,
    expenses_frame, list_recent_expenses, list_incomes, update_expense, update_income
)

# -------------------------------
# HELPER FUNCTIONS
# -------------------------------
def get_cats_dict():
    cats = list_categories()
    return {c["name"]: c["id"] for c in cats}

from app.schema import DB_PATH

def backup_db():
    backup_path = os.path.join(os.path.dirname(DB_PATH), "budget_backup.db")
    if os.path.exists(DB_PATH):
        shutil.copyfile(DB_PATH, backup_path)
        print(f"Database backed up to {backup_path}")
    else:
        print("No database file to backup.")

# -------------------------------
# Currency utilities
# -------------------------------
@st.cache_data(ttl=3600)
def fetch_rates(base="EUR", targets=["EUR", "USD", "GBP"]):
    try:
        url = f"https://api.exchangerate.host/latest?base={base}"
        resp = requests.get(url, timeout=5)
        data = resp.json()
        rates = {cur: data["rates"].get(cur, None) for cur in targets}
    except Exception:
        rates = {"EUR": 1.0, "USD": 1.1, "GBP": 0.85}
    return rates

def currency_selector():
    st.sidebar.markdown("### 💱 Currency Settings")

    base = "EUR"
    targets = ["EUR", "USD", "GBP"]
    rates = fetch_rates(base, targets)

    display_currency = st.sidebar.selectbox("Display currency", targets, index=0)
    st.sidebar.caption("Live rates from exchangerate.host")

    st.sidebar.write("Override rates (optional):")
    user_rate_USD = st.sidebar.number_input("EUR → USD", value=rates.get("USD", 1.1), format="%.4f")
    user_rate_GBP = st.sidebar.number_input("EUR → GBP", value=rates.get("GBP", 0.85), format="%.4f")

    rates["USD"] = user_rate_USD
    rates["GBP"] = user_rate_GBP
    rates["EUR"] = 1.0

    return display_currency, rates

def convert_value(amount, from_currency, to_currency, rates):
    if from_currency == to_currency:
        return amount
    try:
        eur_amount = amount / rates.get(from_currency, 1.0)
        return eur_amount * rates.get(to_currency, 1.0)
    except Exception:
        return amount

def to_display_currency(amount, row_currency, target_currency, rates):
    """Convert amount from row_currency to target_currency using rates dict."""
    if row_currency == target_currency:
        return amount
    else:
        # Convert to EUR first, then to target
        eur_amount = amount / rates.get(row_currency, 1)
        return eur_amount * rates.get(target_currency, 1)

# -------------------------------
# Setup
# -------------------------------

BASE_DIR = os.path.dirname(__file__)
st.set_page_config(page_title="Budget Baddie", layout="wide")
init_db()
today = date.today()
# Backup DB on start
backup_db()

# -------------------------------
# Sidebar navigation
# -------------------------------
st.sidebar.title("Budget Baddie")
page = st.sidebar.radio("Go to page", [
    "Overview",
    "Manage Expenses & Income",
    "Manage Categories",
    "Export Data"
])
display_currency, rates = currency_selector()

# -------------------------------
# PAGE: OVERVIEW
# -------------------------------
if page == "Overview":
    st.title("💸 Overview")

    # Recent Expenses
    st.header("🧾 Recent Expenses")
    recent_exp = pd.DataFrame(list_recent_expenses(limit=10))
    if not recent_exp.empty:
        recent_exp["Converted amount"] = recent_exp.apply(
            lambda r: convert_value(r["amount"], r.get("currency", "EUR"), display_currency, rates), axis=1
        )
        recent_exp.rename(columns={
            "amount": f"Amount ({recent_exp.get('currency', 'EUR').iloc[0] if 'currency' in recent_exp else 'EUR'})",
            "Converted amount": f"Converted amount ({display_currency})"
        }, inplace=True)
        st.dataframe(recent_exp)
    else:
        st.info("No recent expenses yet.")

    # Recent Income
    st.header("💰 Recent Income")
    recent_inc = pd.DataFrame(list_incomes(limit=10))
    if not recent_inc.empty:
        recent_inc["Converted amount"] = recent_inc.apply(
            lambda r: convert_value(r["amount"], r.get("currency", "EUR"), display_currency, rates), axis=1
        )
        recent_inc.rename(columns={
            "amount": f"Amount ({recent_inc.get('currency', 'EUR').iloc[0] if 'currency' in recent_inc else 'EUR'})",
            "Converted amount": f"Converted amount ({display_currency})"
        }, inplace=True)
        st.dataframe(recent_inc)
    else:
        st.info("No recent income yet.")

    # Expense Overview
    st.header("📊 Expense Overview")
    today = date.today()
    all_years = list(range(today.year - 5, today.year + 1))
    selected_years = st.multiselect("Select year(s)", all_years, default=[today.year])

    df = pd.DataFrame()
    month_to_num = {name: i for i, name in enumerate(list(calendar.month_name)[1:], start=1)}

    selected_months = ["All"]
    for year in selected_years:
        month_nums = list(range(1, 13)) if "All" in selected_months else [month_to_num[m] for m in selected_months]
        for month in month_nums:
            df = pd.concat([df, expenses_frame(year, month)], ignore_index=True)

    if df.empty:
        st.warning("No expenses for selected period.")
    else:
        df["Converted amount"] = df.apply(
            lambda r: convert_value(r["amount"], r.get("currency", "EUR"), display_currency, rates), axis=1
        )
        df.rename(columns={
            "amount": f"Amount ({df.get('currency', 'EUR').iloc[0] if 'currency' in df else 'EUR'})",
            "Converted amount": f"Converted amount ({display_currency})"
        }, inplace=True)
        st.dataframe(df)

        # Pie chart by category
        by_cat = df.groupby("category")[f"Converted amount ({display_currency})"].sum().reset_index()
        fig_cat = px.pie(by_cat, names="category", values=f"Converted amount ({display_currency})",
                         title=f"Expenses by Category ({display_currency})")
        st.plotly_chart(fig_cat, use_container_width=True)

        # Income vs Expenses
        st.header("💵 Income vs Expenses Overview")

        incomes = pd.DataFrame(list_incomes(limit=1000))
        if not incomes.empty:
            incomes["Converted amount"] = incomes.apply(
                lambda r: convert_value(r["amount"], r.get("currency", "EUR"), display_currency, rates), axis=1
            )
            total_income = incomes["Converted amount"].sum()
        else:
            total_income = 0.0

        df["is_emergency"] = df["category"].apply(lambda x: str(x).lower().strip() == "unexpected / emergencies")
        total_emergency = df[df["is_emergency"]][f"Converted amount ({display_currency})"].sum()
        total_other_exp = df[~df["is_emergency"]][f"Converted amount ({display_currency})"].sum()

        summary_df = pd.DataFrame([
            {"Category": "Income", "Type": "Income", f"Amount ({display_currency})": total_income},
            {"Category": "Expenses", "Type": "Expected", f"Amount ({display_currency})": total_other_exp},
            {"Category": "Expenses", "Type": "Unexpected", f"Amount ({display_currency})": total_emergency},
        ])

        fig_income_exp = px.bar(
            summary_df,
            x="Category",
            y=f"Amount ({display_currency})",
            color="Type",
            text_auto=".2f",
            title=f"Income vs Expenses (Expected vs Unexpected) — {display_currency}",
        )
        fig_income_exp.update_layout(barmode="stack", legend_title_text="")
        st.plotly_chart(fig_income_exp, use_container_width=True)

        total_expenses = total_emergency + total_other_exp
        balance = total_income - total_expenses
        st.markdown(
            f"**💰 Total income:** {total_income:,.2f} {display_currency}  \n"
            f"**💸 Total expenses:** {total_expenses:,.2f} {display_currency}  "
            f"(_Expected: {total_other_exp:,.2f}, Unexpected: {total_emergency:,.2f}_)  \n\n"
            f"**⚖️ Net balance:** {balance:,.2f} {display_currency}  "
            + ("✅ Surplus" if balance >= 0 else "🚨 Deficit")
        )

# -------------------------------
# PAGE: MANAGE EXPENSES & INCOME
# -------------------------------
elif page == "Manage Expenses & Income":
    st.title("🧾 Manage Expenses & Income")

    # --- Add Expense ---
    st.header("Add / Edit Expense")
    cats = list_categories()
    if not cats:
        st.warning("No categories defined.")
    else:
        cat_map = {c["name"]: c["id"] for c in cats}
        cat_name = st.selectbox("Category", options=list(cat_map.keys()))
        cat_id = cat_map[cat_name]

        subs = {sc["name"]: sc["id"] for c in cats if c["id"] == cat_id for sc in c["subcategories"]}
        sub_name = st.selectbox("Subcategory", options=[""] + list(subs.keys()))
        sub_id = subs.get(sub_name) if sub_name else None

        exp_date = st.date_input("Date", value=today)
        exp_currency = st.selectbox("Currency", ["EUR", "USD", "GBP"], index=0)
        exp_amount = st.number_input(f"Amount ({exp_currency})", min_value=0.0, format="%.2f")
        desc = st.text_area("Description")
        expected = st.checkbox("Expected?")

        if st.button("Add Expense"):
            add_expense(exp_date, exp_amount, cat_id, sub_id, desc, expected, exp_currency)
            st.success("Expense added!")

    st.subheader("Edit/Delete Existing Expenses")
    expenses = pd.DataFrame(list_recent_expenses(limit=50))
    if expenses.empty:
        st.info("No expenses to edit.")
    else:
        for i, row in expenses.iterrows():
            with st.expander(f"🧾 {row['description']} — {row['amount']} {row.get('currency', 'EUR')}"):
                new_desc = st.text_input("Description", value=row["description"], key=f"exp_desc_{row['id']}")
                new_amount = st.number_input("Amount", value=float(row["amount"]), min_value=0.0, format="%.2f", key=f"exp_amt_{row['id']}")
                new_currency = st.selectbox(
                    "Currency",
                    ["EUR", "USD", "GBP"],
                    index=["EUR", "USD", "GBP"].index(row.get("currency", "EUR")),
                    key=f"exp_curr_{row['id']}"
                )

                # Category and subcategory
                cats_dict = get_cats_dict()
                new_cat_name = st.selectbox(
                    "Category",
                    options=list(cats_dict.keys()),
                    index=list(cats_dict.keys()).index(row["category"]),
                    key=f"exp_cat_{row['id']}"
                )
                new_cat_id = cats_dict[new_cat_name]

                subcategories = {sc["name"]: sc["id"] for c in list_categories() if c["id"] == new_cat_id for sc in c["subcategories"]}
                new_sub_name = st.selectbox(
                    "Subcategory (optional)",
                    options=[""] + list(subcategories.keys()),
                    index=([""] + list(subcategories.keys())).index(row["subcategory"]) if row["subcategory"] in subcategories else 0,
                    key=f"exp_sub_{row['id']}"
                )
                new_sub_id = subcategories.get(new_sub_name) if new_sub_name else None

                # Expected checkbox
                new_expected = st.checkbox("Expected (planned)?", value=bool(row.get("expected", False)), key=f"exp_expected_{row['id']}")

                new_date = st.date_input("Date", value=pd.to_datetime(row["date"]).date(), key=f"exp_date_{row['id']}")

                if st.button("Save changes", key=f"save_exp_{row['id']}"):
                    update_expense(
                        expense_id=row["id"],
                        exp_date=new_date,
                        amount=new_amount,
                        category_id=new_cat_id,
                        subcategory_id=new_sub_id,
                        description=new_desc,
                        expected=new_expected,
                        currency=new_currency
                    )
                    st.success("Expense updated!")

                if st.button("Delete", key=f"del_exp_{row['id']}"):
                    delete_expense(row["id"])
                    st.warning("Expense deleted!")

    st.markdown("---")

    st.subheader("Edit/Delete Existing Income")
    incomes = pd.DataFrame(list_incomes(limit=50))
    if incomes.empty:
        st.info("No income entries to edit.")
    else:
        cats_dict = get_cats_dict()
        for i, row in incomes.iterrows():
            with st.expander(f"💵 {row['description']} — {row['amount']} {row.get('currency', 'EUR')}"):
                # Editable fields
                new_desc = st.text_input("Description", value=row.get("description", ""), key=f"inc_desc_{row['id']}")
                new_amount = st.number_input(
                    "Amount",
                    value=float(row.get("amount", 0.0)),
                    min_value=0.0,
                    format="%.2f",
                    key=f"inc_amt_{row['id']}"
                )
                new_currency = st.selectbox(
                    "Currency",
                    ["EUR", "USD", "GBP"],
                    index=["EUR", "USD", "GBP"].index(row.get("currency", "EUR")),
                    key=f"inc_curr_{row['id']}"
                )
                new_date = st.date_input(
                    "Date",
                    value=pd.to_datetime(row.get("date", date.today())).date(),
                    key=f"inc_date_{row['id']}"
                )

                # Preserve old category/subcategory if present
                cat_id = row.get("category_id", None)
                sub_id = row.get("subcategory_id", None)

                # Save changes button
                if st.button("Save changes", key=f"save_inc_{row['id']}"):
                    update_income(
                        income_id=row["id"],
                        amount=new_amount,
                        description=new_desc,
                        currency=new_currency,
                        inc_date=new_date,
                        category_id=cat_id,
                        subcategory_id=sub_id
                    )
                    st.success("Income updated!")

                # Delete button
                if st.button("Delete", key=f"del_inc_{row['id']}"):
                    delete_income(row["id"])
                    st.warning("Income deleted!")


# -------------------------------
# PAGE: MANAGE CATEGORIES
# -------------------------------
elif page == "Manage Categories":
    st.title("📂 Manage Categories")
    cats = list_categories()
    
    for c in cats:
        with st.expander(f"{c['name']}"):
            # Editable fields for category itself
            new_name = st.text_input("Category Name", c["name"], key=f"name_{c['id']}")
            new_desc = st.text_area("Description", c["description"], key=f"desc_{c['id']}")
            recur = st.checkbox("Recurrent", value=c["recurrent"], key=f"recur_{c['id']}")
            exp_val = st.number_input("Expected monthly (€)", min_value=0.0, value=c["expected_monthly"], format="%.2f", key=f"exp_{c['id']}")
            
            # Save category changes
            if st.button("💾 Save Category", key=f"save_cat_{c['id']}"):
                update_category(
                    category_id=c["id"],
                    name=new_name,
                    description=new_desc,
                    recurrent=recur,
                    expected_monthly=exp_val
                )
                st.success(f"Category '{new_name}' updated!")

            if st.button("🗑 Delete Category", key=f"del_cat_{c['id']}"):
                delete_category(c["id"])
                st.success(f"Category '{new_name}' deleted!")

            st.markdown("---")
            st.subheader("Subcategories")
            
            # Editable existing subcategories
            for sc in c["subcategories"]:
                sc_name = st.text_input("Subcategory Name", sc["name"], key=f"sc_name_{sc['id']}")
                sc_desc = st.text_area("Description", sc["description"], key=f"sc_desc_{sc['id']}")
                
                if st.button("💾 Save Subcategory", key=f"save_sc_{sc['id']}"):
                    update_subcategory(sc["id"], name=sc_name, description=sc_desc)
                    st.success(f"Subcategory '{sc_name}' updated!")

                if st.button("🗑 Delete Subcategory", key=f"del_sc_{sc['id']}"):
                    delete_subcategory(sc["id"])
                    st.success(f"Subcategory '{sc_name}' deleted!")

            # Add new subcategory
            st.subheader("➕ Add new subcategory")
            new_sc_name = st.text_input("New subcategory name", key=f"new_sc_name_{c['id']}")
            new_sc_desc = st.text_area("Description", key=f"new_sc_desc_{c['id']}")
            new_labels = st.text_input("Labels (comma-separated)", key=f"new_sc_labels_{c['id']}")
            if st.button("Add Subcategory", key=f"add_sc_{c['id']}"):
                create_subcategory(c["id"], new_sc_name, new_sc_desc, [l.strip() for l in new_labels.split(",") if l.strip()])
                st.success("Subcategory created!")

    # Add new category
    st.subheader("➕ Add new category")
    new_name = st.text_input("New category name", key="new_cat_name")
    new_desc = st.text_area("Description", key="new_cat_desc")
    new_recur = st.checkbox("Recurrent (monthly expense)?", key="new_cat_recur")
    new_expval = st.number_input("Expected monthly (€)", min_value=0.0, format="%.2f", key="new_cat_expval")
    if st.button("Add category"):
        if new_name.strip():
            create_category(new_name, new_desc, recurrent=new_recur, expected_monthly=new_expval)
            st.success("Category created!")

# -------------------------------
# PAGE: EXPORT DATA
# -------------------------------
elif page == "Export Data":
    st.title("📤 Export Expenses & Income")
    try:
        df_exp = pd.DataFrame(list_recent_expenses(limit=1000))
        df_inc = pd.DataFrame(list_incomes(limit=1000))

        if df_exp.empty and df_inc.empty:
            st.info("No data to export.")
        else:
            if not df_exp.empty:
                st.subheader("Expenses")
                st.dataframe(df_exp)
                csv = df_exp.to_csv(index=False).encode("utf-8")
                st.download_button("Download Expenses CSV", data=csv, file_name="expenses_export.csv", mime="text/csv")
            if not df_inc.empty:
                st.subheader("Income")
                st.dataframe(df_inc)
                csv = df_inc.to_csv(index=False).encode("utf-8")
                st.download_button("Download Income CSV", data=csv, file_name="income_export.csv", mime="text/csv")
    except Exception as e:
        st.error(f"Error exporting: {e}")