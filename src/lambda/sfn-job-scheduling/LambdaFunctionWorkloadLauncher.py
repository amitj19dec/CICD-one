from __future__ import print_function
import boto3
import time
ssm = boto3.client('ssm')

def lambda_handler(event, context):
    if "job_url" not in event:
        return event
    instance_id=event["masterinstanceid"]
    command = 'sudo runuser -l  centos -c "cd /home/centos && /home/centos/solido-launcher.sh &> solido-launcher.out &"'


    response = ssm.send_command(
        InstanceIds=[instance_id],
        DocumentName='AWS-RunShellScript',
        TimeoutSeconds=30,
        Comment='boto dir',
        Parameters={"commands":[command],"executionTimeout":["172800"]})

    cmd_id= response['Command']['CommandId']
    time.sleep(10)
    output = ssm.get_command_invocation(CommandId=cmd_id,InstanceId=instance_id)
    print(output["StandardOutputContent"])

