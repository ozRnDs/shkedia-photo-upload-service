import io
import PIL
from PIL import Image, ExifTags
import base64
import logging
logger = logging.getLogger(__name__)

class ImageProcessingService:

    def __init__(self, 
                 thumbnail_width_size: int=400,
                 thumbnail_height_size: int=200):
        self.thumbnail_width_size = thumbnail_width_size
        self.thumbnail_height_size = thumbnail_height_size

    def get_image_thumbnail_bytes(self, image_file) -> bytes:
        try:
            temp_image = Image.open(image_file)
            exif_dict = temp_image._getexif()
            exif_dict = ImageProcessingService.parse_exif(exif_dict)
            temp_image = ImageProcessingService.rotate_image(temp_image)
            exif=None
            if "exif" in temp_image.info:
                exif = temp_image.info['exif']

            w,h = temp_image.size
            image_aspect_ratio = h/w
            image_format = temp_image.format
            if image_format is None:
                image_format="JPEG"
            temp_image = temp_image.resize((self.thumbnail_width_size, int(self.thumbnail_width_size*image_aspect_ratio)))
            thumbnail_w,thumbnail_h = temp_image.size
            mem_file = io.BytesIO()
            if exif:
                temp_image.save(mem_file, format=image_format, exif=exif)
            else:
                temp_image.save(mem_file, format=image_format)
            image_byte_array = mem_file.getvalue()
            mem_file.close()
            # target_file = io.StringIO()
            # temp_image.save(target_file)
            # temp_image.close()
            return image_byte_array, (w,h), (thumbnail_w, thumbnail_h),exif_dict
        except Exception as err:
            raise Exception(f"Failed to create thumbnail to image: {str(err)}")

    @staticmethod
    def parse_exif(exif) -> dict:
        if exif is None:
            return None
        tagged_exif = {ExifTags.TAGS[key]:value for key,value in exif.items()}
        floating_exif = {key:float(value.real) for key,value in tagged_exif.items() if type(value)==PIL.TiffImagePlugin.IFDRational}
        binary_exif = {key:value.decode() for key,value in tagged_exif.items() if type(value)==bytes}
        tagged_exif.update(floating_exif)
        tagged_exif.update(binary_exif)

        return tagged_exif
        
        
    
    @staticmethod
    def rotate_image(image: Image) -> str:
        try:
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

            return image
        
        except (AttributeError, KeyError, IndexError, TypeError):
            logger.info("Image doesn't have tags :(")
            return image
            pass
        
