import os
from unittest import mock

import aws_extras.c7n_monkey as monkey

import boto3
import pytest
from botocore.config import Config


@pytest.fixture
def fixture():
    setup()
    yield
    teardown()

def teardown():
    pass

def setup():
    # Configuration for localstack profile and endpoints
    boto3.setup_default_session(profile_name='moto')
    config = Config(region_name='us-east-1')

    client = boto3.client("appsync", region_name="us-east-1")
    api = client.create_graphql_api(
        name="api1", authenticationType="API_KEY", tags={"key": "val", "key2": "val2"}
    )["graphqlApi"]
    import time
    time.sleep(1)

def test_setup(fixture):
    # run custodian for `test_sqs_query` and `test_sqs_teardown`

    with mock.patch.dict('os.environ', dict(os.environ) | {"AWS_PROFILE": "moto"}):
        command = ['run', '-s', 'out', '--verbose', 'test_query.yml']
        return_value= monkey.main(command)
        assert not return_value
        command = ['run', '-s', 'out', '--verbose', 'test_teardown.yml']
        return_value = monkey.main(command)
        assert not return_value