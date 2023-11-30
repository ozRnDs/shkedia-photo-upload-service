import io
import base64
import zlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding

class EncryptService:

    def __init__(self,
                public_key_location: str=None,
                private_key_location: str=None) -> None:
        
        self.padding_function = padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),
                                algorithm=hashes.SHA256(),
                                label=None)
        if public_key_location:
            self.public_key = self.__load_public_key__(public_key_location)
        if private_key_location:
            self.private_key_location = private_key_location

    def __load_public_key__(self,public_key_location) -> bytes:
        with open(public_key_location, "rb") as key_file:
            loaded_public_key = serialization.load_pem_public_key(key_file.read())
        return loaded_public_key

    def __load_private_key__(self) -> bytes:
        with open(self.private_key_location, "rb") as key_file:
            loaded_private_key = serialization.load_pem_private_key(key_file.read(),
                                                            password=None)
        return loaded_private_key

    def encrypt(self, values_to_encrypt: dict[str,bytes]) -> tuple:
        temp_dict = values_to_encrypt.copy()
        encryptor, encrypted_key = self.__prepare_encryptor__()
        for key, value in temp_dict.items():
            temp_encrypted = encryptor.encrypt(value)
            temp_dict[key]=zlib.compress(temp_encrypted)
            if key=="media_thumbnail":
                values_to_encrypt[key] = base64.b64encode(temp_dict[key]).decode()
        return temp_dict, encrypted_key

    def decrypt(self, encrypted_key, values_to_decrypt: dict[str,bytes]) -> dict[str, bytes]:
        temp_dict = values_to_decrypt.copy()
        loaded_private_key = self.__load_private_key__()
        decrypted_key = loaded_private_key.decrypt(encrypted_key,self.padding_function)
        del loaded_private_key
        decryptor = Fernet(decrypted_key)
        del decrypted_key
        for key, value in temp_dict.items():
            if key=="media_thumbnail":
                value=base64.b64decode(temp_dict[key].encode())
            temp_decompressed = zlib.decompress(value)
            temp_dict[key] = decryptor.decrypt(temp_decompressed)
        return temp_dict

    def __prepare_encryptor__(self):
        symmetric_key = Fernet.generate_key()
        encryptor = Fernet(symmetric_key)
        encrypted_key = self.public_key.encrypt(symmetric_key,self.padding_function)
        del symmetric_key
        return encryptor, encrypted_key