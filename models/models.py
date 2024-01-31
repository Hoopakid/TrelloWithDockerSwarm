from datetime import datetime
import enum

from database import Base
from sqlalchemy import Column, Integer, String, ForeignKey, MetaData, Enum, TIMESTAMP

metadata = MetaData()


class TrelloChoiceEnum(enum.Enum):
    private = "Private"
    public = "Public"
    workspace = "Workspace"


class BoardBackground(Base):
    __tablename__ = "background"
    metadata = metadata

    id = Column(Integer, index=True, autoincrement=True, primary_key=True)
    background = Column(String)


class Board(Base):
    __tablename__ = "board"
    metadata = metadata

    id = Column(Integer, index=True, autoincrement=True, primary_key=True)
    board_name = Column(String)
    user_id = Column(Integer)
    visibility = Column(Enum(TrelloChoiceEnum), default=TrelloChoiceEnum.public)
    background = Column(Integer, ForeignKey("background.id"))
    created_at = Column(TIMESTAMP, default=datetime.utcnow)


class BoardTable(Base):
    __tablename__ = "boardtable"

    id = Column(Integer, index=True, autoincrement=True, primary_key=True)
    title = Column(String)


class BoardUsers(Base):
    __tablename__ = "boardusers"
    metadata = metadata

    id = Column(Integer, index=True, autoincrement=True, primary_key=True)
    board_id = Column(Integer, ForeignKey("board.id"))
    user_id = Column(Integer)


class TaskTable(Base):
    __tablename__ = "tasktable"

    id = Column(Integer, index=True, autoincrement=True, primary_key=True)
    message = Column(String)
    board_id = Column(Integer, ForeignKey("boardtable.id"))
