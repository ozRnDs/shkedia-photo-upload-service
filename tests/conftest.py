import logging
logger = logging.getLogger(__name__)
import sys, os
import pytest
import pickle
from fastapi.testclient import TestClient
from datetime import datetime

sys.path.append(f"{os.getcwd()}/src")
print(sys.path)

from main import app, app_config # TODO: Figure out better way to test the app
from models.media import MediaRequest, MediaDB
from routes.media import ImageRequest



@pytest.fixture(scope="session")
def client_fixture():
    client = TestClient(app)
    yield client
    client.close()

@pytest.fixture(scope="session")
def original_service_uri_fixture():
    return "http://10.0.0.12:3080/"

@pytest.fixture(scope="session")
def search_result_fixture():
    with open(f"{os.getcwd()}/tests/data/media_data_07122023191705.pickle",'rb') as file:
        media_list = pickle.load(file)
    return media_list

@pytest.fixture(scope="session")
def images_request_list(search_result_fixture):
    request_list = []
    for media in search_result_fixture["results"]:
        media_db = MediaDB(**media)
        request_list.append(ImageRequest(name=media_db.media_name,
                     date=int(media_db.created_on.timestamp()),
                     dateStr=media_db.created_on.isoformat(),
                     uri=media_db.device_media_uri,
                     size=media_db.media_size_bytes,
                     camera_maker="",
                     camera_model=""))
    yield request_list

@pytest.fixture(scope="session")
def token_fixture():
    with open(f"{os.getcwd()}/tests/data/token_data_30112023113138.pickle",'rb') as file:
        token = pickle.load(file)
    return token

@pytest.fixture(scope="session")
def test_images_list():
    return [f"{os.getcwd()}/tests/data/test.jpg",
            f"{os.getcwd()}/tests/data/test_large.jpg", 
            f"{os.getcwd()}/tests/data/20230406_112401.jpg"]