from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from database import get_async_session
from schemas import BoardScheme
from utils import verify_token

app = FastAPI()


@app.post('/create-board')
async def create_board(
        board_data: BoardScheme,
        session: AsyncSession = Depends(get_async_session),
        token: dict = Depends(verify_token)
):
    if token is None:
        raise HTTPException(detail="Unauthorized", status_code=status.HTTP_401_UNAUTHORIZED)

    try:
        pass

    except Exception as e:
        raise HTTPException(detail=f"{e}", status_code=status.HTTP_400_BAD_REQUEST)
