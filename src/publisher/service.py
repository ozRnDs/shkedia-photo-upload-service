import traceback
import logging
logger = logging.getLogger(__name__)

import boto3
from .sns_wrapper import SnsWrapper
from typing import List

class PublisherService:
    def __init__(self,
                 topic_names: List[str],
                 environment: str = "test"
                 ) -> None:
        self.sns_service = SnsWrapper(boto3.resource("sns"))
        self.topic_names = topic_names
        self.topics = {}
        for topic_name in self.topic_names:
            if len(topic_name)>0 and type(topic_name)==str:
                self.topics[topic_name] = self.sns_service.create_topic(topic_name+"_"+self.environment)

    def publish(self, topic_name, message, message_id):
        try:
            self.sns_service.publish_message(self.topics[topic_name],message.model_dump_json(),message_id)
        except Exception as err:
            traceback.print_exc()
            logger.error(err)
            raise err