import os
import os.path
from dataclasses import asdict
import pytest
from unittest.mock import patch
import boto3
from botocore.stub import Stubber

os.environ['S3_BUCKET'] = 'test-bucket'
os.environ['S3_PREFIX'] = 'test-prefix'
from cfresource import resource

def test_extract_and_validate_properties():
    source = {
        'body': {
            'GitHubRepo': 'repo',
            'GitHubBranch': 'branch',
            'CodePipelineName': 'cpname',
            'ChangeMatchExpressions': '.*',
        }
    }

    actual = resource.extract_and_validate_properties(source, 'body')

    actual_dict = asdict(actual)
    source['body']['ServiceToken'] = None
    assert actual_dict == source['body']

def test_extract_and_validate_properties_extra():
    source = {
        'body': {
            'GitHubRepo': 'repo',
            'GitHubBranch': 'branch',
            'CodePipelineName': 'cpname',
            'ChangeMatchExpressions': '.*',
            'NopeNotNeeded': 1234
        }
    }

    actual = resource.extract_and_validate_properties(source, 'body')

    actual_dict = asdict(actual)
    source['body']['ServiceToken'] = None
    del source['body']['NopeNotNeeded']
    assert actual_dict == source['body']

def test_extract_and_validate_properties_missing():
    source = {
        'body': {
            'GitHubBranch': 'branch',
            'CodePipelineName': 'cpname',
            'ChangeMatchExpressions': '.*'
        }
    }

    with pytest.raises(ValueError) as e:
        resource.extract_and_validate_properties(source, 'body')
        assert 'GitHubRepo' in e.value

def test_extract_and_validate_properties_for_reals():
    source = {
        'LogicalResourceId': 'MonoRepoTrigger',
        'RequestId': 'aeef721d-6bad-474b-9eba-c0bc90b36c75',
        'RequestType': 'Create',
        'ResourceProperties': {
            'ChangeMatchExpressions': 'cf-github-monorepo/.*,readme.md',
            'CodePipelineName': 'mono-repo-example',
            'GitHubBranch': 'master',
            'GitHubRepo': 'mono-repo-experiment',
            'ServiceToken': 'arn:aws:lambda:us-east-1:0000:function:my-function'
        },
        'ResourceType': 'Custom::MonoRepoTriggerFunction',
        'ResponseURL': 'https://some-url',
        'ServiceToken': 'arn:aws:lambda:us-east-1:0000:function:my-function',
        'StackId': 'arn:aws:cloudformation:us-east-1:0000:stack/my-stack/22'
    }

    resource.extract_and_validate_properties(source, 'ResourceProperties')

@pytest.fixture()
def valid_properties():
    return resource.ResourceProperties(
        GitHubRepo='GitHubRepositoryName', GitHubBranch='MyBranchName',
        ChangeMatchExpressions='.*', CodePipelineName='pipeline')

@pytest.mark.parametrize(
    'pipeline,expected', [
        ('NameOfTheCodePipeline', 'GitHubRepositoryName-MyBranchName-NameOfTheCodePipel-26BA0737'),
        ('cpname', 'GitHubRepositoryName-MyBranchName-cpname-254D7E69')])
def test_get_filename(pipeline, expected, valid_properties):
    valid_properties.CodePipelineName = pipeline

    actual = resource.get_filename(valid_properties)

    print(actual)
    assert actual == expected

def test_get_s3_key():
    actual = resource.get_s3_key('somefile')

    assert actual == 'test-prefix/somefile.json'

def build_cf_event(eventType):
    event = {
        'LogicalResourceId': 'logicalId',
        'RequestId': 'aeef721d-6bad-474b-9eba-c0bc90b36c75',
        'RequestType': eventType,
        'ResourceProperties': {
            'ChangeMatchExpressions': '.*',
            'CodePipelineName': 'pipeline',
            'GitHubBranch': 'branch',
            'GitHubRepo': 'repo',
            'ServiceToken': 'arn'
        },
        'ResourceType': 'resource-type',
        'ResponseURL': 'https://some-url',
        'ServiceToken': 'arn:token',
        'StackId': 'arn:stack'
    }
    if eventType == 'Update':
        event['OldResourceProperties'] = {
            'ChangeMatchExpressions': '.*',
            'CodePipelineName': 'oldpipeline',
            'GitHubBranch': 'oldbranch',
            'GitHubRepo': 'oldrepo',
            'ServiceToken': 'oldarn'
        }
    props = resource.extract_and_validate_properties(event, 'ResourceProperties')
    return event, resource.get_filename(props), resource.props_to_config_data(props)


@patch('cfresource.resource.send_response')
@patch('cfresource.resource.put_s3')
def test_handler_create(putS3, sendResponse):
    event, filename, config = build_cf_event('Create')

    resource.handler(event, None)

    s3_args = putS3.call_args.args
    assert s3_args[1] == 'test-bucket'
    assert s3_args[2] == resource.get_s3_key(filename)
    assert s3_args[3] == config
    assert s3_args[4] == 'application/json'
    response_args = sendResponse.call_args.args
    assert response_args[0] == 'https://some-url'
    assert response_args[1]['Status'] == 'SUCCESS'

@patch('cfresource.resource.send_response')
@patch('cfresource.resource.put_s3', side_effect=KeyError)
def test_handler_create_fail(putS3, sendResponse):
    event, filename, config = build_cf_event('Create')

    resource.handler(event, None)

    response_args = sendResponse.call_args.args
    assert response_args[0] == 'https://some-url'
    assert response_args[1]['Status'] == 'FAILED'
    assert response_args[1]['Reason'] == repr(KeyError())

@patch('cfresource.resource.send_response')
@patch('cfresource.resource.put_s3')
@patch('cfresource.resource.delete_s3')
def test_handler_update(deleteS3, putS3, sendResponse):
    event, filename, config = build_cf_event('Update')
    oldprops = resource.extract_and_validate_properties(event, 'OldResourceProperties')
    oldfilename = resource.get_filename(oldprops)

    resource.handler(event, None)

    s3_delete_args = deleteS3.call_args.args
    assert s3_delete_args[1] == 'test-bucket'
    assert s3_delete_args[2] == resource.get_s3_key(oldfilename)
    s3_args = putS3.call_args.args
    assert s3_args[1] == 'test-bucket'
    assert s3_args[2] == resource.get_s3_key(filename)
    assert s3_args[3] == config
    assert s3_args[4] == 'application/json'
    response_args = sendResponse.call_args.args
    assert response_args[0] == 'https://some-url'
    assert response_args[1]['Status'] == 'SUCCESS'


def test_put_s3():
    client = boto3.client('s3')
    stub = Stubber(client)

    bucket = 'test-bucket'
    key = 'file'
    body = 'test'.encode()
    contentType = 'application/json'
    response = {
        'Expiration': 'expiration',
        'ETag': 'etag',
    }
    params = {
        'Bucket': bucket,
        'Key': key,
        'Body': body,
        'ContentType': contentType
    }
    stub.add_response('put_object', service_response=response, expected_params=params)

    with stub:
        resource.put_s3(client, bucket, key, body, contentType)
        stub.assert_no_pending_responses()

def test_delete_s3():
    client = boto3.client('s3')
    stub = Stubber(client)
    bucket = 'test-bucket'
    key = 'file'
    params = {
        'Bucket': bucket,
        'Key': key
    }
    response = {
        'VersionId': 'v001',
    }
    stub.add_response('delete_object', service_response=response, expected_params=params)

    with stub:
        resource.delete_s3(client, bucket, key)
        stub.assert_no_pending_responses()
