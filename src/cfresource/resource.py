import os
from dataclasses import dataclass, asdict, field, fields
import hashlib
import json
import boto3
import requests

PHYSICAL_RESOURCE_ID = 'GitHubIntegrationMonoRepoS3ConfigResource'
S3_BUCKET = os.environ['S3_BUCKET']
S3_PREFIX = os.environ['S3_PREFIX']
s3client = boto3.client('s3')

def handler(event, context):
    print(event)
    try:
        request_type = event['RequestType']
        properties = extract_and_validate_properties(event, 'ResourceProperties')
        file_name = get_filename(properties)
        EVENT_MAP[request_type](event, properties, file_name)
        response = success(event, None)
    except Exception as e:
        response = failure(event, repr(e))
    finally:
        send_response(event['ResponseURL'], response)

def handle_create(event, properties, filename):
    put_s3(s3client, S3_BUCKET, get_s3_key(filename), props_to_config_data(properties), 'application/json')

def handle_update(event, properties, filename):
    oldProperties = extract_and_validate_properties(event, 'OldResourceProperties')
    oldFilename = get_filename(oldProperties)
    delete_s3(s3client, S3_BUCKET, get_s3_key(oldFilename))
    put_s3(s3client, S3_BUCKET, get_s3_key(filename), props_to_config_data(properties), 'application/json')

def props_to_config_data(properties):
    data = asdict(properties)
    if 'ServiceToken' in data:
        del data['ServiceToken']
    return json.dumps(data).encode()

def get_s3_key(filename):
    return f'{S3_PREFIX}/{filename}.json'

def put_s3(client, bucket, key, body, contentType):
    client.put_object(Bucket=S3_BUCKET, Key=key, Body=body, ContentType=contentType)

def delete_s3(client, bucket, key):
    client.delete_object(Bucket=bucket, Key=key)

def handle_delete(event, properties, filename):
    delete_s3(s3client, S3_BUCKET, get_s3_key(filename))

EVENT_MAP = {
    'Create': handle_create,
    'Update': handle_update,
    'Delete': handle_delete
}

@dataclass
class ResourceProperties:
    GitHubRepo: str
    GitHubBranch: str
    ChangeMatchExpressions: str
    CodePipelineName: str
    ServiceToken: str = field(default=None)

def extract_and_validate_properties(event, key):
    raw_properties = event[key]
    properties = {}
    required = fields(ResourceProperties)
    for f in [f for f in required if f.default]:
        if f.name not in raw_properties:
            raise ValueError(f'Property {f.name} is missing from the event {properties}')
        properties[f.name] = raw_properties[f.name]

    return ResourceProperties(**properties)

def get_filename(properties):
    fulltext = f'{properties.GitHubRepo}-{properties.GitHubBranch}-{properties.CodePipelineName}'
    hash = hashlib.sha1(fulltext.encode()).hexdigest().upper()
    return f'{fulltext[:52]}-{hash[:8]}'

def failure(request, reason):
    print(f'Failed: reason={reason}')
    print(f'Failed: request={request}')
    return get_response(request, False, reason=reason)

def success(request, data):
    return get_response(request, True, data=data)

def get_response(request, success, reason='', data=None):
    response = {
        'RequestId': request['RequestId'],
        'LogicalResourceId': request['LogicalResourceId'],
        'StackId': request['StackId'],
        'PhysicalResourceId': request.get('PhysicalResourceId', PHYSICAL_RESOURCE_ID)
    }
    if success:
        response['Status'] = 'SUCCESS'
        if data:
            response['Data'] = data
    else:
        response['Status'] = 'FAILED'
        response['Reason'] = reason

    return response

def send_response(url, data):
    requests.put(url, json=data)
