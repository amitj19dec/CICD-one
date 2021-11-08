from __future__ import print_function
import boto3
import time
import json
import os


ssm = boto3.client('ssm')

#ENV_SSM_INSTANCE_ID = os.environ.get('ENV_SSM_INSTANCE_ID')

def lambda_handler(event, context):
    #instance_id= "i-07f1d82e6b2e3f60e"
    #instance_id = "i-0f6053893387fffd2"
    instance_id = "i-0a7255febbc7c284d"
    bucket = event["session_s3_bucket"]
    url = event["session_s3_path"]

    name=event["pcluster_name"]
    config="{}.config".format(name)
    src_url="s3://{}/{}/{}".format(bucket,url,config)

    command = "cd /home/centos &&  sudo -u centos /usr/bin/bash create_pcluster_ssm.sh {} {} {}".format(
        src_url,config,name)
    #command = "cd /home/ssm-user && touch testfile"
    print(command)

    run_command_using_ssm([instance_id],[command])
    
    return event


def run_command_using_ssm(instances, commands):
    response = ssm.send_command(
        InstanceIds=instances,
        DocumentName='AWS-RunShellScript',
        TimeoutSeconds=30,
        Comment='boto dir',
        Parameters={"commands":commands})

    cmd_id= response['Command']['CommandId']
    time.sleep(50)
    output = ssm.get_command_invocation(CommandId=cmd_id,InstanceId=instances[0])
    print(output)