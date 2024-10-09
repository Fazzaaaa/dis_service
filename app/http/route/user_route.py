from fastapi import APIRouter
from starlette.status import HTTP_201_CREATED

from app.http.controller.user_controller import UserController
from app.schema.base_schema import WebResponse
from app.schema.user_schema import UserResponse, RegisterUserRequest
from fastapi import Body


def get_user_router():
    user_router = APIRouter()
    user_controller = UserController()

    @user_router.post("/register", response_model=WebResponse[UserResponse], status_code=HTTP_201_CREATED)
    async def register(request: RegisterUserRequest = Body(...)):
        return user_controller.register(request)

    return user_router