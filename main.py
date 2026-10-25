from datetime import date
from typing import Annotated, Optional

from fastapi import Depends, FastAPI, HTTPException
from sqlmodel import Field, Session, SQLModel, create_engine, func, select


engine = create_engine("sqlite:///expenses.db", connect_args={"check_same_thread": False})

class ExpenseIn(SQLModel):
    title: str = Field(min_length=1)
    amount: float = Field(gt=0)
    category: str = Field(min_length=1)
    spent_on: date = Field(default_factory=date.today)

class Expense(ExpenseIn, table=True):
    id: Optional[int] = Field(default=None, primary_key= True)

SQLModel.metadata.create_all(engine)
app = FastAPI(title="Expense Tracker API")

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

def find_or_404(session: Session, expense_id:int) -> Expense:
    expense = session.get(Expense, expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense


@app.post("/expenses", status_code=201)
def create_expense(data:ExpenseIn, session: SessionDep) -> Expense:
    expense = Expense.model_validate(data)
    session.add(expense)
    session.commit()
    session.refresh(expense)
    return expense


@app.get("/expenses")
def list_expenses(session: SessionDep) -> list[Expense]:
    return session.exec(select(Expense)).all()

@app.get("/expenses/summary")
def category_totals(session: SessionDep):
    rows = session.exec(
        select(Expense.category,
               func.sum(Expense.amount)).group_by(Expense.category)
    ).all()
    return {category: round(total,2) for category, total in rows}


@app.get("/expenses/{expense_id}")
def get_expense(expense_id: int, session: SessionDep) -> Expense:
    return find_or_404(session, expense_id)

@app.put("/expenses/{expense_id}")
def update_expense(expense_id: int, data: ExpenseIn, session: SessionDep) -> Expense:
    expense = find_or_404(session, expense_id)
    expense.sqlmodel_update(data.model_dump(exclude_unset = True))
    session.add(expense)
    session.commit()
    session.refresh(expense)
    return expense

@app.delete("/expenses/{expense_id}", status_code=204)
def delete_expense(expense_id: int, session: SessionDep):
    session.delete(find_or_404(session, expense_id))
    session.commit()

