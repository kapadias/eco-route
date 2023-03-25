from fastapi import HTTPException


async def raise_error(status_code: int, message: str):
    # raise the http exception
    raise HTTPException(status_code=status_code, detail=message)
