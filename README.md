# 💰 BudgetBaddie

**BudgetBaddie** is a simple, pythonic personal budget tracker that helps you manage your expenses, incomes, and recurring categories. Visualize your spending and stay on top of your finances effortlessly!

---

![BudgetBaddie Logo](docs/logo.jpg)

---

## Features

- Track expenses and incomes
- Manage categories and subcategories
- Handle recurrent and expected expenses
- Visualize spending with monthly or yearly summaries
- Export your data easily
- Interactive web interface using **Streamlit**

---

## Getting Started (Local)

### Prerequisites
- Python 3.9+
- `virtualenv` or `venv` for isolated environments

### Setup

0. Unable any aliasing, e.g. ```unalias python3```, ```unalias pip```, etc.

1. Clone the repository:
   ```bash
   git clone https://github.com/MatteoSaccardi/budgetbaddie.git
   cd budgetbaddie
   ```

2. Create and activate virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Initialize the database:
   ```bash
   python -m app.schema
   ```

5. Run the app:
   ```bash
   PYTHONPATH=$(pwd) streamlit run app/streamlit_app.py
   ```

6. Open your web browser and navigate to [http://localhost:8501](http://localhost:8501)

---

## Usage

- Sidebar menu: Navigate between pages:
- Overview: Visualize expenses for selected months/years.
- Add Expenses: Record new expenses with category, subcategory, expected flag, and notes.
- Manage Categories: Add, edit, or delete categories and subcategories.
- Export: Download recent or filtered expenses as CSV.
- Overview Page:
  * Select one or multiple years
  * Select months or “All” for full-year comparison
  * Pie charts for category and subcategory breakdown
  * Compare real vs expected spending for recurrent categories
- Manage Categories Page:
  * Edit existing categories: name, description, recurrent flag, expected monthly
  * Add new categories with all fields
  * Manage subcategories for each category
- Add Expenses Page:
  * Choose category/subcategory
  * Enter date, amount, description, and expected flag
- Export Page:
  * Download filtered expenses in CSV
  * Multi-year export supported

---

## Dependencies

- [https://streamlit.io/](Streamlit)
- [https://sqlalchemy.org/](SQLAlchemy)
- [https://pydantic-docs.helpmanual.io/](Pydantic)
- [https://pandas.pydata.org/](Pandas)
- [https://matplotlib.org/](Matplotlib)
- [https://python-dateutil.readthedocs.io/en/stable/](python-dateutil)

---

## Contributing


Contributions are welcome! You can email me at [my personal email](mailto:matteo.saccardi97@gmail.com) for any questions or suggestions.
- Open issues for bugs or feature requests
- Suggest improvements
- Submit pull requests

---

## License

This project is licensed under the [MIT License](LICENSE) Matteo Saccardi