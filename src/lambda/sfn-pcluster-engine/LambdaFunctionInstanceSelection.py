import json
import random

def lambda_handler(event, context):
    if "instance_type" not in event["EFS"]:
        #instances = ["c5.4xlarge", "m5.4xlarge", "m4.4xlarge","m5.2xlarge","c5.2xlarge","m4.2xlarge","m5.2xlarge","c5.2xlarge","m4.2xlarge"]
        instances = ["m5.2xlarge","c5.2xlarge","m4.2xlarge","m5.2xlarge","c5.2xlarge","m4.2xlarge"]

        #instances = ["m6g.4xlarge"]
        return  random.choice(instances)
    else:
        return event["EFS"]["instance_type"]