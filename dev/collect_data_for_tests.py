import logging
logging.basicConfig(format='%(asctime)s.%(msecs)05d | %(levelname)s | %(filename)s:%(lineno)d | %(message)s' , datefmt='%FY%T')
logger = logging.getLogger()
logger.setLevel(logging.INFO)

from pydantic import BaseModel, Field
from datetime import datetime
from uuid import uuid4
import requests
import pickle
import os

SERVICE_BASE_URL="http://10.0.0.5"


class LoginRequest(BaseModel):
    username: str
    password: str

class User(BaseModel):
    user_id: str = Field(default_factory=lambda: str(uuid4()))
    user_name: str
    created_on: datetime = Field(default_factory=lambda: datetime.now().isoformat())

class TokenHeader(BaseModel):
    access_token: str
    token_type: str

    def get_token_as_header(self):
        return {"Authorization": self.token_type + " " + self.access_token}

def login(username: str, password: str):

    request_content = LoginRequest(username=username, password=password).model_dump()
    login_service_url = SERVICE_BASE_URL+":4430/login"

    login_response = requests.post(login_service_url, data=request_content)
    if login_response.status_code==200:
        logger.info("Logged In")
        return TokenHeader(**login_response.json())
    raise PermissionError(login_response.json()['detail'])

def search_user(token: TokenHeader,**kargs):

    get_user_url = SERVICE_BASE_URL+":4430/user"

    user_response = requests.get(get_user_url, params=kargs, headers=token.get_token_as_header())

    if user_response.status_code == 200:
        logger.info("Got User Details")
        return User(**user_response.json())

def search_media(token: TokenHeader,**kargs):

    search_media_url = SERVICE_BASE_URL+":4431/v1/media/search"

    media_response = requests.get(search_media_url,headers=token.get_token_as_header(),params=kargs)
    # media_response = requests.get(search_media_url,params=kargs)

    if media_response.status_code==200:

        logger.info(media_response.json()["total_results_number"])
        return media_response.json()
    raise Exception(media_response.json()["detail"])

if __name__ == "__main__":
    token = login("test_user", "new_user")
    with open(f"{os.getcwd()}/tests/data/token_data_{datetime.now().strftime('%d%m%Y%H%M%S')}.pickle","wb") as file:
        pickle.dump(token.model_dump(), file, protocol=pickle.HIGHEST_PROTOCOL)
    user = search_user(token=token, search_field="user_name", search_value="test_user")
    try:
        logger.info(f"Search for {user.user_name} medias")
        results = search_media(token=token, owner_id=user.user_id)
        with open(f"{os.getcwd()}/tests/data/media_data_{datetime.now().strftime('%d%m%Y%H%M%S')}.pickle", "wb") as file:
            pickle.dump(results, file, protocol=pickle.HIGHEST_PROTOCOL)
    except Exception as err:
        logger.error(err)
    try:
        logger.info(f"Search for medias named Test_Media")
        results = search_media(token=token, media_name="Test_Media")
    except Exception as err:
        logger.error(err)


