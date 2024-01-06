import traceback
import logging
logger = logging.getLogger(__name__)

import requests

from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Depends, HTTPException, status, APIRouter, Request
from typing import Annotated
from passlib.context import CryptContext
from pydantic import BaseModel
from datetime import timedelta, datetime
import sqlalchemy
from sqlalchemy.orm import Session

from db.user_service import UserDBService, UserRequest
from db.sql_models import User
from .models import Token

class TokenData(BaseModel):
    name: str | None = None
    id: str | None = None
    auth_token: Token | None = None

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

class AuthService:
    def __init__(self,
                 user_db_service: UserDBService=None,
                 jwt_key_location: str=None,                
                 default_expire_delta_min: int=15,
                 jwt_algorithm: str="HS256") -> None:
        self.user_db_service = user_db_service
        self.jwt_key_location = jwt_key_location
        self.jwt_algorithm = jwt_algorithm
        # self.session_token: str = self.__create_session_token__(service_token_location)
        # self.user_service_uri = user_service_uri
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.default_expire_delta = timedelta(minutes=default_expire_delta_min)
        self.router = self.__initialize_routes__()


    def __initialize_routes__(self):
        router = APIRouter(tags=["Login"])
        router.add_api_route(path="/login", 
                             endpoint=self.log_in,
                             methods=["post"]
                             )
        return router

    def log_in(self, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            user_request = UserRequest(user_name=form_data.username, password=form_data.password)
            auth_token = self.user_db_service.login_user(user=user_request)
            user_data = self.user_db_service.search_user(auth_token,search_value=form_data.username)
            media_db_service_token_data = TokenData(name=user_data.user_name, id=user_data.user_id, auth_token=auth_token)
            media_db_service_token_data = self.create_access_token(data=media_db_service_token_data.model_dump())

            return {"access_token": media_db_service_token_data, "token_type": "bearer"}
        except PermissionError as err:
            raise credentials_exception
        except Exception as err:
            traceback.print_exc()
            logger.error(err)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

    def __get_jwt_key__(self):
        with open(self.jwt_key_location, 'r') as file:
            temp_token = file.read()
        return temp_token

    def auth_request(self, request: Request, token: Annotated[str,Depends(oauth2_scheme)]):
        try:
            request.user_data = self.__get_data_from_token__(token)
            return
        except Exception as err:
            logger.warning(str(err))
        try:
            token = Token.from_token_header(request.headers.get("authorization"))
            user_data = self.user_db_service.get_current_user(token)
            request.user_data = TokenData(name=user_data.user_name,id=user_data.user_id) 
            return
        except Exception as err:
            logger.warning(str(err))
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Not Authorized")

    def __get_data_from_token__(self, token: str) -> TokenData:
        credentials_exception = PermissionError("Invalid Session Token")
        try:
            payload = jwt.decode(token, self.__get_jwt_key__(), algorithms=[self.jwt_algorithm])
            username: str = payload.get("name")
            user_id: str = payload.get("id")
            auth_token: str = payload.get("auth_token")
            if username is None or auth_token is None:
                raise credentials_exception
            token_data = TokenData(name=username,id=user_id,auth_token=Token(**auth_token))
            return token_data
        except JWTError:
            raise credentials_exception
    
    def create_access_token(self, data: dict, expires_delta: timedelta | None=None):
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta if expires_delta else self.default_expire_delta)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.__get_jwt_key__() ,algorithm=self.jwt_algorithm)
        return encoded_jwt
    
    async def middleware_function(self, request: Request, call_next):
        logger.info(f"Auth Service Catch")
        response = await call_next(request)
        return response