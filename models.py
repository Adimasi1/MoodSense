from sqlalchemy import Column, Integer, String, Float
from database import Base

class single_text(Base):
    __tablename__ = "single_text"
    id = Column(Integer, primary_key=True, index=True)
    # request_id is optional now (nullable) to avoid requiring clients to provide it
    text = Column(String(5000), index=True, nullable=False)
    cleaned_text = Column(String(5000), index=True, nullable=True)
    language = Column(String (30), index=True, nullable = True)
    neg = Column(Float, index=True, nullable=True)
    neu = Column(Float, index=True, nullable=True)
    pos = Column(Float, index=True, nullable=True)
    compound = Column(Float, index=True, nullable=True)