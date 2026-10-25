# Expense Tracker API

FastAPI + SQLite to add, list, update and delete expenses, with totals per category

## Run
    pip install -r requirements.txt
    uvicorn main:app --reload

Then open http://127.0.0.1:8000/docs

## Tests
    pip install pytest
    pytest

Tests run automatically on every push and pull request via github actions