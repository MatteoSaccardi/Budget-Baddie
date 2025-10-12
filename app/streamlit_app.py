import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date
import calendar

from app.schema import (
    init_db, list_categories, create_category, update_category, create_subcategory,
    add_expense, add_income, expenses_frame, list_recent_expenses
)

# -------------------------------
# INITIALIZATION
# -------------------------------
st.set_page_config(page_title="Budget Baddie", layout="wide")
# Display logo at the top
# st.image("docs/logo.png", width=150)  # Adjust width as needed
init_db()
today = date.today()

# -------------------------------
# SIDEBAR NAVIGATION
# -------------------------------
st.sidebar.image("docs/logo.png", width=200)  # Logo at top of sidebar
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to page", [
    "Overview",
    "Add Expense",
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
    recent = list_recent_expenses(limit=10)
    if recent:
        st.dataframe(pd.DataFrame(recent))
    else:
        st.info("No recent expenses yet.")

    st.header("📊 Expense Overview")

    # 1️⃣ Year selection
    today = date.today()
    all_years = list(range(today.year - 5, today.year + 1))  # last 5 years
    selected_years = st.multiselect("Select year(s) to include", all_years, default=[today.year])

    df = pd.DataFrame()

    month_to_num = {name: i for i, name in enumerate(list(calendar.month_name)[1:], start=1)}
    month_names = list(calendar.month_name)[1:]  # ['January', 'February', ..., 'December']

    if len(selected_years) == 1:
        year = selected_years[0]
        months_options = ["All"] + month_names
        selected_months = st.multiselect(
            f"Select month(s) for {year}", 
            months_options, 
            default=["All"]
        )
        
        if "All" in selected_months:
            month_nums = list(range(1, 13))
        else:
            month_nums = [month_to_num[m] for m in selected_months]
        
        # Gather expenses
        for month in month_nums:
            df = pd.concat([df, expenses_frame(year, month)], ignore_index=True)

    else:
        # Multiple years: select months per year
        for year in selected_years:
            default_month_name = calendar.month_name[today.month]
            selected_months = st.multiselect(
                f"Select month(s) for {year}",
                month_names,
                default=[default_month_name]  # use name, not number
            )
            month_nums = [month_to_num[m] for m in selected_months]
            for month in month_nums:
                df = pd.concat([df, expenses_frame(year, month)], ignore_index=True)


    if df.empty:
        st.warning("No expenses found for the selected period.")
    else:
        st.dataframe(df)

        # Pie by category
        fig_cat, ax_cat = plt.subplots()
        by_cat = df.groupby("category")["amount"].sum()
        ax_cat.pie(by_cat, labels=by_cat.index, autopct="%1.1f%%", startangle=90)
        ax_cat.axis("equal")
        st.pyplot(fig_cat)

        # Pie by subcategory within each category
        for cat, subdf in df.groupby("category"):
            sub_by = subdf.groupby("subcategory")["amount"].sum()
            if len(sub_by) > 1:
                st.subheader(f"Subcategory breakdown: {cat}")
                fig_sub, ax_sub = plt.subplots()
                ax_sub.pie(sub_by, labels=sub_by.index, autopct="%1.1f%%", startangle=90)
                ax_sub.axis("equal")
                st.pyplot(fig_sub)

    st.header("📈 Expected vs Real Spending (Recurrent Categories)")
    cats_df = pd.DataFrame(list_categories())
    if "recurrent" in cats_df.columns:
        recurrent_cats = cats_df[cats_df["recurrent"]]
    else:
        recurrent_cats = pd.DataFrame()
    if recurrent_cats.empty:
        st.info("No recurrent categories found.")
    else:
        by_cat_real = df.groupby("category")["amount"].sum().reindex(recurrent_cats["name"], fill_value=0.0)
        expected_vals = recurrent_cats.set_index("name")["expected_monthly"]
        combined = pd.DataFrame({"Expected": expected_vals, "Real": by_cat_real})
        st.bar_chart(combined)

# -------------------------------
# PAGE: ADD EXPENSE
# -------------------------------
elif page == "Add Expense":
    st.title("➕ Add Expense")
    cats_dict = get_cats_dict()
    if not cats_dict:
        st.warning("No categories defined. Add categories first.")
    else:
        cat_name = st.selectbox("Category", options=list(cats_dict.keys()))
        cat_id = cats_dict.get(cat_name)
        subcategories = {sc["name"]: sc["id"] for c in list_categories() if c["id"] == cat_id for sc in c["subcategories"]}
        sub_name = st.selectbox("Subcategory (optional)", options=[""] + list(subcategories.keys()))
        sub_id = subcategories.get(sub_name) if sub_name else None

        exp_date = st.date_input("Date", value=today)
        amount = st.number_input("Amount (€)", min_value=0.0, format="%.2f")
        desc = st.text_area("Description")
        expected = st.checkbox("Expected (planned) expense?")

        if st.button("Add Expense"):
            add_expense(exp_date, amount, cat_id, sub_id, desc, expected)
            st.success("Expense added!")

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

            st.markdown("---")
            st.subheader("Subcategories")
            
            # Editable existing subcategories
            for sc in c["subcategories"]:
                sc_name = st.text_input("Subcategory Name", sc["name"], key=f"sc_name_{sc['id']}")
                sc_desc = st.text_area("Description", sc["description"], key=f"sc_desc_{sc['id']}")
                
                if st.button("💾 Save Subcategory", key=f"save_sc_{sc['id']}"):
                    # Reuse create_subcategory only if new, otherwise you may want an update_subcategory function
                    # For simplicity, let's create an update_subcategory function in schema.py
                    from app.schema import update_subcategory
                    update_subcategory(sc["id"], name=sc_name, description=sc_desc)
                    st.success(f"Subcategory '{sc_name}' updated!")

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
    st.title("📤 Export Expenses")
    try:
        df_export = pd.DataFrame(list_recent_expenses(limit=1000))
        if df_export.empty:
            st.info("No expenses to export.")
        else:
            st.dataframe(df_export)
            csv = df_export.to_csv(index=False).encode("utf-8")
            st.download_button("Download CSV", data=csv, file_name="expenses_export.csv", mime="text/csv")
    except Exception as e:
        st.error(f"Error exporting: {e}")
