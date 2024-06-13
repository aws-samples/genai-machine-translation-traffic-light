import logging
import os
import cfnresponse

import boto3
from crhelper import CfnResource

helper = CfnResource(json_logging=False, log_level="DEBUG", boto_level="CRITICAL")

logger = logging.getLogger()
logger.setLevel(os.getenv("LogLevel", logging.INFO))
ddb = boto3.client("dynamodb")

PROMPTS_DIR = "prompts"
DDBTABLENAME = os.getenv("DDBTableName")

@helper.create
@helper.update
def create(event, context):
    try:
        for filename in os.listdir(PROMPTS_DIR):
            with open(f"{PROMPTS_DIR}/{filename}", "r") as f:
                response = ddb.put_item(TableName=DDBTABLENAME, Item={"prompt-id": {"S": filename.split(".")[0]}, 
                                                                      "prompt": {"S": f.read()}})
        cfnresponse.send(event, context, cfnresponse.SUCCESS, response)
    except Exception as e:
        cfnresponse.send(event, context, cfnresponse.FAILED, response)


@helper.delete
def delete(event, context):
    cfnresponse.send(event, context, cfnresponse.SUCCESS)


def handler(event, context):
    helper(event, context)
