import os
from unittest import mock

import aws_extras.c7n_monkey as monkey

import boto3
import pytest
from botocore.config import Config


# please write a pytest fixture for this

@pytest.fixture
def sqs_fixture():
    sqs_setup()
    yield
    sqs_teardown()

def sqs_setup():
    # Configuration for localstack profile and endpoints
    boto3.setup_default_session(profile_name='moto')
    config = Config(region_name='us-east-1')

    # SQS
    sqs_client = boto3.client('sqs', config=config)
    response = sqs_client.list_queues()
    if not response.get('QueueUrls') or not any(queue.endswith('/example-queue') for queue in response['QueueUrls']):
        response = sqs_client.create_queue(
            QueueName='example-queue'
        )
        print(f"SQS Queue: {response}")
    else:
        print("SQS Queue: example-queue already exists")

def sqs_teardown():
    # Configuration for localstack profile and endpoints
    boto3.setup_default_session(profile_name='moto')
    config = Config(region_name='us-east-1')

    # SQS
    sqs_client = boto3.client('sqs', config=config)
    response = sqs_client.list_queues()
    if response.get('QueueUrls') and any(queue.endswith('/example-queue') for queue in response['QueueUrls']):
        response = sqs_client.delete_queue(
            QueueUrl=[queue for queue in response['QueueUrls'] if queue.endswith('/example-queue')][0]
        )
        print(f"SQS Queue: {response}")
    else:
        print("SQS Queue: example-queue does not exist")

def test_sqs_setup(sqs_fixture):
    # run custodian for `test_sqs_query` and `test_sqs_teardown`

    with mock.patch.dict('os.environ', dict(os.environ) | {"AWS_PROFILE": "moto"}):
        command = ['run', '-s', 'out', '--verbose', 'test_sqs_query.yml']
        return_value= monkey.main(command)
        assert not return_value
        command = ['run', '-s', 'out', '--verbose', 'test_sqs_teardown.yml']
        return_value = monkey.main(command)
        assert not return_value

