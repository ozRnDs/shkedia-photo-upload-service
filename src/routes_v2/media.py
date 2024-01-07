import time
import traceback
import json
import logging
logger = logging.getLogger(__name__)
from fastapi import APIRouter, HTTPException, status, Request, Depends, UploadFile, Body
from typing import List, Annotated
from pydantic import BaseModel, Field
from datetime import datetime
import base64

from authentication.service import AuthService
from repo.service import MediaRepoService
from db.media_service import MediaDBService, MediaDB, MediaRequest
from image_processing.service import ImageProcessingService
from encryption.service import EncryptService

from project_shkedia_models.media import MediaIDs, MediaDevice, MediaObjectEnum, Media

class GetLatestImageResponse(BaseModel):
    last_image_date: int
    last_image_date_str: str
    #TODO: Create test to compare with current service

    @staticmethod
    def get_latest_image_repsonse(created_on: datetime):
        return GetLatestImageResponse(last_image_date=int(created_on.timestamp()), last_image_date_str=created_on.isoformat())


class ImageRequest(BaseModel):
    name: str
    date: int
    dateStr: str
    uri: str
    size: int
    camera_model: str
    camera_maker: str

class PutImagesMetadataResponse(BaseModel):
    number_of_images_updated: int

class PutImageRequest(BaseModel):
    image: str

class GetUploadListResponse(BaseModel):
    images_names: List[str]=[] # List of the field image_device_name values
    images_ids: List[str]=[] # List of the db's id field values
    images_uri: List[str]=[] # List of the field image_device_uri values

    @staticmethod
    def parse_images_list(images_list: List[MediaDB]):
        new_response: GetUploadListResponse = GetUploadListResponse()
        for media_dict in images_list:
            new_response.images_ids.append(media_dict.media_id)
            new_response.images_names.append(media_dict.media_name)
            new_response.images_uri.append(media_dict.device_media_uri)
        return new_response
    
class GetImagesToDeleteResponse(BaseModel):
    uri_list: List[str]    

class UploadServiceHandlerV2:
    def __init__(self, 
                app_logging_service,
                auth_service: AuthService,
                media_db_service: MediaDBService,
                encryption_service: EncryptService,
                media_repo_service: MediaRepoService,
                image_proccessing_service: ImageProcessingService,
                max_response_length: int = 200,
                 ):
        self.auth_service = auth_service
        self.media_db_service = media_db_service
        self.logging_service = app_logging_service
        self.image_proccessing_service=image_proccessing_service
        self.encrytion_service = encryption_service
        self.media_repo_service = media_repo_service
        self.max_response_length = max_response_length
        self.router = self.__initialize_routes__()


    def __initialize_routes__(self):
        router = APIRouter(tags=["V2 - Images Upload"])
        router.add_api_route(path="/list/last", 
                             endpoint=self.get_latest_image_date,
                             methods=["get"],
                             response_model=GetLatestImageResponse,
                             dependencies=[Depends(self.auth_service.auth_request)])
        router.add_api_route(path="/list", 
                             endpoint=self.put_images_metadata,
                             methods=["post"],
                             response_model=PutImagesMetadataResponse,
                             dependencies=[Depends(self.auth_service.auth_request)])
        router.add_api_route(path="/list/next", 
                             endpoint=self.get_images_to_upload,
                             methods=["get"],
                             response_model=GetUploadListResponse,
                             dependencies=[Depends(self.auth_service.auth_request)])
        router.add_api_route(path="", 
                             endpoint=self.put_image,
                             methods=["put"],
                             dependencies=[Depends(self.auth_service.auth_request)])
        router.add_api_route(path="/delete/next", 
                             endpoint=self.get_images_to_delete,
                             methods=["get"],
                             response_model=GetImagesToDeleteResponse,
                             dependencies=[Depends(self.auth_service.auth_request)])
        router.add_api_route(path="", 
                             endpoint=self.post_deleted_images,
                             methods=["delete"],
                             dependencies=[Depends(self.auth_service.auth_request)])
        router.add_api_route(path="/v2", 
                             endpoint=self.put_new_image,
                             methods=["put","post"],
                             dependencies=[Depends(self.auth_service.auth_request)])
        return router

    def get_latest_image_date(self, request: Request, device_id: str) -> GetLatestImageResponse:
        try:
            page_size = 1000
            search_result = self.media_db_service.search_media(token=request.user_data.auth_token,device_id=device_id, page_size=page_size)
            if search_result.total_results_number==0:
                return GetLatestImageResponse.get_latest_image_repsonse(created_on=datetime(year=1970, month=1, day=1))
            media_list_for_device = search_result.results
            while len(search_result.results)==page_size:
                search_result = self.media_db_service.search_media(token=request.user_data.auth_token,device_id=device_id, page_size=page_size, page_number=search_result.page_number+1)
                media_list_for_device += search_result.results
            media_list_for_device = [MediaIDs(**media_item) for media_item in media_list_for_device]
            media_list_for_device.sort(key=lambda x: x.created_on, reverse=True)

            return GetLatestImageResponse.get_latest_image_repsonse(created_on=media_list_for_device[0].created_on)

        except Exception as err:
            if type(err) == HTTPException:
                raise err
            if type(err) == PermissionError:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Please Go Away")
            traceback.print_exc()
            logger.error(err)
            raise HTTPException(status_code=500, detail="Sorry, Something is wrong. Can't get an answer")

    def get_images_to_upload(self, request: Request, device_id: str, image_index: int=0)-> GetUploadListResponse:
        try:
            # Get all images for device_id and their MEDIA_STOAGE_STATUS=PENDING
            page_size=1000
            search_result = self.media_db_service.search_media(token=request.user_data.auth_token, device_id=device_id, upload_status="PENDING", page_size=page_size,response_type=MediaObjectEnum.MediaDevice.value)
            media_list_for_device = search_result.results
            if len(media_list_for_device)==0:
                return GetUploadListResponse(images_names=[], images_ids=[], images_uri=[])
            while len(search_result.results)>0 and len(media_list_for_device)<self.max_response_length:
                search_result = self.media_db_service.search_media(token=request.user_data.auth_token,device_id=device_id, 
                                                                   upload_status="PENDING", 
                                                                   page_size=page_size, 
                                                                   page_number=search_result.page_number+1,
                                                                    response_type=MediaObjectEnum.MediaDevice.value)
                media_list_for_device += search_result.results
            media_list_for_device = [MediaDevice(**media_item) for media_item in media_list_for_device]
            media_list_for_device.sort(key=lambda x: x.created_on, reverse=True)
            return GetUploadListResponse.parse_images_list(media_list_for_device[image_index:image_index+self.max_response_length])
            pass
        except Exception as err:
            logger.error(err)
            if "not found" in str(err):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))
            raise HTTPException(status_code=500, detail="Sorry, Something is wrong. Can't get an answer")
        
    def put_images_metadata(self, request: Request, device_id: str, images_list: List[ImageRequest]) -> PutImagesMetadataResponse:
        try:
            new_response = PutImagesMetadataResponse(number_of_images_updated=0)
            error_list = []

            for image in images_list:
                media_request = MediaRequest(media_name=image.name,
                                             media_type="IMAGE",
                                             media_size_bytes=image.size,
                                             created_on=datetime.fromtimestamp(image.date),
                                             device_id=device_id,
                                             device_media_uri=image.uri)
                try:
                    self.media_db_service.insert_media(token=request.user_data.auth_token,media=media_request)
                    new_response.number_of_images_updated+=1
                except Exception as err:
                    error_list.append(f"Failed to insert image {media_request.media_name} metadata from {device_id}:  {str(err)}")           
            if len(error_list) > 0:
                logger.error(error_list)
            if len(error_list)==len(images_list):
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="None of the images were updated")
            return new_response
        except Exception as err:
            if type(err)==HTTPException:
                raise err
            logger.error(str(err))
            if type(err)==AttributeError:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))
            raise HTTPException(status_code=500,detail="Server Internal Error")

    def put_image(self, image: UploadFile, 
                  request: Request, 
                  user_name: Annotated[str, Body(...)],
                  device_id: Annotated[str, Body(...)], 
                  image_name: Annotated[str, Body(...)],
                  image_id: Annotated[str, Body(...)],
                  uri: Annotated[str, Body(...)],
                  overwrite: Annotated[bool, Body(...)]=False) -> dict:
        try:
            # Get the image metadata
            # body = await request.form()
            search_result = self.media_db_service.search_media(token=request.user_data.auth_token, media_id=image_id)
            search_result = search_result.results[0]
            if not overwrite and search_result.storage_media_uri:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Media with that name already exists")
            values_to_encrypt={}
            values_to_encrypt["image"]=image.file.read()
            # Create thumbnail of the image
            values_to_encrypt["thumbnail"], image_size, thumbnail_size, exif=self.image_proccessing_service.get_image_thumbnail_bytes(image.file)
            # Encrypt all the data and get encrypted key
            values_to_encrypt, encrypted_key = self.encrytion_service.encrypt(values_to_encrypt=values_to_encrypt)
            # Upload the encrypted image to the repo
            media_storage_info = self.media_repo_service.put_media(token=request.user_data.auth_token, 
                                                                   media_id=search_result.media_id,
                                                                   media_bytes=values_to_encrypt["image"])

            # Update the image metadata in the db (Added key, thumbnail, storage status and url)
            search_result.media_key=encrypted_key
            search_result.media_thumbnail=values_to_encrypt["thumbnail"]
            search_result.storage_bucket_name=media_storage_info.bucket_name
            search_result.storage_media_uri=media_storage_info.media_uri # Make sure repo returns it
            search_result.storage_service_name=media_storage_info.storage_service_name # Make sure repo returns it
            search_result.media_width=image_size[0]
            search_result.media_height=image_size[1]
            search_result.media_thumbnail_width=thumbnail_size[0]
            search_result.media_thumbnail_height=thumbnail_size[1]
            search_result.upload_status="UPLOADED"
            search_result.exif=json.dumps(exif)
            self.media_db_service.update(token=request.user_data.auth_token, media=search_result)
            return {}
        except Exception as err:
            if type(err) == HTTPException:
                raise err            
            error_details = {
                "media_id": image_id,
                "error": str(err)
            }
            logger.error(str(error_details))
            raise HTTPException(status_code=500, detail="Sorry, Something is wrong. Can't get an answer")

    def put_new_image(self, 
                  request: Request, 
                  image: UploadFile, 
                  device_id: Annotated[str, Body(...)],
                  created_on: Annotated[str, Body(...)],
                  device_media_uri: Annotated[str, Body(...)],
                  overwrite: Annotated[bool, Body(...)]=False) -> dict:
        try:
            # Create the media metadata
            media_request = MediaRequest(media_name=image.filename,
                                media_type="IMAGE",
                                media_size_bytes=image.size,
                                created_on=datetime.fromisoformat(created_on),
                                device_id=device_id,
                                device_media_uri=device_media_uri)
            
            search_result = self.media_db_service.insert_media(token=request.user_data.auth_token,media=media_request)
            search_result = self.media_db_service.search_media(token=request.user_data.auth_token,media_id=search_result.media_id,response_type=MediaObjectEnum.Media)
            search_result = Media(**search_result.results[0])
            values_to_encrypt={}
            values_to_encrypt["image"]=image.file.read()
            # Create thumbnail of the image
            values_to_encrypt["thumbnail"], image_size, thumbnail_size, exif=self.image_proccessing_service.get_image_thumbnail_bytes(image.file)
            # Encrypt all the data and get encrypted key
            values_to_encrypt, encrypted_key = self.encrytion_service.encrypt(values_to_encrypt=values_to_encrypt)
            # Upload the encrypted image to the repo
            media_storage_info = self.media_repo_service.put_media(token=request.user_data.auth_token, 
                                                                    media_id=search_result.media_id,
                                                                    media_bytes=values_to_encrypt["image"])

            # Update the image metadata in the db (Added key, thumbnail, storage status and url)
            search_result.media_key=encrypted_key
            search_result.media_thumbnail=values_to_encrypt["thumbnail"]
            search_result.storage_bucket_name=media_storage_info.bucket_name
            search_result.storage_media_uri=media_storage_info.media_uri # Make sure repo returns it
            search_result.storage_service_name=media_storage_info.storage_service_name # Make sure repo returns it
            search_result.media_width=image_size[0]
            search_result.media_height=image_size[1]
            search_result.media_thumbnail_width=thumbnail_size[0]
            search_result.media_thumbnail_height=thumbnail_size[1]
            search_result.upload_status="UPLOADED"
            search_result.exif=json.dumps(exif)
            self.media_db_service.update(token=request.user_data.auth_token, media=MediaDB(**search_result.model_dump()))
            return {}
        except Exception as err:
            if type(err) == HTTPException:
                raise err   
            traceback.print_exc()         
            logger.error(err)
            raise HTTPException(status_code=500, detail="Sorry, Something is wrong. Can't get an answer")

    def get_images_to_delete(self, request: Request, user_name: str, device_id: str) -> GetImagesToDeleteResponse:
        try:
            # Search for media with device_id=device_id and UPLOAD_STATUS=UPLOADED
            search_result = self.media_db_service.search_media(token=request.user_data.auth_token, device_id=device_id, upload_status="UPLOADED")
            media_list_for_device = search_result.results
            while len(media_list_for_device) < search_result.total_results_number:
                search_result = self.media_db_service.search_media(token=request.user_data.auth_token,device_id=device_id, upload_status="UPLOADED", page_number=search_result.page_number+1)
            # Sort the list from old to new
            media_list_for_device.sort(key=lambda x: x.created_on, reverse=False)
            # Get the 50 first (old)
            return GetImagesToDeleteResponse(uri_list=[media.device_media_uri for media in media_list_for_device[0:50]])
        except Exception as err:
            logger.error(err)
            if "not found" in str(err):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))
            raise HTTPException(status_code=500, detail="Sorry, Something is wrong. Can't get an answer")
        
    def post_deleted_images(self, user_name: str, device_id: str, images_list: List[str]):
        try:
            raise HTTPException(status_code=status.HTTP_425_TOO_EARLY)
            #TODO: Search for media with device_id=device_id and UPLOAD_STATUS=UPLOADED
            #TODO: Sort the list from old to new
            #TODO: Get the 50 first (old)
        except Exception as err:
            logger.error(err)
            raise HTTPException(status_code=500, detail="Sorry, Something is wrong. Can't get an answer")