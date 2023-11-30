# shkedia-photo-upload-service
# Overview
The upload service for the ShkediPhoto Private Cloud System.  
The components main responsibilities:
1. Handling communication between the existing Android App Client (need to keep compatibility with the existing HTTP RestAPI)
2. Encrypt the data (images and metadata)
3. Manage the upload process and sync between the media_repo and media_db components

## The service actions
### Upload Images Process - V1 (compatible with current app)
| Method | Route | Description | Input | Success Output | Notes |
| -- | -- | -- | -- | -- | -- |
| GET | /images/list/last?user_name=?device_id=? | Get the list image uploaded for a device | **Query Params:** user_name, device_id | **Body:** { last_image_date: str? } | - |
| POST | /images/list?user_name=&device_id= | Upload list of images to the db (only metadata) | **Query Params:** user_name, device_id **Body:** list of ImageRequest class | **Body:** { "number_of_images_updated": int } | Should change to PUT in the future |
| GET | /images/list/next?user_name=?device_id=?image_index= | Get the next image to be uploaded to the device | **Query Params:** user_name, device_id, image_index | **Body:** GetUploadListResponse | image_index is image number from where to start the second batch of results (Paging Mechanism). The page_size is defined by the service default |
| PUT | /images?user_name=&device_id=&image_name=&image_id | Upload image to the repo | **Query Params:** user_name, device_id, image_name, image_id **Body:** The image | **Body:** {} | - |
| GET | /images/delete/next?user_name=&device_id= | Get the next image that can be deleted from the device | **Query Params:** user_name, device_id | **Body:** { "uri_list": List[str] } | - |
| DELETE | /images?user_name=&device_id= | Update the device_image_status to be DELETED to the images in the list | **Query Params:** user_name, device_id **Body:** images_list | {} | Should change to POST in the future, because it's updating the DB not deleting anything |

#### API Objects
```python
class ImageRequest:
    name: str
    date: datetime
    uri: str
    size: int
    camera_model: str
    camera_maker: str

class GetUploadListResponse:
    images_names: List[str] # List of the field image_device_name values
    images_ids: List[str] # List of the db's id field values
    images_uri: List[str] # List of the field image_device_uri values
```

### Handle media
| Method | Route | Description | Input | Output | Notes |
| -- | -- | -- | -- | -- | -- |
| PUT | /v1/media | Upload new media information | MediaRequest Model | MediaDB Object | The device_id is the most important owner. In the future should be retreived by the token |
| GET | /v1/media/search?page_size=&page_number=&<search_field> | Get a media or list of medias according to the search parameters. The search parameters are fields in the MediDB Object | *page_size* - number of results if single http request<br>*page_number* - The specific "result page" that was retreived<br> *<search_field>* - Property to search by. **Example:** media_name=Test_Media&media_name=Test_Media2 -> will get all the medias with either names  | MediaDB or SearchResult objects | - |
| GET | /v1/media/{media_id} | Equals to path *v1/media/search?media_id= | media_id | MediaDB Object | - |
| DELETE | /v1/media/{media_id} | Deletes media from the db | media_id | MediaDB Object | NOT IMPLEMENTED |
| POST | /v1/media | Updates the media sent in the body | MediaDB object | MediaDB Object |


# Deploy
## Local Deployment
1. Set the location of the credentials files on the host:
    ```bash
    export UPLOAD_SERVICE_VERSION=0.0.1
    ```
1. Create credentials token files as follows:
    ```bash
    # Create the folder to be mounted to the container
    if [ ! -d $HOST_MOUNT ]; then
        sudo mkdir $HOST_MOUNT
        sudo chown $USER $HOST_MOUNT
    fi
1. Create *upload_env.env* file in .local folder with the service variables:
    ```bash
    export CREDENTIALS_FOLDER_NAME=/temp
    export AUTH_DB_CREDENTIALS_LOCATION=$CREDENTIALS_FOLDER_NAME/postgres_credentials.json

    if [ ! -d .local ]; then
        sudo mkdir .local
    fi
    cat << EOT > .local/upload_service.env
    CREDENTIALS_FOLDER_NAME=$CREDENTIALS_FOLDER_NAME
    JWT_KEY_LOCATION=$CREDENTIALS_FOLDER_NAME/jwt_token
    EOT
    ```
1. Run the service using compose command:
    ```bash
    docker compose up -d
    ```
1. The env can be override by the following command:
    ```bash
    export UPLOAD_ENV=.local/upload_service.env
    docker compose --env-file ${UPLOAD_ENV} up -d
    ```

# Development
## Environment

## Build
1. Set the parameters for the build
    ```bash
    export UPLOAD_SERVICE_VERSION=$(cz version -p)
    export IMAGE_NAME=shkedia-photo-upload-service:${UPLOAD_SERVICE_VERSION}
    export IMAGE_FULL_NAME=public.ecr.aws/q2n5r5e8/ozrnds/${IMAGE_NAME}
    ```
2. Build the image
    ```bash
    docker build . -t ${IMAGE_FULL_NAME}
    ```
3. Push the image
    ```bash
    docker push ${IMAGE_FULL_NAME}
    ```
    Before pushing the image, make sure you are logged in

## Test
### Running Tests
1. Make sure you have all the requirements_dev.txt installed. It is essential for the tests
    ```bash
    pip install -r requirements_dev.txt
    ```
1. Run the tests using CLI
    ```bash
    pytest -s tests
    ```
    **IMPORTANT**: Many of the tests need a connection to the sql server as they are integration tests.
**NOTE**: It is possible and easy to run the tests using VScode. Just press the "play" arrow. All the configuration for it are in the .vscode folder. Just make sure to install the Python Extension