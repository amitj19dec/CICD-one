import json
import subprocess
import logging
import os
import boto3



logger = logging.getLogger()
logger.setLevel(logging.INFO)
def download_pclusterconfig(event):
    s3 = boto3.resource('s3')
    name = event["pcluster_name"]
    config = "{}.config".format(name)
    url = event["session_s3_path"]
    bucket = event["session_s3_bucket"]
    
    url_key = "{}/{}".format(url,config)

    session_id = event["session_id"]
    local_slashTmp= '/tmp/' + session_id

    if not os.path.exists(local_slashTmp):
        os.makedirs(local_slashTmp)
    
    local_copy= "{}/{}".format(local_slashTmp,config)
    s3.Bucket(bucket).download_file(url_key,local_copy)
    return local_copy
    
    
def construct_command(conf, pcluster_name):
    return "/opt/pcluster status -c {} {} -nw".format(conf,pcluster_name)


def run_command(command):

    command_list = command.split(' ')
    status='NOT_FOUND'

    try:
        logger.info("Running shell command: \"{}\"".format(command))
        result = subprocess.run(command_list, stdout=subprocess.PIPE);
        output=result.stdout.decode('UTF-8').lstrip().rstrip()
        logger.info("Command output:\n---\n{}\n---".format(output))

        #reading status
        for val in output.split("\n"):
            if val.strip().startswith("Status"):
                print("Got:: "+val)
                return val.rsplit(":",1)[1].strip()

    except Exception as e:
        logger.error("Exception: {}".format(e))
        

    return status

def lambda_handler(event, context):
    conf = download_pclusterconfig(event)
    print(conf)
    pcluster_name=event["pcluster_name"]
    print("Checking tatus of pcluster {}".format(pcluster_name))
    command = construct_command(conf, pcluster_name)
    print(command)
    response = run_command(command)
    return response

