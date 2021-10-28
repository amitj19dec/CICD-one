from __future__ import print_function
import boto3
import time
ssm = boto3.client('ssm')

def lambda_handler(event, context):
    
    if "job_url" not in event:
        return event
    
    instance_id=event["masterinstanceid"]
    job_url="s3://{}".format(event["job_url"])
    job_name=job_url.split("/")[-1]
    dest_dir="/home/centos"
    
    command = 'sudo runuser -l  centos -c "aws s3 cp --recursive {} {}  &"'.format(job_url,dest_dir)
    print(command)
    #command = "sudo -u centos touch /home/centos/amitssmfile "
    #tested
    
            
    response = ssm.send_command(
            InstanceIds=[instance_id],
            DocumentName='AWS-RunShellScript',
            TimeoutSeconds=30,
            Comment='boto dir',
            Parameters={"commands":[command],"executionTimeout":["172800"]})
    
    cmd_id= response['Command']['CommandId']
    time.sleep(10)
    output = ssm.get_command_invocation(CommandId=cmd_id,InstanceId=instance_id)
    print(output)
    print(output["StandardOutputContent"])
    return event
    
