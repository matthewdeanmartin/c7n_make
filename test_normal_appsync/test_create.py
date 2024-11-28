import os
import subprocess

import boto3
import pytest
from botocore.config import Config
from botocore.exceptions import ClientError
from typing import Any
import zipfile
import io


@pytest.fixture
def fixture():
    setup()
    yield
    teardown()

def setup():
    # Configuration for localstack profile and endpoints
    boto3.setup_default_session(profile_name='moto')
    config = Config(region_name='us-east-1')

    client = boto3.client("appsync", region_name="us-east-1")
    api = client.create_graphql_api(
        name="api1", authenticationType="API_KEY", tags={"key": "val", "key2": "val2"}
    )["graphqlApi"]

    api2 = client.create_graphql_api(
        name="api2", authenticationType="API_KEY", tags={"key": "val", "key2": "val2"}
    )

def teardown():
    pass
    # # Configuration for localstack profile and endpoints
    # boto3.setup_default_session(profile_name='moto')
    # config = Config(region_name='us-east-1')
    #
    # client = boto3.client("appsync", region_name="ap-southeast-1")
    #
    # # Query for the api
    # api = client.get_graphql_api(apiId="api1")
    # # if it exists
    # if api:
    #     response = client.delete_graphql_api(
    #         apiId="api1"
    #     )
    # else:
    #     print(api)

def test_setup(fixture):
    # run custodian for `test_query` and `test_teardown`
    # use subprocess.run

    venv = ["poetry", "run"]
    # Expect 1.
    try:
        command = venv + ['custodian', 'run', '-s', 'out', '--verbose',
                          '--cache-period', '0', 'test_query.yml']
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
        command = venv + ['custodian', 'run', '-s', 'out', '--verbose', '--cache-period', '0',
                          'test_teardown.yml']
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
        command = venv + ['custodian', 'run', '-s', 'out', '--verbose',
                          '--cache-period', '0', 'test_teardown.yml']
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

