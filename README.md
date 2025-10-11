# PERSONAL BUDGET BUDDY
Simple pythonic app to track your personal budget.

So far, the way to make it work is

- activate python venv: `source .venv/bin/activate`
- create the database if it doesn't exist: `python -m app.schema`
- run `PYTHONPATH=$(pwd) streamlit run app/streamlit_app.py`
- go to http://localhost:8501