import json
import boto3
import decimal
import os
from datetime import datetime
from boto3.dynamodb.conditions import Key, Attr

#Environment
ENV_JOB_STATUS_TABLE_NAME = os.environ.get('ENV_JOB_STATUS_TABLE_NAME')
ENV_CLUSTER_TABLE_NAME = os.environ.get('ENV_CLUSTER_TABLE_NAME')
ENV_REGION = os.environ['AWS_REGION']

dynamodb = boto3.resource('dynamodb', region_name=ENV_REGION)
cluster_table = dynamodb.Table(ENV_CLUSTER_TABLE_NAME)
job_status_table = dynamodb.Table(ENV_JOB_STATUS_TABLE_NAME)


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)

def schedule_job(event,pcluster_item, job_item):

    current_time = datetime.now().replace(microsecond=0).isoformat()
    job_item["job_state"]="running"
    job_item["pcluster_name"]=pcluster_item["pcluster_name"]
    job_item["start_time"]=datetime.now().replace(microsecond=0).isoformat()
    job_status_table.put_item(Item=job_item)
    pcluster_item["availability"]="BUSY"
    pcluster_item["updated_at"]=current_time
    pcluster_item["workload_count"]=str(int(pcluster_item["workload_count"])+1)
    print("putting item to cluster table")
    cluster_table.put_item(Item=pcluster_item)
    event["job_url"]=job_item["job_url"]
    event["pcluster_item"]=pcluster_item["pcluster_name"]
    event["masterinstanceid"]=pcluster_item["masterinstanceid"]

def idle_cluster(session_id, architecture, platform):

    #first check if any cluster is FREE from the session_id
    item=get_idle_cluster_session(session_id)
    if item != None:
        return item
    item=get_idle_cluster_from_all("{}/{}".format(platform,architecture))
    if item !=None:
        return item
    item = get_idle_cluster_from_all("{}/".format(platform))
    return item

def waiting_job(session_id, architecture, platform):
    item=get_waiting_job_session(session_id)
    if item !=None:
        return item
    item = get_waiting_job_all("{}/{}".format(platform,architecture))
    if item !=None:
        return item
    item = get_waiting_job_all("{}/".format(platform))
    return item
def lambda_handler(event, context):
    if "session_url" not in event:
        return event
    session_id=event["session_id"]
    platform = event["session_url"].split("/")[2]
    architecture= event["session_url"].split("/")[3].split("_")[0]
    print(session_id)
    pcluster_item = idle_cluster(session_id, architecture, platform)

    job_item = None
    if pcluster_item == None:
        event["info"]="no FREE pclusters available from session {} or architecture {} or platform {}".format(session_id,architecture,platform)
    else:
        job_item = waiting_job(session_id, architecture, platform)
        if job_item == None:
            event["info"]="No waiting jobs found to run in session {} or architecture {} or platform {}".format(session_id,architecture,platform)

    if job_item != None:
        schedule_job(event,pcluster_item,job_item)
    return event

def get_idle_cluster_session(session_id):
    response = cluster_table.scan(
        FilterExpression=Attr("session_id").eq(session_id) &
                         Attr("availability").eq('FREE') &
                         Attr("pcluster_status").eq('CREATE_COMPLETE'))
    for i in response['Items']:
        return i
    while 'LastEvaluatedKey' in response:
        response = cluster_table.scan(
            FilterExpression=Attr("session_id").eq(session_id) &
                             Attr("availability").eq('FREE') &
                             Attr("pcluster_status").eq('CREATE_COMPLETE'),
            ExclusiveStartKey=response['LastEvaluatedKey']
        )
        for i in response['Items']:
            return i

def get_idle_cluster_from_all(search_str):
    print("getting idle pclusters for",search_str)
    response = cluster_table.scan(
        FilterExpression=Attr("session_url").contains(search_str) &
                         Attr("availability").eq('FREE') &
                         Attr("pcluster_status").eq('CREATE_COMPLETE'))
    for i in response['Items']:
        print(i)
        return i
    while 'LastEvaluatedKey' in response:
        response = cluster_table.scan(
            FilterExpression=Attr("session_url").contains(search_str)  &
                             Attr("availability").eq('FREE') &
                             Attr("pcluster_status").eq('CREATE_COMPLETE'),
            ExclusiveStartKey=response['LastEvaluatedKey']
        )
        for i in response['Items']:
            print(i)
            return i

def get_waiting_job_session(session_id):
    response = job_status_table.scan(
        FilterExpression=Attr("session_id").eq(session_id)  & Attr("job_state").eq('waiting') )
    for i in response['Items']:
        return i
    while 'LastEvaluatedKey' in response:
        response = job_status_table.scan(
            FilterExpression=Attr("session_id").eq(session_id) & Attr("job_state").eq('waiting'),
            ExclusiveStartKey=response['LastEvaluatedKey']
        )
        for i in response['Items']:
            return i

def get_waiting_job_all(search_str):

    response = job_status_table.scan(
        FilterExpression=Attr("job_url").contains(search_str) & Attr("job_state").eq('waiting') )
    for i in response['Items']:
        print(i)
        return i

    while 'LastEvaluatedKey' in response:
        response = job_status_table.scan(
            FilterExpression=Attr("job_url").contains(search_str) & Attr("job_state").eq('waiting'),
            ExclusiveStartKey=response['LastEvaluatedKey']
        )
        for i in response['Items']:
            return i

