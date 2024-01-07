import logging
logger = logging.getLogger(__name__)
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import traceback


from config import app_config
from authentication.service import AuthService
from db.media_service import MediaDBService
from db.user_service import UserDBService
from repo.service import MediaRepoService
from image_processing.service import ImageProcessingService
from encryption.service import EncryptService

from routes.media import UploadServiceHandlerV1
from routes.users import AuthServiceHandlerV1
from routes_v2.media import UploadServiceHandlerV2
from publisher.service import PublisherService

app = FastAPI(description="Rest API Interface for the upload service", title="Project Shkedia - Upload Service")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://10.0.0.5:25001","http://10.0.0.5:24500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize all app services
try:
    try:
        publisher_service = PublisherService(topic_names=[app_config.IMAGE_CONTENT_TOPIC_NAME,app_config.IMAGE_METADATA_TOPIC_NAME],environment=app_config.ENVIRONMENT)
    except Exception as err:
        traceback.print_exc()
        logger.warning("Could not initialize the publisher service. Service will work without it")

    media_db_service = MediaDBService(host=app_config.MEDIA_DB_HOST, port=app_config.MEDIA_DB_PORT)
    
    user_db_service = UserDBService(host=app_config.USER_DB_HOST, port=app_config.USER_DB_PORT)

    auth_service = AuthService(jwt_key_location=app_config.JWT_KEY_LOCATION,
                               user_db_service=user_db_service,
                               default_expire_delta_min=app_config.TOKEN_TIME_PERIOD)

    media_repo_service = MediaRepoService(host=app_config.MEDIA_REPO_HOST, port=app_config.MEDIA_REPO_PORT)
    
    image_proccessing_service = ImageProcessingService()
    
    encryption_service = EncryptService(public_key_location=app_config.PUBLIC_KEY_LOCATION,
                                        private_key_location=app_config.PRIVATE_KEY_LOCATION)
    
    media_service = UploadServiceHandlerV1(app_logging_service=None,
                                           encryption_service=encryption_service,
                                           media_db_service=media_db_service,
                                           image_proccessing_service=image_proccessing_service,
                                           media_repo_service=media_repo_service) #, auth_service=auth_service)

    media_service_v2 = UploadServiceHandlerV2(app_logging_service=None,
                                              encryption_service=encryption_service,
                                              media_db_service=media_db_service,
                                              auth_service=auth_service,
                                              image_proccessing_service=image_proccessing_service,
                                              media_repo_service=media_repo_service)

    users_service = AuthServiceHandlerV1(user_db_service=user_db_service, auth_service=auth_service)
except Exception as err:
    app_config.logger.error(f"Failed to start service. {err}")
    traceback.print_exc()


# Connect all routes
# Example: app.include_router(new_component.router, prefix="/path")

# app.include_router(media_service.router, prefix="/images")
app.include_router(users_service.router, prefix="/user")
app.include_router(auth_service.router)
app.include_router(media_service_v2.router, prefix="/images")