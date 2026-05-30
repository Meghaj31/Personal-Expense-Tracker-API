from fastapi import FastAPI,HTTPException,Depends
from pydantic import BaseModel
from typing import Optional
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database import get_db
from models import Expense,User
from uuid import UUID
from auth import hash_password, verify_password, create_access_token, get_current_user
from fastapi.security import OAuth2PasswordRequestForm

app=FastAPI()


#schema to tell fastapi what comes in as JSON payload
class ExpenseCreate(BaseModel):

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

class UserCreate(BaseModel):
    name: str
    email: str
    password: str

class UserResponse(BaseModel):
    id: UUID
    name: str
    email: str

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str


@app.get("/")
async def hello():
    return "Hello World!"

@app.post("/expenses", response_model=ExpenseResponse, status_code=201)
async def create_expense(expense: ExpenseCreate, db: AsyncSession=Depends(get_db),current_user: User = Depends(get_current_user)):
    new_expense=Expense(**expense.model_dump(), user_id=current_user.id)
    db.add(new_expense)
    await db.commit()
    await db.refresh(new_expense)
    return new_expense

@app.get("/expenses", response_model=list[ExpenseResponse])
async def get_expenses(db:AsyncSession=Depends(get_db),current_user: User = Depends(get_current_user)):
    result=await db.execute(select(Expense).where(Expense.user_id==current_user.id))
    return result.scalars().all()

@app.get("/expenses/{expense_id}", response_model=ExpenseResponse)
async def get_expense(expense_id: str,db: AsyncSession=Depends(get_db),current_user: User = Depends(get_current_user)):
    result=await db.execute(select(Expense).where(Expense.id==expense_id))
    expense=result.scalar_one_or_none()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    if expense.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return expense


@app.delete("/expenses/{expense_id}", status_code=204)
async def delete_expense(expense_id: str,db:AsyncSession=Depends(get_db),current_user: User = Depends(get_current_user)):
    result=await db.execute(select(Expense).where(Expense.id==expense_id))
    expense=result.scalar_one_or_none()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    if expense.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    await db.delete(expense)
    await db.commit()

@app.patch("/expenses/{expense_id}", response_model=ExpenseResponse)
async def update(expense_id:str,updated:ExpenseCreate,db:AsyncSession=Depends(get_db),current_user: User = Depends(get_current_user)):
    result=await db.execute(select(Expense).where(Expense.id==expense_id))
    expense=result.scalar_one_or_none()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    if expense.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    for key,value in updated.model_dump().items():
        setattr(expense,key,value)
    await db.commit()
    await db.refresh(expense)
    return expense

@app.post("/auth/register", response_model=UserResponse)
async def register(user:UserCreate, db:AsyncSession=Depends(get_db)):
    result=await db.execute(select(User).where(User.email==user.email))
    user_email=result.scalar_one_or_none()
    if user_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    hash_pass=hash_password(user.password)
    new_user=User(
        name=user.name,
        email=user.email,
        hashed_password=hash_pass
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

@app.post("/auth/login", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == form_data.username))
    db_user = result.scalar_one_or_none()
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid Credentials")
    if not verify_password(form_data.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid Credentials")
    token = create_access_token({"sub": str(db_user.id)})
    return {"access_token": token, "token_type": "bearer"}