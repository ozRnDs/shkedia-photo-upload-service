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
