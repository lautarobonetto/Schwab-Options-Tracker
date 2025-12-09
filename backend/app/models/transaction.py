from app.db.base import Base
from sqlalchemy import Column, Integer, String, Float, DateTime

class Transaction(Base):
    __tablename__ = "raw_transactions"

    id = Column(Integer, primary_key=True, index=True) # Schwab Activity ID
    date = Column(DateTime)
    symbol = Column(String, index=True)
    description = Column(String)
    quantity = Column(Float)
    price = Column(Float)
    amount = Column(Float)
    type = Column(String) # TRADE, JOURNAL, ASSIGN
