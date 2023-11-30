import io
from PIL import Image
import base64

class ImageProccessingService:

    def __init__(self, 
                 thumbnail_size: int=200):
        self.thumbnail_size = thumbnail_size

    def get_image_thumbnail_bytes(self, image_file) -> bytes:
        temp_image = Image.open(image_file)
        temp_image.thumbnail((self.thumbnail_size,self.thumbnail_size))
        mem_file = io.BytesIO()
        temp_image.save(mem_file, format=temp_image.format)
        image_byte_array = mem_file.getvalue()
        mem_file.close()
        # target_file = io.StringIO()
        # temp_image.save(target_file)
        # temp_image.close()
        return image_byte_array
        
