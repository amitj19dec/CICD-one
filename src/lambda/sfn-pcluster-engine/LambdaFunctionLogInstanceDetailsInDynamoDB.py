import json
import boto3
import decimal
import os
from datetime import datetime
from boto3.dynamodb.conditions import Key, Attr

#Environment

ENV_CLUSTER_TABLE_NAME = os.environ.get('ENV_CLUSTER_TABLE_NAME')
ENV_REGION = os.environ['AWS_REGION']



dynamodb = boto3.resource('dynamodb', region_name=ENV_REGION)
table=dynamodb.Table(ENV_CLUSTER_TABLE_NAME)

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)
def lambda_handler(event,context):
    pcluster_name=event["pcluster_name"]
    created_at= datetime.now().replace(microsecond=0).isoformat()
    pcluster_status=event["pcluster"]["status"] if "details" in event["pcluster"] else "CREATION_FAILED"
    master_ip= event["pcluster"]["details"] if "details" in event["pcluster"] else "NA"
    masterinstanceid=event["pcluster"]["masterinstanceid"] if "details" in event["pcluster"] else "NA"
    availability="FREE" if "details" in event["pcluster"] else "CREATION_FAILED"
    efs=event["EFS"]['FileSystemId']
    session_url="{}/{}".format(event["session_s3_bucket"],event["session_s3_path"])
    count=0
    

    response = table.put_item(
        Item={
            'pcluster_name': pcluster_name,
            'created_at': created_at,
            'updated_at': created_at,
            'session_id': event["session_id"],
            'pcluster_status':pcluster_status,
            'master_ip':master_ip,
            'masterinstanceid' : masterinstanceid,
            'session_url' : session_url,
            'FileSystemId' : efs,
            'availability':availability,
            'workload_count': count
        }
    )
