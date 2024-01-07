from publisher.service import PublisherService, TimestampLogger, ActionsEnum

import pytest
from datetime import datetime

from project_shkedia_models.media import MediaIDs, MediaTypeEnum

@pytest.fixture(scope="module")
def publisher_service_fixture():
    publisher = PublisherService(topic_names=["test_me"], 
                                 name="upload_test",
                                 id="random_id")
    
    yield publisher


def test_publish(publisher_service_fixture):
    #SETUP
    timestamps_object = TimestampLogger.getLogger("Start Test")
    TOPIC_NAME = "test_me"
    object_to_publish = MediaIDs(device_id="test_device",
                                 owner_id="test_owner",
                                 created_on=datetime.now(),
                                 media_name="something",
                                 media_type=MediaTypeEnum.IMAGE)
    timestamps_object = TimestampLogger.getLogger("Created object to test")

    # Run
    publisher_service_fixture.publish(topic_name=TOPIC_NAME, 
                                      object_to_publish=object_to_publish,
                                      action=ActionsEnum.PUT,
                                      timestamps=timestamps_object)
    