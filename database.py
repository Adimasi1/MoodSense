import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

# This line define a local database file.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sentiment_analyzer.db")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

# create_engine: This is the function used to create the database "engine," which manages the actual connection to the database file.
engine = create_engine(DATABASE_URL,
                       connect_args=connect_args)
# sessionmaker: This creates a factory that produces database "sessions." Think of a session as a temporary workspace for interacting with the database (querying, adding, deleting data).
# autoflush=False: Prevents SQLAlchemy from automatically sending temporary changes to the database before a commit. You usually manage this manually with db.commit(). 
# bind=engine: Tells the sessions created by this factory which database engine to use for communication
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# This creates the special base class that all your SQLAlchemy models (like single_text in models.py) must inherit from. It allows SQLAlchemy's Object-Relational Mapper (ORM) to map your Python classes to database tables and columns.
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
