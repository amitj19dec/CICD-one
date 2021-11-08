import json
import boto3
import time

client = boto3.client('ec2')
def lambda_handler(event, context):
    print(event["pcluster_name"])
    filters =   [
        {   'Name': 'tag:ClusterName', 'Values': [event["pcluster_name"]] },
        {   'Name': 'tag:aws:cloudformation:logical-id', 'Values': ['MasterServer'] },
        {   'Name': 'instance-state-name', 'Values': ['running']}
        
        ]
    
    
    
    # filters = [{
    #      'Name': 'ip-address',
    #      'Values': [public_ip]
    #         }]
    response = client.describe_instances(Filters=filters)
        
    print(response["Reservations"][0]["Instances"])
    instanceId = response["Reservations"][0]["Instances"][0]["InstanceId"]
    ipAddress = response["Reservations"][0]["Instances"][0]["PrivateIpAddress"]
    print(instanceId)
    print(ipAddress)
    event["pcluster"]["masterinstanceid"] = instanceId
    event["pcluster"]["details"] = ipAddress
    print(event)
    return event
    