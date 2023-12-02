import io
from PIL import Image, ExifTags
import base64

class ImageProccessingService:

    def __init__(self, 
                 thumbnail_size: int=200):
        self.thumbnail_size = thumbnail_size

    def get_image_thumbnail_bytes(self, image_file) -> bytes:
        temp_image = Image.open(image_file)
        exif = temp_image.info['exif']
        temp_image.thumbnail((self.thumbnail_size,self.thumbnail_size))
        mem_file = io.BytesIO()
        temp_image.save(mem_file, format=temp_image.format, exif=exif)
        image_byte_array = mem_file.getvalue()
        mem_file.close()
        # target_file = io.StringIO()
        # temp_image.save(target_file)
        # temp_image.close()
        return image_byte_array

    @staticmethod
    def rotate_image(image_file) -> str:
        try:
            # image = Image.open(io.BytesIO(image_bytes))
            image = Image.open(image_file)

            for orientation in ExifTags.TAGS.keys():
                if ExifTags.TAGS[orientation]=="Orientation":
                    break

            exif = image._getexif()

            if exif[orientation] == 3:
                image=image.rotate(180, expand=True)
            elif exif[orientation] == 6:
                image=image.rotate(270, expand=True)
            elif exif[orientation] == 8:
                image=image.rotate(90, expand=True)
            with io.BytesIO() as file:
                image.save(file, format=image.format)
                image_bytes=file.getvalue()
            return image_bytes
        
        except (AttributeError, KeyError, IndexError):
            logger.info("Image doesn't have tags :(")
            return image_bytes
            pass
        
