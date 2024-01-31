from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from utils import verify_token
from database import get_async_session

app = FastAPI()


@app.get("/board-user/add")
async def add_board_user(
        email: str,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=404, detail='Forbidden!')

    # query = select(users).where(users.c.email == email)
    # user_data = await session.execute(query)
