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
    # Expect 1.
    try:
        command = venv + ['custodianx', 'run', '-s', 'out', '--verbose',
                          '--cache-period', '0', 'test_sqs_query.yml']
        print(command)
        output = subprocess.run(command,
                                capture_output=True,
                                check=True,
                                env=dict(os.environ) | {"AWS_PROFILE": "moto"})
        print("Finished initial query.")
        if output.stdout:
            print(output.stdout.decode())
        if output.stderr:
            print(output.stderr.decode())
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        if e.stdout:
            print(e.stdout.decode())
        if e.stderr:
            print(e.stderr.decode())

    # Tear down.
    try:
        command = venv + ['custodianx', 'run', '-s', 'out', '--verbose', '--cache-period', '0',
                          'test_sqs_teardown.yml']
        print(command)
        output = subprocess.run( command,
                                check=True,
                                env=dict(os.environ) | {"AWS_PROFILE": "moto"})
        print(output)
        print("Finished teardown.")
        if output.stdout:
            print(output.stdout.decode())
        if output.stderr:
            print(output.stderr.decode())
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        if e.stdout:
            print(e.stdout.decode())
        if e.stderr:
            print(e.stderr.decode())

    # sleep for 1 second
    import time
    time.sleep(1)

    # Expect 0.
    try:
        command = venv + ['custodianx', 'run', '-s', 'out', '--verbose',
                          '--cache-period', '0', 'test_sqs_query2.yml']
        print(command)
        output = subprocess.run(command,
                                capture_output=True,
                                check=True,
                                env=dict(os.environ) | {"AWS_PROFILE": "moto"})
        print(f"Final output {output}")
        print("Finished querying after teardown.")
        if output.stdout:
            print(output.stdout.decode())
        if output.stderr:
            print(output.stderr.decode())
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        if e.stdout:
            print(e.stdout.decode())
        if e.stderr:
            print(e.stderr.decode())

