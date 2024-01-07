## 0.3.2 (2024-01-07)

### Fix

- **routes/v2/media**: Send Media type to the media_db_service.update function.

## 0.3.1 (2024-01-07)

### Fix

- **publish/service**: service.publish, if object_to_publish is not a list, create one from it and pass it on

## 0.3.0 (2024-01-07)

### Feat

- **main**: Bind publisher to the upload process. Currently only on the full upload process
- **main**: Bind the publisher and UploaderV2 to the main app
- **publisher**: Add publisher component to send message of incomming images
- **routes/users**: Add auth service. Add list_of_devices_ids to the get_devices_list route's response
- **routes_v2/media**: Create v2 api for media routes. Adjust to auth service and add a route that uploads the image and the metadata at once

### Refactor

- **publisher,test_publisher**: Adjust the publisher as service to the project shkedia. The service publishes specific types of message supported by the project's components
- **models/media**: Set the SearchResult.results pydantic to Any. To support multiple result types
- **db/media_service**: Work with project-shkedia-models library. Add retry mechanism for HTTP calls
- **authentication**: Add auth_token to the request to be used by the routes to access other microservices in the system
- **main,AuthService**: Adjust to new AuthService version and bind it to the user_db_service
- **AuthService,sql_models**: Update the AuthService from the MediaDBService. Import the sql_models to implement here

## 0.2.0 (2023-12-07)

### Feat

- **routes/media,models/media,image_processing/service**: Extract more meta data (dimensions, EXIF) from the image and send it to the db
- **encryption/service**: Change the order between compression and encryption

## 0.1.0 (2023-12-03)

### Feat

- **src/ImageProcessingService**: Save image EXIF in thumbnail. Rotate thumbnail according to the orientation tag in the EXIF
- **image_processing/service**: Save the EXIF data to the thumbnail file
- **routes/user,db/user_service**: Create Rest API to the client to deal with all the users functions. Including interface to the auth_service
- **main**: Connect the repo and encryption services to the put_image route
- **repo/service**: Create interface to the repo service
- **models/all**: Adjust to multiple environments
- **models/media**: Add fields to the media object and adjust to multiple environments
- **image_processing/service**: Add function to create thumbnail from image
- **db/service**: Adjust the service to create HTTP requests for the media_db_service
- **routes/media**: Create compatibal RestAPI to handle the images upload process
- **encryption**: Create encryption service for asymmetric and symmetric encryptions
- **main,-config,-models**: Create the basic RestAPI structure

### Fix

- **src/routes/media**: Fix paging mechanism, put_image signature
- **models/user**: Fix type with UserRequest.username
- **routes/media/GetLatestImageResponse**: Get last_image_date from datetime to int (to be compatible with previous version
- **db/service/search_media**: Adjust to SearchResult output from db_media service
- **encryption/service**: Beside "image", encode all fields to b64 after encryption. Add a prefix to mark them for the decryption process

### Refactor

- **authentication/service**: Copy service base from media_db_service. Still under work
- **project**: Create the project base structure from template
