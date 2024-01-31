import aiofiles
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, delete, and_, update
from starlette import status
from models.models import BoardUsers, Board, BoardTable, TaskTable
from database import get_async_session
from utils import verify_token, request_api_for_user_data
from models.models import Board, TrelloChoiceEnum

app = FastAPI(title="Trello")


@app.post("/board-user/add")
async def add_board_user(
        email: str,
        board_id: int,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=404, detail='Forbidden!')
    creator_id = token.get('user_id')

    response = request_api_for_user_data(email)
    if response:
        board_query = select(Board).where(and_(Board.id == board_id, Board.user_id == creator_id))
        board_data = await session.execute(board_query)
        board_data = board_data.scalars().first()

        if board_data:
            board_user_query = select(BoardUsers).where(
                and_(BoardUsers.user_id == response['id'], BoardUsers.board_id == board_id))
            board_user_data = await session.execute(board_user_query)
            board_user_data = board_user_data.scalars().first()
            if board_user_data:
                raise HTTPException(status_code=404, detail='User already in Board!')
            else:
                add_query = insert(BoardUsers).values(board_id=board_id, user_id=response['id'])
                await session.execute(add_query)
                await session.commit()
                return {
                    "status": status.HTTP_201_CREATED,
                    "detail": "User added successfully to Board",
                    "success": True
                }
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

    creator_id = token.get('user_id')

    board_query = select(Board).where(and_(Board.id == board_id, Board.user_id == creator_id))
    board_data = await session.execute(board_query)

    if board_data:
        query = delete(BoardUsers).where(BoardUsers.c.user_id == user_id, BoardUsers.c.board_id == board_id)
        await session.execute(query)
        return {
            "status": status.HTTP_204_NO_CONTENT,
            "detail": "User deleted successfully from Board",
            "success": True
        }
    else:
        raise HTTPException(status_code=404, detail='Not found!')


@app.post('/create-board')
async def create_board(
        board_name: str,
        visibility: TrelloChoiceEnum,
        background: UploadFile = File(...),
        session: AsyncSession = Depends(get_async_session),
):
    try:
        out_file = f'uploads/files/{background.filename}'
        async with aiofiles.open(out_file, 'wb') as f:
            content = await background.read()
            await f.write(content)

        insert_query = insert(Board).values(
            board_name=board_name,
            user_id=1,
            visibility=visibility,
            background=out_file
        )

        await session.execute(insert_query)
        await session.commit()

        return {"detail": "Board successfully created", "status_code": status.HTTP_201_CREATED, "success": True}

    except Exception as e:
        raise HTTPException(detail=f"{e}", status_code=status.HTTP_400_BAD_REQUEST)


@app.patch('/edit-board')
async def edit_board(
        board_id: int,
        new_board_name: str = None,
        new_board_visibility: TrelloChoiceEnum = None,
        session: AsyncSession = Depends(get_async_session),
        token: dict = Depends(verify_token)
):
    if token is None:
        raise HTTPException(detail="Unauthorized", status_code=status.HTTP_401_UNAUTHORIZED)
    user_id = token.get('user_id')

    try:
        board_query = select(Board).where(
            (Board.id == board_id),
            (Board.user_id == user_id)
        )
        board_data = await session.execute(board_query)
        board_data = board_data.scalars().first()
        if board_data:
            update_query = update(Board)
            if new_board_name and new_board_visibility is not None:
                update_query = update_query.where(Board.id == board_id).values(
                    board_name=new_board_name,
                    visibility=new_board_visibility,
                )
            if new_board_name is not None and new_board_visibility is None:
                update_query = update_query.where(Board.id == board_id).values(
                    board_name=new_board_name
                )
            if new_board_visibility is not None and new_board_name is None:
                update_query = update_query.where(Board.id == board_id).values(
                    visibility=new_board_visibility
                )
            if new_board_name and new_board_visibility is None:
                return {"detail": "No changes!!!", "status": status.HTTP_204_NO_CONTENT}
            await session.execute(update_query)
            await session.commit()

            return {
                "detail": "Board updated successfully",
                "status": status.HTTP_200_OK,
                "success": True
            }
        else:
            raise HTTPException(detail="Board not found", status_code=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        raise HTTPException(detail=f"{e}", status_code=status.HTTP_400_BAD_REQUEST)


@app.delete('/delete-board')
async def delete_board(
        board_id: int,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(detail="Unauthorized", status_code=status.HTTP_401_UNAUTHORIZED)
    user_id = token.get('user_id')

    try:
        board_query = select(Board).where(
            (Board.id == board_id),
            (Board.user_id == user_id)
        )
        board_data = await session.execute(board_query)
        board_data = board_data.scalars().first()
        if board_data:
            delete_query = delete(Board).where(Board.id == board_id)
            await session.execute(delete_query)
            await session.commit()
            return {
                "detail": "Board deleted successfully",
                "status": status.HTTP_204_NO_CONTENT,
                "success": True
            }
        else:
            raise HTTPException(detail="Board not found", status_code=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        raise HTTPException(detail=f"{e}", status_code=status.HTTP_400_BAD_REQUEST)


@app.post('/create-table-for-board')
async def create_table_for_board(
        title: str,
        board_id: int,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session),
):
    if token is None:
        raise HTTPException(detail="Unauthorized", status_code=status.HTTP_401_UNAUTHORIZED)
    user_id = token.get('user_id')

    try:
        board_query = select(Board).where(
            (Board.id == board_id),
            (Board.user_id == user_id)
        )
        board_data = await session.execute(board_query)
        board_data = board_data.scalars().first()
        board_user_query = select(BoardUsers).where(
            (BoardUsers.board_id == board_id),
            (BoardUsers.user_id == user_id)
        )
        board_datas = await session.execute(board_query)
        board_datas = board_datas.scalars().first()
        if board_data or board_datas is not None:
            insert_query = insert(BoardTable).values(
                title=title,
                board_id=board_id
            )
            await session.execute(insert_query)
            await session.commit()
            return {
                "detail": "Table for Board created successfully",
                "status": status.HTTP_201_CREATED,
                "success": True
            }
        else:
            raise HTTPException(
                detail="Board not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
    except Exception as e:
        raise HTTPException(
            detail=f"{e}",
            status_code=status.HTTP_400_BAD_REQUEST
        )


@app.patch("/update-table-title")
async def update_table_title(
        table_id: int,
        new_title: str = None,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session),
):
    if token is None:
        raise HTTPException(
            detail="Unauthorized",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    user_id = token.get("user_id")

    try:
        table_query = select(BoardTable).where(
            (BoardTable.id == table_id),
            (BoardTable.user_id == user_id),
        )
        table_data = await session.execute(table_query)
        table_data = table_data.scalars().first()

        if table_data:
            update_query = update(BoardTable)
            if new_title is not None:
                update_query = update_query.where(BoardTable.id == table_id).values(
                    title=new_title
                )
            else:
                return {
                    "detail": "No local changes to save",
                    "status": status.HTTP_204_NO_CONTENT,
                }
            await session.execute(update_query)
            await session.commit()

            return {
                "detail": "Table title updated successfully",
                "status": status.HTTP_200_OK,
                "success": True,
            }
        else:
            raise HTTPException(
                detail="Table not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
    except Exception as e:
        raise HTTPException(
            detail=f"{e}",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


@app.delete("/delete-table{table_id}")
async def delete_table(
        table_id: int,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session),
):
    if token is None:
        raise HTTPException(
            detail="Unauthorized",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    user_id = token.get("user_id")

    try:
        table_query = select(BoardTable).where(
            (BoardTable.id == table_id),
            (BoardTable.user_id == user_id),
        )
        table_data = await session.execute(table_query)
        table_data = table_data.scalars().first()

        if table_data:
            delete_query = delete(BoardTable).where(BoardTable.id == table_id)
            await session.execute(delete_query)
            await session.commit()

            return {
                "detail": "Table deleted successfully",
                "status": status.HTTP_204_NO_CONTENT,
                "success": True,
            }
        else:
            raise HTTPException(
                detail="Table not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
    except Exception as e:
        raise HTTPException(
            detail=f"{e}",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


@app.post('/add-task-for-table')
async def add_task(
        message: str,
        table_id: int,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session),
):
    if token is None:
        raise HTTPException(
            detail="Unauthorized",
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    user_id = token.get('user_id')
    try:
        table_query = select(BoardTable).where(
            (BoardTable.id == table_id),
            (BoardTable.user_id == user_id),
        )
        table_data = await session.execute(table_query)
        table_data = table_data.scalars().first()

        if table_data:
            insert_query = insert(TaskTable).values(
                message=message,
                boardtable_id=table_query
            )
            await session.execute(insert_query)
            await session.commit()
            return {
                "detail": "Message added to table successfully",
                "status": status.HTTP_201_CREATED,
                "success": True,
            }
    except Exception as e:
        raise HTTPException(
            detail=f"{e}",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


@app.patch('/update-task')
async def update_task(
        task_id: int,
        new_message: str = None,
        new_boardtable_id: int = None,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session),
):
    if token is None:
        raise HTTPException(
            detail="Unauthorized",
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    user_id = token.get('user_id')
    try:
        check_query = select(TaskTable).where(
            (TaskTable.id == task_id)
        )
        check_data = await session.execute(check_query)
        check_data = check_data.scalars().first()
        if check_data:
            update_query = update(TaskTable)
            if new_message and new_boardtable_id is not None:
                update_query = update_query.where(TaskTable.id == task_id).values(
                    message=new_message,
                    boardtable_id=new_boardtable_id
                )
            if new_message is not None and new_boardtable_id is None:
                update_query = update_query.where(TaskTable.id == task_id).values(
                    message=new_message
                )
            if new_boardtable_id is not None and new_message is None:
                update_query = update_query.where(TaskTable.id == task_id).values(
                    boardtable_id=new_boardtable_id
                )
            if new_message and new_boardtable_id is None:
                return {
                    "detail": "No local changes to save",
                    "status": status.HTTP_204_NO_CONTENT,
                }
            await session.execute(update_query)
            await session.commit()
            return {
                "detail": "Task updated successfully",
                "status": status.HTTP_200_OK,
                "success": True,
            }
        else:
            raise HTTPException(
                detail="Task not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
    except Exception as e:
        raise HTTPException(
            detail=f"{e}",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


@app.delete('/delete-task')
async def delete_task(
        task_id: int,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session),
):
    if token is None:
        raise HTTPException(
            detail="Unauthorized",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    user_id = token.get('user_id')

    try:
        task_query = select(TaskTable).where(
            (TaskTable.id == task_id),
        )
        task_data = await session.execute(task_query)
        task_data = task_data.scalars().first()
        if task_data:
            delete_query = delete(TaskTable).where(TaskTable.id == task_id)
            await session.execute(delete_query)
            await session.commit()

            return {
                "detail": "Task deleted successfully",
                "status": status.HTTP_204_NO_CONTENT,
                "success": True,
            }
        else:
            raise HTTPException(
                detail="Task not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
    except Exception as e:
        raise HTTPException(
            detail=f"{e}",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
