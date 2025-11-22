# db.py
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import pandas as pd
import os

# SQLite DB file in project folder
DB_PATH = "sqlite:///seating.db"
engine = create_engine(DB_PATH, echo=False)
Base = declarative_base()
Session = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    enrolment_no = Column(String, unique=True, nullable=True)
    name = Column(String)
    email = Column(String, unique=True, nullable=True)
    password_hash = Column(String)
    role = Column(String)  # 'admin' or 'student'

class Room(Base):
    __tablename__ = "rooms"
    id = Column(Integer, primary_key=True)
    room_code = Column(String, unique=True)
    capacity = Column(Integer, default=0)
    layout_meta = Column(Text, nullable=True)

class Seat(Base):
    __tablename__ = "seats"
    id = Column(Integer, primary_key=True)
    room_id = Column(Integer, ForeignKey("rooms.id"))
    seat_no = Column(String)
    enrolment_no = Column(String, nullable=True)
    student_name = Column(String, nullable=True)
    room = relationship("Room")

def init_db():
    """Create DB file and tables (if not exists)."""
    Base.metadata.create_all(engine)

def import_csv(csv_path="seating.csv"):
    """Import seating CSV into SQLite DB.
       CSV must have columns: room,seat_no,enrolment_no,student_name
    """
    if not os.path.exists(csv_path):
        print("CSV not found:", csv_path)
        return
    df = pd.read_csv(csv_path).fillna("")
    s = Session()
    for _, row in df.iterrows():
        room_code = str(row.get("room") or "").strip() or "Unknown"
        seat_no = str(row.get("seat_no") or "").strip()
        enrol = str(row.get("enrolment_no") or "").strip() or None
        name = str(row.get("student_name") or "").strip() or None

        # create/get room
        room = s.query(Room).filter_by(room_code=room_code).first()
        if not room:
            room = Room(room_code=room_code)
            s.add(room)
            s.commit()

        # create or update seat
        seat = s.query(Seat).filter_by(room_id=room.id, seat_no=seat_no).first()
        if not seat:
            seat = Seat(room_id=room.id, seat_no=seat_no, enrolment_no=enrol, student_name=name)
            s.add(seat)
        else:
            seat.enrolment_no = enrol
            seat.student_name = name
    s.commit()
    s.close()
    print("Imported CSV into seating.db")
