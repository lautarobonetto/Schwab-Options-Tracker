from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class TransactionBase(BaseModel):
    date: datetime
    symbol: str
    description: Optional[str] = None
    quantity: float
    price: float
    amount: float
    type: str

class TransactionCreate(TransactionBase):
    id: int # Schwab ID is required

class Transaction(TransactionBase):
    id: int

    class Config:
        from_attributes = True
