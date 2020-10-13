import os
import hmac
from hashlib import sha1
import json
import boto3

SECRET = os.environ['GITHUB_SECRET'].encode('utf-8')
EVAL_FUNCTION_ARN = os.environ['EVAL_FUNCTION_ARN']

lambdaclient = boto3.client('lambda')

def handler(request, context):
    if not verify_signature(request):
        return unauthorized()

    return handle_event(request)

def handle_push_event(request):
    payload = json.loads(request['body'])
    print(f'Invoking eval function {EVAL_FUNCTION_ARN}')
    invoke_function(EVAL_FUNCTION_ARN, json.dumps(payload))
    return success()

def invoke_function(arn, payload):
    response = lambdaclient.invoke_async(FunctionName=arn, InvokeArgs=payload)
    if response['Status'] != 202:
        print(f'Ack! Invoke failed: {response}')

EVENT_MAP = {
    'push': handle_push_event
}

def handle_event(request):
    github_event = extract_event(request)
    return EVENT_MAP[github_event](request) if github_event in EVENT_MAP else success()

def extract_event(request):
    return request['headers']['x-github-event']

def verify_signature(request):
    sent = request['headers']['x-hub-signature'].split('=')[-1].strip()
    calculated = hmac.new(SECRET, msg=request['body'].encode('utf-8'), digestmod=sha1).hexdigest()
    print(f'HMAC SIGNATURE sent={sent} calculated={calculated}')
    return hmac.compare_digest(calculated, sent)

def success():
    return {
        'statusCode': 200,
        'body': json.dumps('success')
    }

def unauthorized():
    return {
        'statusCode': 403,
        'body': json.dumps('Unauthorized')
    }
