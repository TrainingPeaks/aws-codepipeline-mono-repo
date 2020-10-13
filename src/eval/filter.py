import os
import json
import re
import boto3

S3_BUCKET = os.environ['S3_BUCKET']
S3_PREFIX = os.environ['S3_PREFIX']
s3client = boto3.client('s3')

def handler(event, context):
    repo, branch = extract_info(event)
    infos = get_s3_object_infos(s3client, S3_BUCKET, S3_PREFIX, repo, branch)
    configs = get_configs(s3client, infos)
    for config in configs:
        if is_match(event, config['Matches']):
            start_code_pipeline(config['CodePipelineName'])

def extract_info(event):
    branch = event['ref'].split('/')[-1]
    repo = event['repository']['name']
    return (repo, branch)

def get_s3_object_infos(client, bucket, prefix, repo, branch):
    prefix = build_prefix(prefix, repo, branch)
    list_objects = client.get_paginator('list_objects_v2')
    args = {'Bucket': bucket, 'Prefix': prefix}
    results = []
    for page in list_objects.paginate(**args):
        if 'Contents' in page:
            for info in page['Contents']:
                results.append((bucket, info['Key']))
    return results

def build_prefix(prefix, repo, branch):
    filePart = f'{repo}-{branch}'[:52]
    return f'{prefix}/{filePart}'

def get_configs(client, s3infos):
    configs = []
    for info in s3infos:
        config = json.load(client.get_object(Bucket=info[0], Key=info[1])['Body'])
        config['Matches'] = build_regex_matches(config['ChangeMatchExpressions'])
        configs.append(config)
    return configs

def build_regex_matches(changeMatchExpressions):
    change_matches = []
    for regex in changeMatchExpressions.split(','):
        change_matches.append(re.compile(regex.strip()))
    return change_matches

def is_match(event, regex):
    changes = extract_paths(event)
    for r in regex:
        for change in changes:
            if r.match(change):
                print(f'found match with {r.pattern}')
                return True
    return False

def extract_paths(event):
    changes = []
    for commit in event['commits']:
        for i in ['added', 'removed', 'modified']:
            changes += commit[i]
    return changes

def start_code_pipeline(pipelineName):
    client = codepipeline_client()
    print(f'Starting code pipeline: {pipelineName}')
    response = client.start_pipeline_execution(name=pipelineName)
    print(f'Start response {response}')

cpclient = None
def codepipeline_client():
    import boto3
    global cpclient
    if not cpclient:
        cpclient = boto3.client('codepipeline')
    return cpclient
