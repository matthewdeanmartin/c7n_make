import os
import subprocess

import boto3
import pytest
from botocore.config import Config
from botocore.exceptions import ClientError
from typing import Any
import zipfile
import io


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
    # use subprocess.run

    venv = ["poetry", "run"]
    try:
        command = venv + ['custodianx', 'run', '-s', 'out', '--verbose', 'test_sqs_query.yml']
        output = subprocess.run(command,
                                capture_output=True,
                                check=True,
                                env=dict(os.environ) | {"AWS_PROFILE": "moto"})
        print(output.stdout)
    except subprocess.CalledProcessError as e:
        print(e.stdout)
        print(e.stderr)

    try:
        command = venv + ['custodianx', 'run', '-s', 'out', '--verbose', 'test_sqs_teardown.yml']
        output = subprocess.run( command,
                                check=True,
                                env=dict(os.environ) | {"AWS_PROFILE": "moto"})
        print(output.stdout)
    except subprocess.CalledProcessError as e:
        print(e.stdout)
        print(e.stderr)

