from pydantic import BaseModel, Field
from typing import Union, TypeVar, Type, List, Any
from uuid import uuid4
from datetime import datetime

from enum import Enum

class MediaUploadStatus(str, Enum):
    PENDING="PENDING"
    UPLOADED="UPLOADED"
    DELETED="DELETED"

class MediaDeviceStatus(str, Enum):
    EXISTS="EXISTS"
    DELETED="DELETED"

class MediaType(str, Enum):
    IMAGE="IMAGE"
    VIDEO="VIDEO"

class MediaRequest(BaseModel):
    media_name: str
    media_type: str
    media_size_bytes: int
    # media_description: str # TODO: Add to the SQL table
    media_thumbnail: str | None = None
    created_on: datetime
    device_id: str
    device_media_uri: str  

class MediaResponse(MediaRequest):
    media_id: str = Field(default_factory=lambda:str(uuid4()))
    upload_status: MediaUploadStatus = MediaUploadStatus.PENDING
    media_status_on_device: MediaDeviceStatus = MediaDeviceStatus.EXISTS
    owner_id: str

TMediaModel = TypeVar("TMediaModel", bound=MediaRequest)

class MediaDB(MediaResponse):
    storage_service_name: str | None = None
    storage_bucket_name: str | None = None
    storage_media_uri: str | None = None
    media_key: str | None = None

    def __init__(self, **karg):
        MediaResponse.__init__(self,**karg)

    @staticmethod
    def __sql_create_table__():
        sql_template = """CREATE TABLE IF NOT EXISTS medias (
            media_name VARCHAR ( 250 ) NOT NULL,
            media_type VARCHAR ( 50 ) NOT NULL,
            media_size_bytes INTEGER NOT NULL,
            media_description TEXT,
            media_thumbnail VARCHAR ( 50 ),
            created_on TIMESTAMP NOT NULL,
            device_id VARCHAR ( 50 ) NOT NULL REFERENCES devices(device_id),
            device_media_uri VARCHAR ( 250 ) NOT NULL,
            media_id VARCHAR ( 50 ) PRIMARY KEY,
            upload_status VARCHAR ( 50 ) NOT NULL,
            media_status_on_device VARCHAR ( 50 ) NOT NULL,
            owner_id VARCHAR ( 50 ) NOT NULL REFERENCES users(user_id),
            storage_service_name VARCHAR ( 50 ),
            storage_bucket_name VARCHAR ( 50 ),
            storage_media_uri VARCHAR ( 250 ),
            media_key VARCHAR ( 2048 )
        )"""
        return sql_template
    
    def __sql_insert__(self):
        columns = []
        values = []
        for field_name, field_value in self.model_dump().items():
            if field_value:
                columns.append(field_name)
                values.append(field_value)

        sql_template = "INSERT INTO medias (" + ",".join(columns) + ") VALUES ("+",".join(["%s"]*len(columns))+")"
        values = (tuple)(values)
        return sql_template, values

    @staticmethod
    def __sql_select_item__(field_names, field_values):
        sql_template = f"SELECT * FROM medias WHERE"
        search_string = []
        sql_values=[]
        for field_index, field_name in enumerate(field_names):
            field_search = f"{field_name} IN (" + ",".join(["%s"]*len(field_values[field_index])) + ")"
            search_string.append(field_search)
            sql_values+=field_values[field_index]
        sql_template += " "+" AND ".join(search_string)
        return sql_template, (tuple)(sql_values)

    def __sql_update_item__(self,updated_model):
        update_dictionary = self.__get_updated_values__(updated_model=updated_model)
        if len(update_dictionary)==0:
            raise AttributeError("Nothing to update")
        values = []
        update_list = []
        sql_template = "UPDATE medias SET "
        for field_name, field_value in update_dictionary.items():
            if not field_value:
                update_list.append(f"{field_name}=''")
                continue
            update_list.append(f"{field_name}=%s")
            values.append(field_value)
        sql_template += ",".join(update_list)
        sql_template += " WHERE media_id=%s"
        values.append(self.media_id)

        values = (tuple)(values)
        return sql_template, values

    def convert_type(self, target_model: Type[TMediaModel]) -> TMediaModel:
        input_dict = {}
        source_dict = self.model_dump()
        for field_name in target_model.model_fields:
            if field_name in source_dict and source_dict[field_name]:
                input_dict[field_name]=source_dict[field_name]
        return target_model(**input_dict)
    
class SearchResult(BaseModel):
    total_results_number: int
    page_number: int = 0
    page_size: int | None = None
    results: List[MediaDB]