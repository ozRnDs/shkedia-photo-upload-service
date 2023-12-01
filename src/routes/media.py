
import logging
logger = logging.getLogger(__name__)
from fastapi import APIRouter, HTTPException, status, Request, Depends, UploadFile
from typing import List, Annotated
from pydantic import BaseModel
from datetime import datetime
import base64

from repo.service import MediaRepoService
from db.media_service import MediaDBService, MediaDB, MediaRequest, SearchResult, Token
from image_processing.service import ImageProccessingService
from encryption.service import EncryptService

def get_token(request:Request):
    try:
        return Token.get_token_from_request(request=request)
    except Exception as err:
        if type(err) == PermissionError:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Please Go Away")

class GetLatestImageResponse(BaseModel):
    last_image_date: int
    #TODO: Create test to compare with current service

    @staticmethod
    def get_latest_image_repsonse(create_on: datetime):
        return GetLatestImageResponse(last_image_date=int(create_on.timestamp()))


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

class UploadServiceHandlerV1:
    def __init__(self, 
                app_logging_service,
                #  auth_service: AuthService,
                media_db_service: MediaDBService,
                encryption_service: EncryptService,
                media_repo_service: MediaRepoService,
                image_proccessing_service: ImageProccessingService,
                max_response_length: int = 200,
                 ):
        self.media_db_service = media_db_service
        self.logging_service = app_logging_service
        self.image_proccessing_service=image_proccessing_service
        self.encrytion_service = encryption_service
        self.media_repo_service = media_repo_service
        self.max_response_length = max_response_length
        # self.auth_service = auth_service
        # if not self.media_db_service.is_ready():
        #     raise Exception("Can't initializes without db_service")
        self.router = self.__initialize_routes__()


    def __initialize_routes__(self):
        router = APIRouter(tags=["Images Upload"],
                        #    dependencies=[Depends(self.auth_service.__get_user_from_token__)],
                           )
        router.add_api_route(path="/list/last", 
                             endpoint=self.get_latest_image_date,
                             methods=["get"],
                             response_model=GetLatestImageResponse)
        router.add_api_route(path="/list", 
                             endpoint=self.put_images_metadata,
                             methods=["post"],
                             response_model=PutImagesMetadataResponse)
        router.add_api_route(path="/list/next", 
                             endpoint=self.get_images_to_upload,
                             methods=["get"],
                             response_model=GetUploadListResponse)
        router.add_api_route(path="/", 
                             endpoint=self.put_image,
                             methods=["put"])
        router.add_api_route(path="/delete/next", 
                             endpoint=self.get_images_to_delete,
                             methods=["get"],
                             response_model=GetImagesToDeleteResponse)
        router.add_api_route(path="/", 
                             endpoint=self.post_deleted_images,
                             methods=["delete"])
        return router

    def get_latest_image_date(self, token: Annotated[Token, Depends(get_token)], user_name: str, device_id: str) -> GetLatestImageResponse:
        try:
            search_result = self.media_db_service.search_media(token=token,device_id=device_id)
            if search_result.total_results_number==0:
                return GetLatestImageResponse.get_latest_image_repsonse(create_on=datetime(year=1970, month=1, day=1))
            media_list_for_device = search_result.results
            while len(media_list_for_device) < search_result.total_results_number:
                search_result = self.media_db_service.search_media(token=token,device_id=device_id, page_number=search_result.page_number+1)
            
            media_list_for_device.sort(key=lambda x: x.created_on, reverse=True)

            return GetLatestImageResponse.get_latest_image_repsonse(create_on=media_list_for_device[0].created_on)

        except Exception as err:
            if type(err) == HTTPException:
                raise err
            if type(err) == PermissionError:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Please Go Away")
            logger.error(err)
            raise HTTPException(status_code=500, detail="Sorry, Something is wrong. Can't get an answer")

    def get_images_to_upload(self, token: Annotated[Token, Depends(get_token)], user_name:str, device_id: str, image_index: int=0)-> GetUploadListResponse:
        try:
            # Get all images for device_id and their MEDIA_STOAGE_STATUS=PENDING
            search_result = self.media_db_service.search_media(token=token, device_id=device_id, upload_status="PENDING")
            media_list_for_device = search_result.results
            if len(media_list_for_device)==0:
                return GetUploadListResponse(images_names=[], images_ids=[], images_uri=[])
            while len(media_list_for_device) < search_result.total_results_number:
                search_result = self.media_db_service.search_media(token=token,device_id=device_id, upload_status="PENDING", page_number=search_result.page_number+1)
            #TODO: Sort all the images by created date
            media_list_for_device.sort(key=lambda x: x.created_on, reverse=True)
            #TODO: Calculate the list according to the image_index value
            
            #TODO: Parse the list to GetUploadListResponse
            return GetUploadListResponse.parse_images_list(media_list_for_device[image_index:image_index+self.max_response_length])
            pass
        except Exception as err:
            logger.error(err)
            if "not found" in str(err):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))
            raise HTTPException(status_code=500, detail="Sorry, Something is wrong. Can't get an answer")
        
    def put_images_metadata(self, token: Annotated[Token, Depends(get_token)], user_name: str, device_id: str, images_list: List[ImageRequest]) -> PutImagesMetadataResponse:
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
                    self.media_db_service.insert_media(token=token,media=media_request)
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

    def put_image(self, token: Annotated[Token, Depends(get_token)], 
                  user_name: str, device_id: str, 
                  image_name: str, image_id: str, 
                  image_content: UploadFile,
                  overwrite: bool = False) -> dict:
        try:
            # Get the image metadata
            search_result = self.media_db_service.search_media(token=token, media_id=image_id)
            search_result = search_result.results[0]
            if not overwrite and search_result.storage_media_uri:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Media with that name already exists")
            values_to_encrypt={}
            values_to_encrypt["image"]=image_content.file.read()
            # Create thumbnail of the image
            values_to_encrypt["thumbnail"]=self.image_proccessing_service.get_image_thumbnail_bytes(image_content.file)
            # Encrypt all the data and get encrypted key
            values_to_encrypt, encrypted_key = self.encrytion_service.encrypt(values_to_encrypt=values_to_encrypt)

            # Upload the encrypted image to the repo
            media_storage_info = self.media_repo_service.put_media(token=token, 
                                                                   media_id=search_result.media_id,
                                                                   media_bytes=values_to_encrypt["image"])

            # Update the image metadata in the db (Added key, thumbnail, storage status and url)
            search_result.media_key=encrypted_key
            search_result.media_thumbnail=values_to_encrypt["thumbnail"]
            search_result.storage_bucket_name=media_storage_info.bucket_name
            search_result.storage_media_uri=media_storage_info.media_uri # Make sure repo returns it
            search_result.storage_service_name=media_storage_info.storage_service_name # Make sure repo returns it
            search_result.upload_status="UPLOADED"
            self.media_db_service.update(token=token, media=search_result)
            return {}
        except Exception as err:
            if type(err) == HTTPException:
                raise err            
            logger.error(err)
            raise HTTPException(status_code=500, detail="Sorry, Something is wrong. Can't get an answer")

    def get_images_to_delete(self, token: Annotated[Token, Depends(get_token)], user_name: str, device_id: str) -> GetImagesToDeleteResponse:
        try:
            # Search for media with device_id=device_id and UPLOAD_STATUS=UPLOADED
            search_result = self.media_db_service.search_media(token=token, device_id=device_id, upload_status="UPLOADED")
            media_list_for_device = search_result.results
            while len(media_list_for_device) < search_result.total_results_number:
                search_result = self.media_db_service.search_media(token=token,device_id=device_id, upload_status="UPLOADED", page_number=search_result.page_number+1)
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