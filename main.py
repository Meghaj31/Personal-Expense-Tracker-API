from fastapi import FastAPI,HTTPException,Depends
from pydantic import BaseModel
from typing import Optional
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database import get_db
from models import Expense
from uuid import UUID

app=FastAPI()

#schema to tell fastapi what comes in as JSON payload
class ExpenseCreate(BaseModel):
    user_id: UUID
    title: str
    amount: float
    category: str
    date: date
    description: Optional[str] = None

class ExpenseResponse(BaseModel):
    id: UUID
    title: str
    amount: float
    category: str
    date: date
    description: Optional[str] = None
    class Config:
        from_attributes = True


@app.get("/")
async def hello():
    return "Hello World!"

@app.post("/expenses", response_model=ExpenseResponse, status_code=201)
async def create_expense(expense: ExpenseCreate, db: AsyncSession=Depends(get_db)):
    new_expense=Expense(**expense.model_dump())
    db.add(new_expense)
    await db.commit()
    await db.refresh(new_expense)
    return new_expense

@app.get("/expenses", response_model=list[ExpenseResponse])
async def get_expenses(db:AsyncSession=Depends(get_db)):
    result=await db.execute(select(Expense))
    return result.scalars().all()

@app.get("/expenses/{expense_id}", response_model=ExpenseResponse)
async def get_expense(expense_id: str,db: AsyncSession=Depends(get_db)):
    result=await db.execute(select(Expense).where(Expense.id==expense_id))
    expense=result.scalar_one_or_none()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense


@app.delete("/expenses/{expense_id}", status_code=204)
async def delete_expense(expense_id: str,db:AsyncSession=Depends(get_db)):
    result=await db.execute(select(Expense).where(Expense.id==expense_id))
    expense=result.scalar_one_or_none()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    await db.delete(expense)
    await db.commit()

@app.patch("/expenses/{expense_id}", response_model=ExpenseResponse)
async def update(expense_id:str,updated:ExpenseCreate,db:AsyncSession=Depends(get_db)):
    result=await db.execute(select(Expense).where(Expense.id==expense_id))
    expense=result.scalar_one_or_none()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    for key,value in updated.model_dump().items():
        setattr(expense,key,value)
    await db.commit()
    await db.refresh(expense)
    return expense