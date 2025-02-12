from sqlalchemy import Column, Integer, String, Float, Text
from database import Base

# Example model - you can modify or add more models as needed
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)

class Startup(Base):
    __tablename__ = "startups"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String, unique=True, index=True)
    industry = Column(String)
    stage = Column(String)
    funding_needed = Column(Float)
    minimum_investment = Column(Float)
    equity_offering = Column(Float)
    funding_timeline = Column(String)
    primary_use = Column(String)
    description = Column(Text) 