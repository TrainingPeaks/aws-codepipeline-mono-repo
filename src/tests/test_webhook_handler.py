import os
import json
import pytest
import hmac
from hashlib import sha1
from unittest.mock import patch
from botocore.stub import Stubber, ANY

SECRET = 'make sure you keep this one quiet'
os.environ['GITHUB_SECRET'] = SECRET
os.environ['EVAL_FUNCTION_ARN'] = 'test.arn'

from webhook import org

def gh_signature(event, signature):
    if not signature:
        signature = hmac.new(SECRET.encode('utf-8'), msg=event['body'].encode('utf-8'), digestmod=sha1).hexdigest()
    event['headers']['x-hub-signature'] = f'sha1 = {signature}'
    return event

def gh_event(event, eventName):
    event['headers']['x-github-event'] = eventName
    return event

@pytest.fixture()
def apigw_event(request):
    eventName = 'push'
    signature = None
    if hasattr(request, 'param'):
        print(request.param)
        eventName = request.param.get('eventName', 'push')
        signature = request.param.get('signature', None)
    event = {
        'body': '{"ref":"refs/heads/master"}',
        'resource': '/{proxy+}',
        'requestContext': {
            'resourceId': '123456',
            'apiId': '1234567890',
            'resourcePath': '/{proxy+}',
            'httpMethod': 'POST',
            'requestId': 'request-id',
            'accountId': '123456789012',
            'identity': {
                'apiKey': '',
                'userArn': '',
                'userAgent': 'Custom User Agent String',
                'user': '',
                'sourceIp': '127.0.0.1',
                'accountId': '',
            },
            'stage': 'prod',
        },
        'queryStringParameters': {'foo': 'bar'},
        'headers': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'User-Agent': 'Custom User Agent String',
            'Accept-Encoding': 'gzip, deflate, sdch',
        },
        'pathParameters': {'proxy': '/examplepath'},
        'httpMethod': 'POST',
        'stageVariables': {'baz': 'qux'},
        'path': '/examplepath',
    }
    event = gh_signature(event, signature)
    return gh_event(event, eventName)


@patch('webhook.org.invoke_function')
@pytest.mark.parametrize('apigw_event,invokeExpected', [(dict(eventName='ping'), False), (dict(eventName='push'), True)], indirect=['apigw_event'])
def test_handler(invoke_function, apigw_event, invokeExpected):

    response = org.handler(apigw_event, None)

    assert response['statusCode'] == 200
    assert 'success' in response['body']
    assert invoke_function.called == invokeExpected

@patch('webhook.org.invoke_function')
@pytest.mark.parametrize('apigw_event', [dict(eventName='ping', signature='BAD'), dict(eventName='push', signature='BAD')], indirect=['apigw_event'])
def test_handler_invalid_signature(invoke_function, apigw_event):

    response = org.handler(apigw_event, None)

    assert response['statusCode'] == 403
    assert 'Unauthorized' in response['body']
    assert invoke_function.called is False


@pytest.fixture(scope='function')
def lambda_stub():
    with Stubber(org.lambdaclient) as stub:
        yield stub
        stub.assert_no_pending_responses()


@pytest.mark.parametrize('status', [202, 400, 500])
def test_handler_boto3lambda_stub(lambda_stub, apigw_event, status):
    lambda_stub.add_response(
        method='invoke_async',
        service_response={'Status': 202},
        expected_params={'FunctionName': 'test.arn', 'InvokeArgs': ANY}
    )

    response = org.handler(apigw_event, None)

    assert response['statusCode'] == 200


def test_handler_boto3lambda_stub_fail(lambda_stub, apigw_event):
    lambda_stub.add_client_error(
        method='invoke_async',
        service_error_code='ResourceNotFoundException',
        http_status_code=500
    )

    with pytest.raises(org.lambdaclient.exceptions.ResourceNotFoundException):
        org.handler(apigw_event, None)

