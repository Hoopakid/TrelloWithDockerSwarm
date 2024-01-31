from typing import List

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import select, insert, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession

from starlette import status

from models.models import BoardUsers, Board
from database import get_async_session
from schemas import AddBoardUserSchema
from utils import verify_token, request_api_for_user_data

app = FastAPI()



@app.post("/board-user/add")
async def add_board_user(
        email: str,
        board_id: int,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=404, detail='Forbidden!')
    user_id = token.get('user_id')

    response = request_api_for_user_data(email)
    if response:
        board_query = select(Board).where(and_(Board.id == board_id, Board.user_id == user_id))
        board_data = await session.execute(board_query)

        if board_data:
            board_user_query = select(BoardUsers).where(BoardUsers.user_id == response['id']
                                                        and BoardUsers.board_id == board_id)
            board_data = await session.execute(board_user_query)
            board_data = board_data.one()
            if board_data:
                raise HTTPException(status_code=404, detail='Add already exists!')
            else:
                add_query = insert(BoardUsers).values(board_id=board_id, user_id=response['id'])
                await session.execute(add_query)
                await session.commit()
                return 'Succesfuly'
        else:
            raise HTTPException(status_code=404, detail='Not found!')
    else:
        raise HTTPException(status_code=404, detail='No such user exists!')


@app.delete('/board-user/delete')
async def delete_board_user(
        user_id: int,
        board_id: int,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=404, detail='Forbidden!')

    id = token.get('user_id')

    board_query = select(Board).where(and_(Board.id == board_id, Board.user_id == id))
    board_data = await session.execute(board_query)

    if board_data:
        query = delete(BoardUsers).where(BoardUsers.c.user_id == user_id, BoardUsers.c.board_id == board_id)
        await session.execute(query)
        return 'Succesfuly'
    else:
        raise HTTPException(status_code=404, detail='Not found!')

