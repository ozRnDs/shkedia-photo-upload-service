import logging
logger = logging.getLogger(__name__)
from fastapi import APIRouter, HTTPException, status, Request, Depends, UploadFile
from typing import List, Annotated
from pydantic import BaseModel
from datetime import datetime
import base64

from db.user_service import UserDBService, UserRequest, DeviceRequest
from db.media_service import Token #TODO: Move token to different place

from authentication.service import AuthService

def get_token(request:Request):
    try:
        return Token.get_token_from_request(request=request)
    except Exception as err:
        if type(err) == PermissionError:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Please Go Away")

class PutUserResponse(BaseModel):
    user_name: str
    user_id: str

class UserLoginResponse(BaseModel):
    access_token: str
    token_type: str

class DeviceResponse(BaseModel):
    user_name: str
    device_id: str

class DeviceListResponse(BaseModel):
    user_name: str
    devices_list: List[str]
    devices_ids: List[str]
    session_id: str = "Deprecated Field" # Deprecated


class AuthServiceHandlerV1:
    def __init__(self, 
                auth_service: AuthService,
                user_db_service: UserDBService,
                 ):
        self.auth_service = auth_service
        self.user_db_service = user_db_service
        self.router = self.__initialize_routes__()


    def __initialize_routes__(self):
        router = APIRouter(tags=["User API"],
                        #    dependencies=[Depends(self.auth_service.__get_user_from_token__)],
                           )
        router.add_api_route(path="/register", 
                             endpoint=self.put_user,
                             methods=["put"],
                             response_model=PutUserResponse)
        router.add_api_route(path="/login", 
                             endpoint=self.post_login,
                             methods=["post"],
                             response_model=UserLoginResponse)
        router.add_api_route(path="/device/register", 
                             endpoint=self.get_device_register,
                             methods=["get"],
                             response_model=DeviceResponse)
        router.add_api_route(path="/device/reattach", 
                             endpoint=self.get_reattach_device,
                             methods=["get"],
                             response_model=DeviceResponse)
        router.add_api_route(path="/device/list", 
                             endpoint=self.get_devices_list,
                             methods=["get"],
                             response_model=DeviceListResponse,
                             dependencies=[Depends(self.auth_service.auth_request)])
        return router
    
    def put_user(self, user: UserRequest) -> PutUserResponse:
        try:
            user_response = self.user_db_service.insert_user(user)
            return PutUserResponse(user_name=user_response.user_name, user_id=user_response.user_id)
        except Exception as err:
            raise HTTPException(status_code=500, detail=str(err))

    def post_login(self, user:UserRequest) -> UserLoginResponse:
        try:
            return self.user_db_service.login_user(user)
        except Exception as err:
            if "Permission Denied" in str(err):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Permission Denied")
            raise HTTPException(status_code=500, detail=str(err))

    def get_device_register(self, token: Annotated[Token, Depends(get_token)], user_name: str, device_name: str) -> DeviceResponse:
        try:
            # Check if device exists
            list_of_devices = self.user_db_service.search_device(token=token, search_field="device_name", search_value=device_name)
            if len(list_of_devices)>0:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Device Name Taken")
            # Create Device
            new_device = self.user_db_service.insert_device(token=token, device_request=DeviceRequest(device_name=device_name, owner_name=user_name))
            return DeviceResponse(user_name=user_name, device_id=new_device.device_id)
        except Exception as err:
            raise HTTPException(status_code=500, detail=str(err))

    def get_reattach_device(self, token: Annotated[Token, Depends(get_token)], user_name: str, device_name: str) -> DeviceResponse:
        try:
            # Get Device details by device name
            list_of_devices = self.user_db_service.search_device(token=token, search_field="device_name", search_value=device_name)
            # Find device id from device name
            if len(list_of_devices)==0:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device was not found")
            return DeviceResponse(user_name=user_name, device_id=list_of_devices[0].device_id)
        except Exception as err:
            raise HTTPException(status_code=500, detail=str(err))

    def get_devices_list(self, request: Request) -> DeviceListResponse:
        try:
            # Get User Details
            # user = self.user_db_service.search_user(token=token, search_field="user_name", search_value=user_name)
            # Extract User Id
            list_of_devices = self.user_db_service.search_device(token=request.user_data.auth_token, search_field="owner_id", search_value=request.user_data.id)
            # Get all devices with owner_id = user_id
            list_of_devices_names = [device.device_name for device in list_of_devices]
            list_of_devices_ids = [device.device_id for device in list_of_devices]
            return DeviceListResponse(user_name=request.user_data.name, devices_list=list_of_devices_names, devices_ids=list_of_devices_ids)
        except Exception as err:
            raise HTTPException(status_code=500, detail=str(err))