from sqlalchemy import String, create_engine, Column, Integer, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

Base = declarative_base()

class Empresa(Base):
    __tablename__ = "empresas"
    id = Column(String, primary_key=True)
    estoque = Column(JSON) 

def get_db():
    DATABASE_URL = os.getenv("POSTGRES_CONNECTION")
    if not DATABASE_URL:
        raise RuntimeError("Variável POSTGRES_CONNECTION não configurada")
    
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()