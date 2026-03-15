from sqlalchemy import Column, Integer, Text
from db import Base

class QAData(Base):

    __tablename__ = "qa_data"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text)
    answer = Column(Text)