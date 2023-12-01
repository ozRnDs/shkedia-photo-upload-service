import os

from models.media import SearchResult
from authentication.models import Token

def test_get_latest_image_date_no_token(client_fixture, search_result_fixture):
    # SETUP
    params = { "device_id": SearchResult(**search_result_fixture).results[0].device_id ,
              "user_name": "No user" }

    # RUN
    results = client_fixture.get("/images/list/last",params=params)
    
    # ASSERT
    assert results.status_code == 401

def test_get_latest_image_date_fake_token(client_fixture, search_result_fixture):
    # SETUP
    params = { "device_id": SearchResult(**search_result_fixture).results[0].device_id ,
              "user_name": "No user" }
    
    fake_token = Token(access_token="Badtoken", token_type="bearer")

    # RUN
    results = client_fixture.get("/images/list/last",params=params, headers=fake_token.get_token_as_header())
    
    # ASSERT
    assert results.status_code == 401

def test_get_latest_image_date_real_token(client_fixture, search_result_fixture, token_fixture):
    # SETUP
    params = { "device_id": SearchResult(**search_result_fixture).results[0].device_id ,
              "user_name": "No user" }
    
    real_token = Token(**token_fixture)

    # RUN
    results = client_fixture.get("/images/list/last",params=params, headers=real_token.get_token_as_header())
    
    # ASSERT
    assert results.status_code == 200

def test_get_images_to_upload_device_doesnt_exists(client_fixture, search_result_fixture, token_fixture):
    # SETUP
    params = { "device_id": "IdontExist" ,
              "user_name": "No user" }
    
    real_token = Token(**token_fixture)

    # RUN
    results = client_fixture.get("/images/list/next",params=params, headers=real_token.get_token_as_header())
    
    # ASSERT
    assert results.status_code == 400
    assert "not found" in results.json()["detail"]

def test_get_images_to_upload_nominal(client_fixture, search_result_fixture, token_fixture):
    # SETUP
    params = { "device_id": SearchResult(**search_result_fixture).results[0].device_id ,
              "user_name": "No user" }
    
    real_token = Token(**token_fixture)

    # RUN
    results = client_fixture.get("/images/list/next",params=params, headers=real_token.get_token_as_header())
    
    # ASSERT
    assert results.status_code == 200

def test_put_images_metadata_nominal(client_fixture, search_result_fixture, images_request_list, token_fixture):
    # SETUP
    params = { "device_id": SearchResult(**search_result_fixture).results[0].device_id ,
              "user_name": "No user" }
    
    data = [image_request.model_dump() for image_request in images_request_list][0:2]

    real_token = Token(**token_fixture)

    # RUN
    results = client_fixture.post("/images/list",
                                  params=params,
                                  json=data,
                                  headers=real_token.get_token_as_header())
    
    # ASSERT
    assert results.status_code == 200
    assert results.json()["number_of_images_updated"]==len(data)

def test_put_images_metadata_device_doesnt_exists(client_fixture, search_result_fixture, images_request_list, token_fixture):
    # SETUP
    params = { "device_id": "IDontExist" ,
              "user_name": "No user" }
    
    data = [image_request.model_dump() for image_request in images_request_list][0:2]

    real_token = Token(**token_fixture)

    # RUN
    results = client_fixture.post("/images/list",
                                  params=params,
                                  json=data,
                                  headers=real_token.get_token_as_header())
    
    # ASSERT
    assert results.status_code == 500
    assert "None of the images were updated" == results.json()["detail"]

def test_get_images_to_delete_nominal(client_fixture, search_result_fixture, token_fixture):
    # SETUP
    params = { "device_id": SearchResult(**search_result_fixture).results[0].device_id ,
              "user_name": "No user" }
    
    real_token = Token(**token_fixture)

    # RUN
    results = client_fixture.get("/images/delete/next",params=params, headers=real_token.get_token_as_header())
    
    # ASSERT
    assert results.status_code == 200

def test_get_images_to_delete_device_doesnt_exists(client_fixture, search_result_fixture, token_fixture):
    # SETUP
    params = { "device_id": "IDontExists" ,
              "user_name": "No user" }
    
    real_token = Token(**token_fixture)

    # RUN
    results = client_fixture.get("/images/delete/next",params=params, headers=real_token.get_token_as_header())
    
    # ASSERT
    assert results.status_code == 400
    assert "not found" in results.json()["detail"]

def test_put_image_nominal(client_fixture, 
                           search_result_fixture, 
                           token_fixture, 
                           test_images_list):
    #SETUP
    with open(test_images_list[1],'rb') as image_file:
        image_bytes = image_file.read()
    
    files={"image_content": image_bytes}

    image_name = os.path.basename(test_images_list[0])

    real_token = Token(**token_fixture)

    params = { "device_id": SearchResult(**search_result_fixture).results[0].device_id ,
              "user_name": "No user",
               "image_name": image_name,
                "image_id":  search_result_fixture["results"][0]["media_id"],
                "overwrite": True}

    # RUN
    results = client_fixture.put("/images",params=params, files=files ,headers=real_token.get_token_as_header())

    # ASSERT
    assert results.status_code == 200
    assert type(results.json()) == dict
    assert len(results.json()) == 0

def test_put_image_file_exists(client_fixture, 
                           search_result_fixture, 
                           token_fixture, 
                           test_images_list):
    #SETUP
    with open(test_images_list[1],'rb') as image_file:
        image_bytes = image_file.read()
    
    files={"image_content": image_bytes}

    image_name = os.path.basename(test_images_list[0])

    real_token = Token(**token_fixture)

    params = { "device_id": SearchResult(**search_result_fixture).results[0].device_id ,
              "user_name": "No user",
               "image_name": image_name,
                "image_id":  search_result_fixture["results"][0]["media_id"],
                "overwrite": False}

    # RUN
    results = client_fixture.put("/images",params=params, files=files ,headers=real_token.get_token_as_header())

    # ASSERT
    assert results.status_code == 409
    assert "already exists" in results.json()["detail"]