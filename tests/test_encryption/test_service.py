import pytest
import io
from PIL import Image

from encryption.service import EncryptService

@pytest.fixture(scope="module")
def encrypt_service_fixture():
    return EncryptService(public_key_location="/temp/data.pub",
                          private_key_location="/temp/data")

def test_symmetic_encryption_text(encrypt_service_fixture: EncryptService):
    # SETUP

    message = b"What am I?"
    result_encryptor, result_key = encrypt_service_fixture.__prepare_encryptor__()
    
    # RUN
    encrypted_message = result_encryptor.encrypt(message)

    result_message = result_encryptor.decrypt(encrypted_message)
    
    assert result_message == message
    assert encrypted_message != message
    
def test_symmetic_encryption_image(encrypt_service_fixture: EncryptService, test_images_list):
    # SETUP
    image_path = test_images_list[0]
    image_file = Image.open(image_path)
    image_bytes = io.BytesIO()
    image_file.save(image_bytes, format=image_file.format)
    image_bytes_array = image_bytes.getvalue()
    image_bytes.close()
    result_encryptor, result_key = encrypt_service_fixture.__prepare_encryptor__()

    # RUN
    encrypted_image = result_encryptor.encrypt(image_bytes_array)

    result_image_bytes = result_encryptor.decrypt(encrypted_image)

    result_image_file = Image.open(io.BytesIO(result_image_bytes))

    decrypted_image_path = image_path.replace(".jpg","-decrypted.jpg")
    result_image_file.save(decrypted_image_path)

def test_encryption(encrypt_service_fixture: EncryptService, test_images_list):
    # SETUP
    values_to_encrypt={}
    values_to_encrypt["image"]=b"This is a message to the world"
    values_to_encrypt["thumbnail"]=b"But you can't here it"

    # RUN
    encrypted_values, encrypted_key = encrypt_service_fixture.encrypt(values_to_encrypt)   

    result_decrypted_values = encrypt_service_fixture.decrypt(encrypted_key,encrypted_values)
    # ASSERT

    for key, value in values_to_encrypt.items():
        result_decrypted_values[key]=value