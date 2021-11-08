import os
import boto3
import random


# pcluster config file has its own sanity check
# if a line starts with '#', it means a comment
# else if a line starts with '[' it means a section is defined
# else if its a blank line, ignore
# else, its a valid line
# a valid line is '=' separated
# left of '=' is key
# right of '=' is value
# if the value starts with $, that means it has to be replaced.
# there is no error check in place



s3 = boto3.resource('s3')
local_template="local.template"

ENV_MASTER_SUBNETS = os.environ.get('ENV_MASTER_SUBNETS').split()
ENV_COMPUTE_SUBNETS = os.environ.get('ENV_COMPUTE_SUBNETS').split()
ENV_MASTER_SUBNETS_VPC2 = os.environ.get('ENV_MASTER_SUBNETS_VPC2').split()
ENV_COMPUTE_SUBNETS_VPC2 = os.environ.get('ENV_COMPUTE_SUBNETS_VPC2').split()
ENV_VPC2_ID = os.environ.get('ENV_VPC2_ID')
ENV_PROXY_SERVER_VPC2 = os.environ.get('ENV_PROXY_SERVER_VPC2')
ENV_PROXY_SERVER = os.environ.get('ENV_PROXY_SERVER')

unwantedTags = ["TSG_TASK"]

def lambda_handler(event, context):
    print(event)
    #1. do_customization
    config_dict = event["pcluster_setup"]
    do_customization(event,config_dict)

    #2. download, instantiate, and upload template
    do_processing(event, config_dict)
    return event

def randomize_instances(config_dict):
    x86= ["m5.2xlarge","c5.2xlarge","m4.2xlarge","m5.2xlarge","c5.2xlarge","m4.2xlarge","m5.4xlarge","c5.4xlarge","m4.4xlarge","m5.4xlarge","c5.4xlarge","m4.4xlarge"]
    #aarch = ["m6g.2xlarge","m6g.4xlarge"]
    aarch = ["m6g.8xlarge","m6g.12xlarge"]

    if "m6g" in config_dict["master_instance_type"]:
        print("m6g instance is chosen in setup")
        config_dict["compute_instance_type"] = random.choice(aarch)
    else:
        print("x86 instance is chosen in setup")
        config_dict["compute_instance_type"] = random.choice(x86)

    if ".2xlarge" in config_dict["compute_instance_type"] :
        config_dict["max_queue_size"] = str(12)
    elif ".4xlarge" in config_dict["compute_instance_type"] :
        config_dict["max_queue_size"] = str(6)
    elif ".8xlarge" in config_dict["compute_instance_type"] :
        config_dict["max_queue_size"] = str(3)  
    elif ".12xlarge" in config_dict["compute_instance_type"] :
        config_dict["max_queue_size"] = str(2)
    else :
        print("Unknown instance type selected. Taking predefined max_queue_size")
    print("Compute instance type : {} , max_queue_size : {}".format(config_dict["compute_instance_type"],config_dict["max_queue_size"]))

def do_customization(event,config_dict):
    config_dict["vpc_id"]=event["vpc"]
    if config_dict["vpc_id"] == ENV_VPC2_ID:
        config_dict["master_subnet_id"]= random.choice(ENV_MASTER_SUBNETS_VPC2)
        config_dict["compute_subnet_id"]=random.choice(ENV_COMPUTE_SUBNETS_VPC2)
        config_dict["proxy_server"]=ENV_PROXY_SERVER_VPC2
    else :
        config_dict["master_subnet_id"]= random.choice(ENV_MASTER_SUBNETS)
        config_dict["compute_subnet_id"]=random.choice(ENV_COMPUTE_SUBNETS)
        config_dict["proxy_server"]=ENV_PROXY_SERVER

    print("VPC:{}".format(config_dict["vpc_id"]))
    print("Master subnet selected :{}".format(config_dict["master_subnet_id"]))
    print("Compute subnet selected :{}".format(config_dict["compute_subnet_id"]))
    print("Proxy server selected :{}".format(config_dict["proxy_server"]))
    randomize_instances(config_dict)
    print("Selected master instance_type {}".format(config_dict["master_instance_type"]))
    print("Selected compute instance_type {}".format(config_dict["compute_instance_type"]))
    mount_target_ip=event["EFS"]["target-ip"]
    print("Max queue size set to :{}".format(config_dict["max_queue_size"]))
    static_post_install_args= config_dict["post_install_args"]
    bucket=event["session_s3_bucket"]
    url = event["session_s3_path"]
    pdk_url="s3://{}/{}/pdk.tgz".format(bucket,url)
    complete_post_install_args="{} {} {}".format(mount_target_ip,static_post_install_args,pdk_url)
    config_dict["post_install_args"]=complete_post_install_args
    config_dict["additional_sg"]=event["SecurityGroups"][0]
    config_dict["tags"]=do_tagging(event["TAGS"])



def do_processing(event, config_dict):

    #1. download
    local_template = download(event)   #/tmp/123456/local.template

    config_name="{}.config".format(event["pcluster_name"])    # 123456-0.config
    local_config="/tmp/{}/{}".format(event["session_id"],config_name)  #  /tmp/123456/123456-0.config

    #2. instantiate
    instantiate(local_template,local_config,config_dict)


    #3.upload
    bucket = event["session_s3_bucket"]
    upload_key = event["session_s3_path"]+"/"+config_name
    s3.meta.client.upload_file(local_config, bucket, upload_key)
    print("Uploading {} to {}/{}".format(local_config, bucket, upload_key))

def instantiate(local_config_template_path, local_config_file_path, config_dict):
    with open(local_config_template_path) as input:
        with open(local_config_file_path, "w") as output:
            for line in input:
                print(line)
                output.write(line_by_line(line, config_dict))
                #output.write("\n")
        output.close()
    input.close()


def download(event):


    template_url=event["pcluster_setup"]["pcluster_config_template_path"].replace("s3://","")
    template_bucket=event["pcluster_setup"]["pcluster_config_template_path"].replace("s3://","").split("/")[0]
    template_key = template_url.split("/",1)[1]
    local_dir = '/tmp/' + event["session_id"]

    if not os.path.exists(local_dir):
        os.makedirs(local_dir)

    local_path="{}/{}".format(local_dir,local_template)

    s3.Bucket(template_bucket).download_file(template_key, local_path)
    return local_path




def line_by_line(line, config_dict):

    if line.startswith('#') or line.startswith("[") or line.startswith('\n'):
        return line
    else:
        parts = line.split('=')
        key = parts[0].strip()
        val_to_replace = parts[1].strip()

        if val_to_replace.startswith("$") and key==val_to_replace.replace("$","").strip():
            value = config_dict[key.lstrip().rstrip()]
            if(key=="post_install_args"):
                value='"{}"'.format(value)
            return key + " = " + value + "\n"

        return line


def do_tagging(inputjsontags):
    print("old tags :{}".format(inputjsontags))
    mapmigrate = {
        "Key": "map-migrated",
        "Value": "d-server-02neur6nspl23a"
    }
    mapmigrateapp= {
        "Key": "map-migrated-app",
        "Value": "d-application-01yhuao027m22y"
    }

    extrajsontags = [mapmigrate, mapmigrateapp]
    
    newTags = {}
#    tags="{"
#    for tag in inputjsontags:
#        for key in tag.keys():
#            tags+='"{}":'.format(tag[key])
#        tags=tags[:-1]+","


#    if "map-migrated" not in tags:
#        for tag in extrajsontags:
#            for key in tag.keys():
#                tags+='"{}":'.format(tag[key])
#            tags=tags[:-1]+","


#    tags=tags[:-1]+"}"

    for tag in inputjsontags:
        newTags[tag["Key"]] = tag["Value"]
    if "map-migrated" not in newTags.keys():
        for tag in extrajsontags:
            print("Adding tag : {}".format(tag))
            newTags[tag["Key"]] = tag["Value"]

    # removing unwanted tags
    for unwantedTag in unwantedTags:
        if unwantedTag in newTags.keys():
                print("removing tag :{}".format(unwantedTag))
                del newTags[unwantedTag]
                
    print (newTags)
    return str(newTags)


