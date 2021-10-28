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
    print(job_name)
    dest_dir="/home/centos"
    
    command2= 'sudo runuser -l  centos -c "chmod 777 {}/{}.job.tgz  & "'.format(dest_dir,job_name)
    print(command2)
    
    command=[command2]
    time.sleep(30)        
    response = ssm.send_command(
            InstanceIds=[instance_id],
            DocumentName='AWS-RunShellScript',
            TimeoutSeconds=60,
            Comment='boto dir',
            Parameters={"commands":command,"executionTimeout":["172800"]})
    
    cmd_id= response['Command']['CommandId']
    time.sleep(10)
    output = ssm.get_command_invocation(CommandId=cmd_id,InstanceId=instance_id)
    #print(output["StandardOutputContent"])
    return event
    
