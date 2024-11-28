# Copyright The Cloud Custodian Authors.
# SPDX-License-Identifier: Apache-2.0

# register provider
from aws_extras.provider import Awsx  # NOQA


def initialize():
    """This is for registering all plugins other than resource plugins"""
    # Plugins registered on import
    # import execution modes
    # import aws_extras.policy
    # import aws_extras.container_host.modes
    # import aws_extras.output # noqa
    import aws_extras.resources.appsync