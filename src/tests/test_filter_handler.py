import os
import io
import datetime
import re
import pytest
import json
import boto3
from unittest.mock import patch
from botocore.stub import Stubber
from botocore.response import StreamingBody

os.environ['S3_BUCKET'] = 'test-bucket'
os.environ['S3_PREFIX'] = 'some/prefix'

from eval import filter

@pytest.fixture()
def github_event():
    return {
        "ref": "refs/heads/master",
        "before": "0000000000000000000000000000000000000000",
        "after": "0000000000000000000000000000000000000001",
        "repository": {
            "id": 264744304,
            "node_id": "id=",
            "name": "repo",
            "full_name": "Org/repo",
            "private": True,
            "owner": {
                "name": "Org",
                "email": None,
                "login": "Org",
                "id": 1,
                "node_id": "nid",
                "avatar_url": "https://avatars3.githubusercontent.com/u/1?v=4",
                "gravatar_id": "",
                "url": "https://api.github.com/users/Org",
                "html_url": "https://github.com/Org",
                "followers_url": "https://api.github.com/users/Org/followers",
                "following_url": "https://api.github.com/users/Org/following{/other_user}",
                "gists_url": "https://api.github.com/users/Org/gists{/gist_id}",
                "starred_url": "https://api.github.com/users/Org/starred{/owner}{/repo}",
                "subscriptions_url": "https://api.github.com/users/Org/subscriptions",
                "organizations_url": "https://api.github.com/users/Org/orgs",
                "repos_url": "https://api.github.com/users/Org/repos",
                "events_url": "https://api.github.com/users/Org/events{/privacy}",
                "received_events_url": "https://api.github.com/users/Org/received_events",
                "type": "Organization",
                "site_admin": False
            },
            "html_url": "https://github.com/Org/repo",
            "description": None,
            "fork": False,
            "url": "https://github.com/Org/repo",
            "forks_url": "https://api.github.com/repos/Org/repo/forks",
            "keys_url": "https://api.github.com/repos/Org/repo/keys{/key_id}",
            "collaborators_url": "https://api.github.com/repos/Org/repo/collaborators{/collaborator}",
            "teams_url": "https://api.github.com/repos/Org/repo/teams",
            "hooks_url": "https://api.github.com/repos/Org/repo/hooks",
            "issue_events_url": "https://api.github.com/repos/Org/repo/issues/events{/number}",
            "events_url": "https://api.github.com/repos/Org/repo/events",
            "assignees_url": "https://api.github.com/repos/Org/repo/assignees{/user}",
            "branches_url": "https://api.github.com/repos/Org/repo/branches{/branch}",
            "tags_url": "https://api.github.com/repos/Org/repo/tags",
            "blobs_url": "https://api.github.com/repos/Org/repo/git/blobs{/sha}",
            "git_tags_url": "https://api.github.com/repos/Org/repo/git/tags{/sha}",
            "git_refs_url": "https://api.github.com/repos/Org/repo/git/refs{/sha}",
            "trees_url": "https://api.github.com/repos/Org/repo/git/trees{/sha}",
            "statuses_url": "https://api.github.com/repos/Org/repo/statuses/{sha}",
            "languages_url": "https://api.github.com/repos/Org/repo/languages",
            "stargazers_url": "https://api.github.com/repos/Org/repo/stargazers",
            "contributors_url": "https://api.github.com/repos/Org/repo/contributors",
            "subscribers_url": "https://api.github.com/repos/Org/repo/subscribers",
            "subscription_url": "https://api.github.com/repos/Org/repo/subscription",
            "commits_url": "https://api.github.com/repos/Org/repo/commits{/sha}",
            "git_commits_url": "https://api.github.com/repos/Org/repo/git/commits{/sha}",
            "comments_url": "https://api.github.com/repos/Org/repo/comments{/number}",
            "issue_comment_url": "https://api.github.com/repos/Org/repo/issues/comments{/number}",
            "contents_url": "https://api.github.com/repos/Org/repo/contents/{+path}",
            "compare_url": "https://api.github.com/repos/Org/repo/compare/{base}...{head}",
            "merges_url": "https://api.github.com/repos/Org/repo/merges",
            "archive_url": "https://api.github.com/repos/Org/repo/{archive_format}{/ref}",
            "downloads_url": "https://api.github.com/repos/Org/repo/downloads",
            "issues_url": "https://api.github.com/repos/Org/repo/issues{/number}",
            "pulls_url": "https://api.github.com/repos/Org/repo/pulls{/number}",
            "milestones_url": "https://api.github.com/repos/Org/repo/milestones{/number}",
            "notifications_url": "https://api.github.com/repos/Org/repo/notifications{?since,all,participating}",
            "labels_url": "https://api.github.com/repos/Org/repo/labels{/name}",
            "releases_url": "https://api.github.com/repos/Org/repo/releases{/id}",
            "deployments_url": "https://api.github.com/repos/Org/repo/deployments",
            "created_at": 1589744852,
            "updated_at": "2020-05-17T19:47:32Z",
            "pushed_at": 1589772461,
            "git_url": "git://github.com/Org/repo.git",
            "ssh_url": "git@github.com:Org/repo.git",
            "clone_url": "https://github.com/Org/repo.git",
            "svn_url": "https://github.com/Org/repo",
            "homepage": None,
            "size": 0,
            "stargazers_count": 0,
            "watchers_count": 0,
            "language": None,
            "has_issues": True,
            "has_projects": True,
            "has_downloads": True,
            "has_wiki": True,
            "has_pages": False,
            "forks_count": 0,
            "mirror_url": None,
            "archived": False,
            "disabled": False,
            "open_issues_count": 0,
            "license": None,
            "forks": 0,
            "open_issues": 0,
            "watchers": 0,
            "default_branch": "master",
            "stargazers": 0,
            "master_branch": "master",
            "organization": "Org"
        },
        "pusher": {
            "name": "user1",
            "email": "user1@org"
        },
        "organization": {
            "login": "Org",
            "id": 1,
            "node_id": "id=",
            "url": "https://api.github.com/orgs/Org",
            "repos_url": "https://api.github.com/orgs/Org/repos",
            "events_url": "https://api.github.com/orgs/Org/events",
            "hooks_url": "https://api.github.com/orgs/Org/hooks",
            "issues_url": "https://api.github.com/orgs/Org/issues",
            "members_url": "https://api.github.com/orgs/Org/members{/member}",
            "public_members_url": "https://api.github.com/orgs/Org/public_members{/member}",
            "avatar_url": "https://avatars3.githubusercontent.com/u/1?v=4",
            "description": ""
        },
        "sender": {
            "login": "user1",
            "id": 3467709,
            "node_id": "id=",
            "avatar_url": "https://avatars0.githubusercontent.com/u/3467709?v=4",
            "gravatar_id": "",
            "url": "https://api.github.com/users/user1",
            "html_url": "https://github.com/user1",
            "followers_url": "https://api.github.com/users/user1/followers",
            "following_url": "https://api.github.com/users/user1/following{/other_user}",
            "gists_url": "https://api.github.com/users/user1/gists{/gist_id}",
            "starred_url": "https://api.github.com/users/user1/starred{/owner}{/repo}",
            "subscriptions_url": "https://api.github.com/users/user1/subscriptions",
            "organizations_url": "https://api.github.com/users/user1/orgs",
            "repos_url": "https://api.github.com/users/user1/repos",
            "events_url": "https://api.github.com/users/user1/events{/privacy}",
            "received_events_url": "https://api.github.com/users/user1/received_events",
            "type": "User",
            "site_admin": False
        },
        "created": True,
        "deleted": False,
        "forced": False,
        "base_ref": None,
        "compare": "https://github.com/Org/repo/commit/d8a20fd5b86b",
        "commits": [
            {
                "id": "d8a20fd5b86b1c08c9962573d21317ec70905b60",
                "tree_id": "17362e7ba0d9e82f0983d368964e8c4609421d15",
                "distinct": True,
                "message": "Sparse basics",
                "timestamp": "2020-05-17T21:27:27-06:00",
                "url": "https://github.com/Org/repo/commit/d8a20fd5b86b1c08c9962573d21317ec70905b60",
                "author": {
                    "name": "First Last",
                    "email": "user1@org",
                    "username": "user1"
                },
                "committer": {
                    "name": "First Last",
                    "email": "user1@org",
                    "username": "user1"
                },
                "added": [
                    ".flake8",
                    ".gitattributes",
                    ".gitignore",
                    "github-endpoint/.gitignore",
                    "github-endpoint/deploy.sh",
                    "github-endpoint/events/ping-event.json",
                    "github-endpoint/package.sh",
                    "github-endpoint/readme.md",
                    "github-endpoint/template.yaml",
                    "github-endpoint/tests/unit/__init__.py",
                    "github-endpoint/tests/unit/test_handler.py",
                    "github-endpoint/webhook/__init__.py",
                    "github-endpoint/webhook/org.py",
                    "github-endpoint/webhook/requirements.txt",
                    "readme.md"
                ],
                "removed": [],
                "modified": []
            }
        ],
        "head_commit": {
            "id": "d8a20fd5b86b1c08c9962573d21317ec70905b60",
            "tree_id": "17362e7ba0d9e82f0983d368964e8c4609421d15",
            "distinct": True,
            "message": "Sparse basics",
            "timestamp": "2020-05-17T21:27:27-06:00",
            "url": "https://github.com/Org/repo/commit/d8a20fd5b86b1c08c9962573d21317ec70905b60",
            "author": {
                "name": "First Last",
                "email": "user1@org",
                "username": "user1"
            },
            "committer": {
                "name": "First Last",
                "email": "user1@org",
                "username": "user1"
            },
            "added": [
                ".flake8",
                ".gitattributes",
                ".gitignore",
                "github-endpoint/.gitignore",
                "github-endpoint/deploy.sh",
                "github-endpoint/events/ping-event.json",
                "github-endpoint/package.sh",
                "github-endpoint/readme.md",
                "github-endpoint/template.yaml",
                "github-endpoint/tests/unit/__init__.py",
                "github-endpoint/tests/unit/test_handler.py",
                "github-endpoint/webhook/__init__.py",
                "github-endpoint/webhook/org.py",
                "github-endpoint/webhook/requirements.txt",
                "readme.md"
            ],
            "removed": [],
            "modified": []
        }
    }

def test_extract_info(github_event):
    repo, branch = filter.extract_info(github_event)

    assert repo == 'repo'
    assert branch == 'master'

def test_extract_paths():
    event = {
        "commits": [
            {
                "added": ["one"],
                "removed": [],
                "modified": []
            },
            {
                "added": [],
                "removed": ["two"],
                "modified": []
            },
            {
                "added": [],
                "removed": [],
                "modified": ["three"]
            }
        ]
    }

    paths = filter.extract_paths(event)

    for i in ["one", "two", "three"]:
        assert i in paths


@pytest.mark.parametrize('regexs,expected', [
    pytest.param(('^no-way-this-matches.sh', ), False, id='no-match'),
    pytest.param(('.*org.py.*', ), True, id='first-match'),
    pytest.param(('^README.MD', '^github-endpoint/.*'), True, id='second-match')
])
def test_is_match(github_event, regexs, expected):
    regex = [re.compile(x) for x in regexs]

    actual = filter.is_match(github_event, regex)

    assert actual == expected

def test_build_regex_matches():
    regexes = filter.build_regex_matches('^.*$,.*')

    for r in regexes:
        assert isinstance(r, re.Pattern)
    assert ['^.*$', '.*'] == [x.pattern for x in regexes]

@pytest.mark.parametrize('prefix,repo,branch,expected', [
    pytest.param('prefix', 'repo', 'branch', 'prefix/repo-branch', id='normal'),
    pytest.param('superlongprefixtomakesure-we-arent-off', 'repo', 'branch', 'superlongprefixtomakesure-we-arent-off/repo-branch', id='long prefix'),
    pytest.param('prefix', 'TransactionalEmailTemplates', 'experiment-with-cloudformation-setup-ses-config-set-events', 'prefix/TransactionalEmailTemplates-experiment-with-cloudfor', id='long branch')
])
def test_build_prefix(prefix, repo, branch, expected):
    actual = filter.build_prefix(prefix, repo, branch)

    assert actual == expected

@patch('eval.filter.start_code_pipeline')
@patch('eval.filter.get_configs', return_value=[{'CodePipelineName': 'pipeline', 'Matches': filter.build_regex_matches('.*org.py.*')}])
@patch('eval.filter.get_s3_object_infos', return_value=[])
def test_handler_starts(s3infos, configs, start, github_event):
    filter.handler(github_event, None)

    assert start.called

@patch('eval.filter.start_code_pipeline')
@patch('eval.filter.get_configs', return_value=[{'CodePipelineName': 'pipeline', 'Matches': filter.build_regex_matches('not-a-chance')}])
@patch('eval.filter.get_s3_object_infos', return_value=[])
def test_handler_nomatch_nostart(s3infos, configs, start, github_event):
    filter.handler(github_event, None)

    assert start.called is False

def test_get_s3_object_infos():
    client = boto3.client('s3')
    stub = Stubber(client)
    bucket = 'test-bucket'
    repo = 'repo'
    branch = 'branch'
    prefix = 'some-prefix'
    s3prefix = filter.build_prefix(prefix, repo, branch)
    response = {
        'IsTruncated': False,
        'Name': 'test-bucket',
        'MaxKeys': 1000, 'Prefix': '',
        'Contents': [
            {
                'Key': f'{s3prefix}/config1.json',
                'ETag': '"abc123"',
                'StorageClass': 'STANDARD',
                'LastModified': datetime.datetime(2020, 1, 20, 22, 9),
                'Owner': {'ID': 'abc123', 'DisplayName': 'myname'},
                'Size': 14814
            },
            {
                'Key': f'{s3prefix}/config2.json',
                'ETag': '"abc123"',
                'StorageClass': 'STANDARD',
                'LastModified': datetime.datetime(2020, 1, 20, 22, 9),
                'Owner': {'ID': 'abc123', 'DisplayName': 'myname'},
                'Size': 14814
            }
        ],
        'EncodingType': 'url'
    }
    expected = [('test-bucket', f'{s3prefix}/config1.json'), ('test-bucket', f'{s3prefix}/config2.json')]
    stub.add_response('list_objects_v2', service_response=response, expected_params={'Bucket': bucket, 'Prefix': s3prefix})

    with stub:
        infos = filter.get_s3_object_infos(client, bucket, prefix, repo, branch)

    assert infos == expected

def test_get_configs():
    client = boto3.client('s3')
    stub = Stubber(client)
    infos = [('test-bucket', 'some-prefix/config1.json')]
    expected_json = {
        'GitHubRepo': 'repo',
        'GitHubBranch': 'branch',
        'ChangeMatchExpressions': '.*',
        'CodePipelineName': 'pipeline'
    }
    expected_encoded = json.dumps(expected_json).encode()
    expected_json['Matches'] = filter.build_regex_matches(expected_json['ChangeMatchExpressions'])
    expected = [expected_json]
    response = {
        'Body': StreamingBody(io.BytesIO(expected_encoded), len(expected_encoded)),
    }
    stub.add_response('get_object', service_response=response, expected_params={'Bucket': infos[0][0], 'Key': infos[0][1]})

    with stub:
        actual = filter.get_configs(client, infos)
        stub.assert_no_pending_responses()

    assert actual == expected

@patch('eval.filter.codepipeline_client')
def test_start_code_pipeline(codepipeline_client):
    client = boto3.client('codepipeline')
    codepipeline_client.return_value = client
    stub = Stubber(client)
    response = {
        'pipelineExecutionId': 'abcd123'
    }
    pipelineName = 'test-pipeline'
    stub.add_response('start_pipeline_execution', service_response=response, expected_params={'name': pipelineName})

    with stub:
        filter.start_code_pipeline(pipelineName)
        stub.assert_no_pending_responses()
