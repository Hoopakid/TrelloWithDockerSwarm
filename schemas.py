from pydantic import BaseModel

from models.models import TrelloChoiceEnum


class BoardScheme(BaseModel):
    board_name: str
    visibility: TrelloChoiceEnum
    background: int