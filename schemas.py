from pydantic import BaseModel


class AddBoardUserSchema(BaseModel):
    id: int
    board_id: int
    user_id: int
