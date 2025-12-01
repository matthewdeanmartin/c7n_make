# Copyright The Cloud Custodian Authors.
# SPDX-License-Identifier: Apache-2.0


from c7n.provider import clouds, Provider

# from collections import Counter, namedtuple
# import contextlib
import copy
# import datetime
# import itertools
import logging
# import os
import operator
# import socket
# import sys
# import time
# import threading
# import traceback
# from urllib import parse as urlparse
# from urllib.request import urlopen, Request
# from urllib.error import HTTPError, URLError
#
# import boto3
#
# from botocore.validate import ParamValidator
# from boto3.s3.transfer import S3Transfer

from c7n.credentials import SessionFactory
from c7n.resources.aws import XrayTracer, HAVE_XRAY, join_output, get_profile_session, get_service_region_map, \
    _default_bucket_region, _default_account_id, _default_region

# from c7n.config import Bag
# from c7n.exceptions import InvalidOutputConfig, PolicyValidationError
# from c7n.log import CloudWatchLogHandler
# from c7n.utils import parse_url_config, backoff_delays

from .resource_map import ResourceMap

# # Import output registries aws provider extends.
# from c7n.output import (
#     api_stats_outputs,
#     blob_outputs,
#     log_outputs,
#     metrics_outputs,
#     tracer_outputs
# )
#
# # Output base implementations we extend.
# from c7n.output import (
#     Metrics,
#     DeltaStats,
#     BlobOutput,
#     LogOutput,
# )

from c7n.registry import PluginRegistry
from c7n import utils


log = logging.getLogger('custodian.provider')


@clouds.register('awsx')
class Awsx(Provider):

    display_name = 'AWSX'
    resource_prefix = 'awsx'

    resources = PluginRegistry('%s.resources' % resource_prefix)

    # import paths for resources
    resource_map = ResourceMap

    def initialize(self, options):
        """
        """
        _default_region(options)
        _default_account_id(options)
        _default_bucket_region(options)

        if options.tracer and options.tracer.startswith('xray') and HAVE_XRAY:
            XrayTracer.initialize(utils.parse_url_config(options.tracer))
        return options

    def get_session_factory(self, options):
        return SessionFactory(
            options.region,
            options.profile,
            options.assume_role,
            options.external_id,
            options.session_policy)

    def initialize_policies(self, policy_collection, options):
        """Return a set of policies targetted to the given regions.

        Supports symbolic regions like 'all'. This will automatically
        filter out policies if they are being targetted to a region that
        does not support the service. Global services will target a
        single region (us-east-1 if only all specified, else first
        region in the list).

        Note for region partitions (govcloud and china) an explicit
        region from the partition must be passed in.
        """
        from c7n.policy import Policy, PolicyCollection
        policies = []
        service_region_map, resource_service_map = get_service_region_map(
            options.regions, policy_collection.resource_types, self.type)
        if 'all' in options.regions:
            enabled_regions = {
                r['RegionName'] for r in
                get_profile_session(options).client('ec2').describe_regions(
                    Filters=[{'Name': 'opt-in-status',
                              'Values': ['opt-in-not-required', 'opted-in']}]
                ).get('Regions')}
        for p in policy_collection:
            if 'awsx.' in p.resource_type:
                _, resource_type = p.resource_type.split('.', 1)
            else:
                resource_type = p.resource_type
            available_regions = service_region_map.get(
                resource_service_map.get(resource_type), ())

            # its a global service/endpoint, use user provided region
            # or us-east-1.
            if not available_regions and options.regions:
                candidates = [r for r in options.regions if r != 'all']
                candidate = candidates and candidates[0] or 'us-east-1'
                svc_regions = [candidate]
            elif 'all' in options.regions:
                svc_regions = list(set(available_regions).intersection(enabled_regions))
            else:
                svc_regions = options.regions

            for region in svc_regions:
                if available_regions and region not in available_regions:
                    level = ('all' in options.regions and
                             logging.DEBUG or logging.WARNING)
                    # TODO: fixme
                    policy_collection.log.log(
                        level, "policy:%s resources:%s not available in region:%s",
                        p.name, p.resource_type, region)
                    continue
                options_copy = copy.copy(options)
                options_copy.region = str(region)

                if len(options.regions) > 1 or 'all' in options.regions and getattr(
                        options, 'output_dir', None):
                    options_copy.output_dir = join_output(options.output_dir, region)
                policies.append(
                    Policy(p.data, options_copy,
                           session_factory=policy_collection.session_factory()))

        return PolicyCollection(
            # order policies by region to minimize local session invalidation.
            # note relative ordering of policies must be preserved, python sort
            # is stable.
            sorted(policies, key=operator.attrgetter('options.region')),
            options)


resources = Awsx.resources
