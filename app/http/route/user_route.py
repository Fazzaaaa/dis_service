import math
from typing import List

from bson import ObjectId
from fastapi import APIRouter, Depends, Request, HTTPException, Response, UploadFile
from starlette.responses import JSONResponse
from starlette.status import HTTP_201_CREATED, HTTP_200_OK

from app.http.controller.user_controller import UserController
from app.http.middleware.auth import get_current_user
from app.schema.base_schema import WebResponse
from app.schema.user_schema import UserResponse, RegisterUserRequest, TokenResponse, LoginUserRequest, GetUserRequest, \
    LogoutUserRequest, UpdateUserRequest, ChangePasswordRequest, AddAccountRequest, ChangePhotoRequest, AccountResponse, \
    ListAccountRequest, GetAccountRequest, ForgetPasswordRequest, UpdateAccountRequest, DeleteAccountRequest, \
    WithdrawalRequest, FollowRequest
from fastapi import Body, File, Request
from app.core.logger import logger
import io
from PIL import Image


def get_user_router():
    user_router = APIRouter()
    user_controller = UserController()

    @user_router.post("/register", response_model=WebResponse[UserResponse], status_code=HTTP_201_CREATED)
    async def register(request: RegisterUserRequest = Body(...)):
        return user_controller.register(request)

    @user_router.post("/login", response_model=WebResponse[TokenResponse], status_code=HTTP_200_OK)
    async def login(request: LoginUserRequest = Body(...)):
        try:
            token_response = user_controller.login(request)
            logger.info(f"Token response: {token_response}")
            return token_response
        except HTTPException as e:
            logger.error(f"HTTPException during login: {e.detail}")
            raise e
        except Exception as e:
            logger.error(f"Exception during login: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal Server Error")

    @user_router.get("/current", response_model=WebResponse[UserResponse], status_code=HTTP_200_OK)
    async def get(request: Request, current_user: str = Depends(get_current_user)):
        logger.info(f"Current user: {current_user}")
        if current_user:
            request.state.id = current_user
            data = GetUserRequest(id=request.state.id)
            return user_controller.get(data)
        else:
            raise HTTPException(status_code=400, detail="Invalid user ID")

    @user_router.delete("/logout", response_model=WebResponse[bool], status_code=HTTP_200_OK)
    async def logout(request: Request, current_user: str = Depends(get_current_user)):
        try:
            if current_user:
                access_token = request.headers.get("Authorization").split(" ")[1]
                refresh_token = request.headers.get("X-Refresh-Token")
                logger.info(f"Refresh token: {refresh_token}")
                body = LogoutUserRequest(id=current_user, refresh_token=refresh_token, access_token=access_token)
                return user_controller.logout(body)
        except Exception as e:
            logger.error(f"Error in logout: {str(e)}")
            raise HTTPException(status_code=400, detail="Invalid token")

    @user_router.patch("/update", response_model=WebResponse[UserResponse], status_code=HTTP_200_OK)
    async def update(request: UpdateUserRequest = Body(...), current_user: str = Depends(get_current_user)):
        logger.info(f"Current user: {current_user}")
        if current_user:
            request.id = current_user
        else:
            raise HTTPException(status_code=400, detail="Invalid user ID")
        try:
            return user_controller.update(request)
        except HTTPException as err:
            logger.error(f"Error during update: {err.detail}")
            raise HTTPException(detail=err.detail, status_code=err.status_code)

    @user_router.patch("/change_password", response_model=WebResponse[bool], status_code=HTTP_200_OK)
    async def change_password(request: ChangePasswordRequest = Body(...), current_user: str = Depends(get_current_user)):
        logger.info(f"Current user: {current_user}")
        if current_user:
            request.id = current_user
        else:
            raise HTTPException(status_code=400, detail="Invalid user ID")
        try:
            return user_controller.change_password(request)
        except HTTPException as err:
            logger.error(f"Error during change password: {err.detail}")
            raise HTTPException(detail=err.detail, status_code=err.status_code)

    @user_router.patch("/change_profile", response_model= WebResponse[UserResponse], status_code=HTTP_200_OK)
    async def change_profile(file: UploadFile = File(...), current_user: str = Depends(get_current_user)):
        logger.info(f"Current user: {current_user}")
        await file.read()
        if current_user:
            request = ChangePhotoRequest(id=current_user, photo=file.filename)
        else:
            raise HTTPException(status_code=400, detail="Invalid user ID")
        try:
            return user_controller.change_profile(request, file)
        except HTTPException as err:
            logger.error(f"Error during change profile: {err.detail}")
            raise HTTPException(detail=err.detail, status_code=err.status_code)

    @user_router.post("/forget_password", response_model=WebResponse[bool], status_code=HTTP_200_OK)
    async def forget_password(request: ForgetPasswordRequest = Body(...)):
        pass

    @user_router.post("/add_account", response_model=WebResponse[AccountResponse], status_code=HTTP_201_CREATED)
    async def add_account(request: AddAccountRequest, current_user: str = Depends(get_current_user)):
        logger.info(f"Current user: {current_user}")
        if current_user:
            request.id = current_user
        else:
            raise HTTPException(status_code=400, detail="Invalid user ID")
        try:
            return user_controller.add_account(request)
        except HTTPException as err:
            logger.error(f"Error during add account: {err.detail}")
            raise HTTPException(detail=err.detail, status_code=err.status_code)

    @user_router.get("/account/{id}", response_model=WebResponse[AccountResponse], status_code=HTTP_200_OK)
    async def get_account(id, current_user: str = Depends(get_current_user)):
        logger.info(f"Current user: {current_user}")
        if current_user:
            request = GetAccountRequest(id=current_user, account_id=id)
        else:
            raise HTTPException(status_code=400, detail="Invalid user ID")
        try:
            return user_controller.get_account(request)
        except HTTPException as err:
            logger.error(f"Error during get account: {err.detail}")
            raise HTTPException(detail=err.detail, status_code=err.status_code)

    @user_router.get("/accounts", response_model=WebResponse[List[AccountResponse]], status_code=HTTP_200_OK)
    async def list_account(request: Request, current_user: str = Depends(get_current_user)):
        logger.info(f"Current user: {current_user}")
        bank = request.query_params.get("bank")
        name = request.query_params.get("name")
        number = request.query_params.get("number")
        page = request.query_params.get("page", 1)
        size = request.query_params.get("size", 10)
        data = ListAccountRequest()
        try:
            if current_user:
                data.id = current_user
                data.name = name if name else None
                data.bank = bank if bank else None
                data.number = number if number else None
                data.page = int(page)
                data.size = int(size)

                result = user_controller.list_account(data)
                total = result["total"]
                paging = {
                    "page": data.page,
                    "size": data.size,
                    "total_item": total,
                    "total_page": int(math.ceil(total / data.size))
                }
                return WebResponse(data=result["data"], paging=paging)
            else:
                raise HTTPException(status_code=400, detail="Invalid user ID")
        except HTTPException as err:
            logger.error(f"Error during list account: {err.detail}")
            raise HTTPException(detail=err.detail, status_code=err.status_code)

    @user_router.patch("/account/{id}", response_model=WebResponse[AccountResponse], status_code=HTTP_200_OK)
    async def update_account(id, request: UpdateAccountRequest = Body(...), current_user: str = Depends(get_current_user)):
        logger.info(f"Current user: {current_user}")
        if current_user:
            request.id = current_user
            request.account_id = id
        else:
            raise HTTPException(status_code=400, detail="Invalid user ID")
        try:
            return user_controller.update_account(request)
        except HTTPException as err:
            logger.error(f"Error during update account: {err.detail}")
            raise HTTPException(detail=err.detail, status_code=err.status_code)

    @user_router.delete("/account/{id}", response_model=WebResponse[bool], status_code=HTTP_200_OK)
    async def delete_account(id, current_user: str = Depends(get_current_user)):
        logger.info(f"Current user: {current_user}")
        if current_user:
            request = DeleteAccountRequest(id=current_user, account_id=id)
        else:
            raise HTTPException(status_code=400, detail="Invalid user ID")
        try:
            return user_controller.delete_account(request)
        except HTTPException as err:
            logger.error(f"Error during delete account: {err.detail}")
            raise HTTPException(detail=err.detail, status_code=err.status_code)

    @user_router.post("/withdrawal", response_model=WebResponse[UserResponse], status_code=HTTP_200_OK)
    async def withdrawal(request: WithdrawalRequest, current_user: str = Depends(get_current_user)):
        logger.info(f"Current user: {current_user}")
        if current_user:
            request.id = current_user
        else:
            raise HTTPException(status_code=400, detail="Invalid user ID")
        try:
            return user_controller.withdrawal(request)
        except HTTPException as err:
            logger.error(f"Error during withdrawal: {err.detail}")
            raise HTTPException(detail=err.detail, status_code=err.status_code)

    @user_router.post("/follow/{target_id}", response_model=WebResponse[bool], status_code=HTTP_200_OK)
    async def follow(target_id, request: FollowRequest = Body(...), current_user: str = Depends(get_current_user)):
        logger.info(f"Current user: {current_user}")
        if current_user:
            request.id = current_user
            request.target_id = target_id
        else:
            raise HTTPException(status_code=400, detail="Invalid user ID")
        try:
            return user_controller.follow(request)
        except HTTPException as err:
            logger.error(f"Error during follow: {err.detail}")
            raise HTTPException(detail=err.detail, status_code=err.status_code)

    return user_router