import sys

from fastapi import FastAPI

import traceback


from config import app_config
from authentication.service import AuthService
from db.media_service import MediaDBService
from db.user_service import UserDBService
from repo.service import MediaRepoService
from image_processing.service import ImageProccessingService
from encryption.service import EncryptService

from routes.media import UploadServiceHandlerV1
from routes.users import AuthServiceHandlerV1
    
app = FastAPI(description="Rest API Interface for the media db service")

#TODO: Bind auth service as middleware to all requests

# Initialize all app services
try:
    auth_service = AuthService(jwt_key_location=app_config.JWT_KEY_LOCATION,
                               db_service=None,
                               default_expire_delta_min=app_config.TOKEN_TIME_PERIOD)
    
    media_db_service = MediaDBService(host=app_config.MEDIA_DB_HOST, port=app_config.MEDIA_DB_PORT)
    
    user_db_service = UserDBService(host=app_config.USER_DB_HOST, port=app_config.USER_DB_PORT)

    media_repo_service = MediaRepoService(host=app_config.MEDIA_REPO_HOST, port=app_config.MEDIA_REPO_PORT)
    
    image_proccessing_service = ImageProccessingService()
    
    encryption_service = EncryptService(public_key_location=app_config.PUBLIC_KEY_LOCATION,
                                        private_key_location=app_config.PRIVATE_KEY_LOCATION)
    
    media_service = UploadServiceHandlerV1(app_logging_service=None,
                                           encryption_service=encryption_service,
                                           media_db_service=media_db_service,
                                           image_proccessing_service=image_proccessing_service,
                                           media_repo_service=media_repo_service) #, auth_service=auth_service)

    users_service = AuthServiceHandlerV1(user_db_service=user_db_service)    
except Exception as err:
    app_config.logger.error(f"Failed to start service. {err}")
    traceback.print_exc()


# Connect all routes
# Example: app.include_router(new_component.router, prefix="/path")

app.include_router(media_service.router, prefix="/images")
app.include_router(users_service.router, prefix="/user")