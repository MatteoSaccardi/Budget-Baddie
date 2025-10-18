import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date
import calendar
import plotly.express as px

from app.schema import (
    init_db, list_categories, create_category, update_category, delete_category,
    create_subcategory, update_subcategory, delete_subcategory,
    add_expense, add_income, delete_expense, delete_income,
    expenses_frame, list_recent_expenses, list_incomes
)

import os
BASE_DIR = os.path.dirname(__file__)
logo_path = BASE_DIR + "/../docs/logo.png"

# -------------------------------
# INITIALIZATION
# -------------------------------
st.set_page_config(page_title="Budget Baddie", layout="wide")
init_db()
today = date.today()

# -------------------------------
# SIDEBAR NAVIGATION
# -------------------------------
st.sidebar.image(logo_path, width=200)  # Logo at top of sidebar
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to page", [
    "Overview",
    "Manage Expenses & Income",
    "Manage Categories",
    "Export Data"
])

# -------------------------------
# HELPER FUNCTIONS
# -------------------------------
def get_cats_dict():
    cats = list_categories()
    return {c["name"]: c["id"] for c in cats}

# -------------------------------
# PAGE: OVERVIEW
# -------------------------------
if page == "Overview":
    st.title("💸 Budget Baddie — Overview")
    
    st.header("🧾 Recent Expenses")
    recent_exp = list_recent_expenses(limit=10)
    if recent_exp:
        st.dataframe(pd.DataFrame(recent_exp))
    else:
        st.info("No recent expenses yet.")

    st.header("💰 Recent Income")
    recent_inc = list_incomes(limit=10)
    if recent_inc:
        st.dataframe(pd.DataFrame(recent_inc))
    else:
        st.info("No recent income yet.")

    st.header("📊 Expense Overview")
    today = date.today()
    all_years = list(range(today.year - 5, today.year + 1))
    selected_years = st.multiselect("Select year(s) to include", all_years, default=[today.year])

    df = pd.DataFrame()
    month_to_num = {name: i for i, name in enumerate(list(calendar.month_name)[1:], start=1)}
    month_names = list(calendar.month_name)[1:]

    for year in selected_years:
        default_month_name = calendar.month_name[today.month]
        options = ["All"] + month_names
        default_value = [default_month_name] if len(selected_years) > 1 else ["All"]
        # Ensure defaults are valid
        default_value = [v for v in default_value if v in options]
        selected_months = st.multiselect(
            f"Select month(s) for {year}",
            options,
            default=default_value,
        )
        month_nums = list(range(1, 13)) if "All" in selected_months else [month_to_num[m] for m in selected_months]
        for month in month_nums:
            df = pd.concat([df, expenses_frame(year, month)], ignore_index=True)

    # if df.empty:
    #     st.warning("No expenses found for the selected period.")
    # else:
    #     st.dataframe(df)
    #     fig_cat, ax_cat = plt.subplots()
    #     by_cat = df.groupby("category")["amount"].sum()
    #     ax_cat.pie(by_cat, labels=by_cat.index, autopct="%1.1f%%", startangle=90)
    #     ax_cat.axis("equal")
    #     st.pyplot(fig_cat)

    #     for cat, subdf in df.groupby("category"):
    #         sub_by = subdf.groupby("subcategory")["amount"].sum()
    #         if len(sub_by) > 1:
    #             st.subheader(f"Subcategory breakdown: {cat}")
    #             fig_sub, ax_sub = plt.subplots()
    #             ax_sub.pie(sub_by, labels=sub_by.index, autopct="%1.1f%%", startangle=90)
    #             ax_sub.axis("equal")
    #             st.pyplot(fig_sub)

    # st.header("📈 Expected vs Real Spending (Recurrent Categories)")
    # cats_df = pd.DataFrame(list_categories())
    # if "recurrent" in cats_df.columns:
    #     recurrent_cats = cats_df[cats_df["recurrent"]]
    # else:
    #     recurrent_cats = pd.DataFrame()
    # if recurrent_cats.empty:
    #     st.info("No recurrent categories found.")
    # elif df.empty:
    #     st.info("No expenses found for the selected period, cannot compute Expected vs Real.")

    # else:
    #     by_cat_real = df.groupby("category")["amount"].sum().reindex(recurrent_cats["name"], fill_value=0.0)
    #     expected_vals = recurrent_cats.set_index("name")["expected_monthly"]
    #     combined = pd.DataFrame({"Expected": expected_vals, "Real": by_cat_real})
    #     st.bar_chart(combined)

    if df.empty:
        st.warning("No expenses found for the selected period.")
    else:
        # Merge expected monthly values for recurrent categories
        cats_df = pd.DataFrame(list_categories())
        if "expected_monthly" in cats_df.columns:
            expected_map = cats_df.set_index("name")["expected_monthly"].to_dict()
            # Replace boolean expected column with actual expected amount
            df["expected"] = df.apply(
                lambda row: expected_map.get(row["category"], 0.0) if row.get("expected") else 0.0,
                axis=1
            )

        st.dataframe(df)

        # Expense overview by category (interactive)
        by_cat = df.groupby("category")["amount"].sum().reset_index()
        fig_cat = px.pie(
            by_cat,
            names="category",
            values="amount",
            title="Expenses by Category",
            hover_data={"amount": ":.2f"},
        )
        st.plotly_chart(fig_cat, use_container_width=True)

        # st.header("📈 Expected vs Real Spending (Recurrent Categories)")
        cats_df = pd.DataFrame(list_categories())
        if "recurrent" in cats_df.columns:
            recurrent_cats = cats_df[cats_df["recurrent"]]
        else:
            recurrent_cats = pd.DataFrame()
        if recurrent_cats.empty:
            st.info("No recurrent categories found.")
        elif df.empty:
            st.info("No expenses found for the selected period, cannot compute Expected vs Real.")

        else:
            by_cat_real = df.groupby("category")["amount"].sum().reindex(recurrent_cats["name"], fill_value=0.0)
            expected_vals = recurrent_cats.set_index("name")["expected_monthly"]
            combined = pd.DataFrame({"Expected": expected_vals, "Real": by_cat_real})
            st.bar_chart(combined)

        # Subcategory breakdown
        for cat, subdf in df.groupby("category"):
            sub_by = subdf.groupby("subcategory")["amount"].sum().reset_index()
            if len(sub_by) > 1:
                st.subheader(f"Subcategory breakdown: {cat}")
                fig_sub = px.pie(
                    sub_by,
                    names="subcategory",
                    values="amount",
                    hover_data={"amount": ":.2f"},
                    title=f"Subcategories of {cat}",
                )
                st.plotly_chart(fig_sub, use_container_width=True)
            
        # Download button
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download Expenses CSV",
            data=csv,
            file_name="expenses_overview.csv",
            mime="text/csv",
        )


# -------------------------------
# PAGE: MANAGE EXPENSES
# -------------------------------
elif page == "Manage Expenses & Income":
    st.title("🧾 Manage Expenses & Income")

    st.header("Add New Expense")
    cats_dict = get_cats_dict()
    if not cats_dict:
        st.warning("No categories defined. Add categories first.")
    else:
        cat_name = st.selectbox("Category", options=list(cats_dict.keys()), key="new_exp_cat")
        cat_id = cats_dict[cat_name]
        subcategories = {sc["name"]: sc["id"] for c in list_categories() if c["id"] == cat_id for sc in c["subcategories"]}
        sub_name = st.selectbox("Subcategory (optional)", options=[""] + list(subcategories.keys()), key="new_exp_sub")
        sub_id = subcategories.get(sub_name) if sub_name else None

        exp_date = st.date_input("Date", value=today, key="new_exp_date")
        amount = st.number_input("Amount (€)", min_value=0.0, format="%.2f", key="new_exp_amount")
        desc = st.text_area("Description", key="new_exp_desc")
        expected = st.checkbox("Expected (planned) expense?", key="new_exp_expected")

        if st.button("Add Expense", key="btn_add_exp"):
            add_expense(exp_date, amount, cat_id, sub_id, desc, expected)
            st.success("Expense added!")

    st.markdown("---")
    st.header("Edit Existing Expenses")

    expenses = list_recent_expenses(limit=1000)
    expenses_df = pd.DataFrame(expenses)

    if expenses_df.empty:
        st.info("No expenses found.")
    else:
        expenses_df = expenses_df.sort_values(by=["date", "id"], ascending=[False, False])
        st.dataframe(expenses_df)

        df_exp = expenses_df.reset_index(drop=True)
        selected_expense_id = st.selectbox(
            "Select an expense to edit",
            options=df_exp["id"],
            format_func=lambda eid: (
                df_exp.loc[df_exp["id"] == eid, "description"].values[0]
                if df_exp.loc[df_exp["id"] == eid, "description"].values[0]
                else df_exp.loc[df_exp["id"] == eid, "category"].values[0]
            ) + f" ({df_exp.loc[df_exp['id'] == eid, 'amount'].values[0]}€)"
        )

        exp = df_exp[df_exp["id"] == selected_expense_id].iloc[0]

        # Editable fields
        cats_dict = get_cats_dict()
        cat_name = st.selectbox(
            "Category",
            options=list(cats_dict.keys()),
            index=list(cats_dict.keys()).index(exp["category"]),
            key=f"edit_cat_{selected_expense_id}"
        )
        cat_id = cats_dict[cat_name]

        subcategories = {sc["name"]: sc["id"] for c in list_categories() if c["id"] == cat_id for sc in c["subcategories"]}
        sub_name = st.selectbox(
            "Subcategory (optional)",
            options=[""] + list(subcategories.keys()),
            index=([""] + list(subcategories.keys())).index(exp["subcategory"]) if exp["subcategory"] in subcategories else 0,
            key=f"edit_sub_{selected_expense_id}"
        )
        sub_id = subcategories.get(sub_name) if sub_name else None

        new_date = st.date_input("Date", value=pd.to_datetime(exp["date"]).date(), key=f"edit_date_{selected_expense_id}")
        new_amount = st.number_input("Amount (€)", min_value=0.0, value=float(exp["amount"]), format="%.2f", key=f"edit_amt_{selected_expense_id}")
        new_desc = st.text_area("Description", value=exp["description"], key=f"edit_desc_{selected_expense_id}")
        new_expected = st.checkbox("Expected (planned)?", value=bool(exp["expected"]), key=f"edit_expected_{selected_expense_id}")

        if st.button("💾 Save Changes", key=f"save_exp_{selected_expense_id}"):
            from app.schema import update_expense
            update_expense(
                expense_id=selected_expense_id,
                exp_date=new_date,
                amount=new_amount,
                category_id=cat_id,
                subcategory_id=sub_id,
                description=new_desc,
                expected=new_expected
            )
            st.success("Expense updated!")

        if st.button("🗑️ Delete Expense", key=f"delete_exp_{selected_expense_id}"):
            from app.schema import delete_expense
            delete_expense(selected_expense_id)
            st.warning("Expense deleted!")

    # --- Income ---
    st.subheader("➕ Add Income")
    if cats_dict:
        inc_cat_name = st.selectbox("Income Category", options=list(cats_dict.keys()), key="inc_cat")
        inc_cat_id = cats_dict[inc_cat_name]
        inc_sub_name = st.selectbox("Subcategory (optional)", options=[""] + list(subcategories.keys()), key="inc_sub")
        inc_sub_id = subcategories.get(inc_sub_name) if inc_sub_name else None

        inc_date = st.date_input("Date", value=today, key="inc_date")
        inc_amount = st.number_input("Amount (€)", min_value=0.0, format="%.2f", key="inc_amount")
        inc_desc = st.text_area("Description", key="inc_desc")

        if st.button("Add Income", key="add_income"):
            add_income(inc_date, inc_amount, inc_cat_id, inc_sub_id, inc_desc)
            st.success("Income added!")

    st.subheader("📝 Edit / Delete Income")
    df_inc = pd.DataFrame(list_incomes(limit=1000))
    if not df_inc.empty:
        for _, row in df_inc.iterrows():
            with st.expander(f"{row['date']} — {row['category']} — €{row['amount']}"):
                new_date = st.date_input("Date", value=pd.to_datetime(row['date']).date(), key=f"inc_date_{row['id']}")
                new_amount = st.number_input("Amount (€)", min_value=0.0, value=row['amount'], format="%.2f", key=f"inc_amount_{row['id']}")
                new_desc = st.text_area("Description", value=row['description'], key=f"inc_desc_{row['id']}")

                if st.button("💾 Update Income", key=f"upd_inc_{row['id']}"):
                    add_income(new_date, new_amount, inc_cat_id, inc_sub_id, new_desc)
                    delete_income(row['id'])
                    st.success("Income updated!")

                if st.button("🗑 Delete Income", key=f"del_inc_{row['id']}"):
                    delete_income(row['id'])
                    st.success("Income deleted!")

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
