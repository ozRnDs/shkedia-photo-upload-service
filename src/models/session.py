from pydantic import BaseModel, Field
from typing import Union
from uuid import uuid4
from datetime import datetime, timedelta

class Session(BaseModel):
    session_id: str = Field(default_factory=lambda:str(uuid4()))
    user_id: str
    device_id: str
    session_secret: str
    expiration_date: str = Field(default_factory=lambda:(datetime.now() + timedelta(days=7)).isoformat())
    last_activity: Union[str, None] = None

    @staticmethod
    def __sql_create_table__():
        sql_template = """CREATE TABLE IF NOT EXISTS sessions (
            session_id VARCHAR ( 50 ) PRIMARY KEY,
            user_id VARCHAR ( 50 ) NOT NULL REFERENCES users(user_id),
            device_id VARCHAR ( 50 ) NOT NULL REFERENCES devices(device_id),
            session_secret VARCHAR ( 50 ) UNIQUE NOT NULL,
            expiration_date TIMESTAMP NOT NULL,
            last_activity TIMESTAMP
        )"""
        return sql_template
    
    def __sql_insert__(self):
        sql_template = """INSERT INTO sessions (
            session_id, user_id, device_id, session_secret, expiration_date, last_activity
        ) VALUES (%s, %s, %s, %s, %s, %s)"""
        values = (self.session_id, self.user_id, self.device_id, self.session_secret, self.expiration_date, self.last_activity)
        return sql_template, values

    @staticmethod
    def __sql_select_item__(field_name, field_value):
        sql_template = f"SELECT * FROM sessions WHERE {field_name}=%s"
        return sql_template, (field_value,)

    
