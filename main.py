from fastapi import FastAPI,HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import date

app=FastAPI()

#schema to tell fastapi what comes in as JSON payload
class ExpenseCreate(BaseModel):
    title: str
    amount: float
    category: str
    date: date
    description: Optional[str] = None

class ExpenseResponse(BaseModel):
    id: int
    title: str
    amount: float
    category: str
    date: date
    description: Optional[str] = None

expenses=[]
next_id=1


@app.get("/")
async def hello():
    return "Hello World!"

@app.post("/expenses", response_model=ExpenseResponse, status_code=201)
def create_expense(expense: ExpenseCreate):
    global next_id
    new_expense = ExpenseResponse(id=next_id, **expense.model_dump())
    expenses.append(new_expense)
    next_id += 1
    return new_expense

@app.get("/expenses", response_model=list[ExpenseResponse])
def get_expenses():
    return expenses

@app.get("/expenses/{expense_id}", response_model=ExpenseResponse)
def get_expense(expense_id: int):
    for expense in expenses:
        if expense.id == expense_id:
            return expense
    raise HTTPException(status_code=404, detail="Expense not found")

@app.patch("/expenses/{expense_id}", response_model=ExpenseResponse)
def update_expense(expense_id: int, updated: ExpenseCreate):
    for index, expense in enumerate(expenses):
        if expense.id == expense_id:
            expenses[index] = ExpenseResponse(id=expense_id, **updated.model_dump())
            return expenses[index]
    raise HTTPException(status_code=404, detail="Expense not found")

@app.delete("/expenses/{expense_id}", status_code=204)
def delete_expense(expense_id: int):
    for index, expense in enumerate(expenses):
        if expense.id == expense_id:
            expenses.pop(index)
            return
    raise HTTPException(status_code=404, detail="Expense not found")