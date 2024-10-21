# Monkey patch c7n to add a new provider
# As far as I can tell, c7n can't import a new provider unless it know about it in advance
# (see c7n.resources.load_providers())

import sys
import logging

import c7n.provider as providers
import c7n.resources
from aws_extras.provider import Awsx  # NOQA

from aws_extras.entry import initialize


LOGGER = logging.getLogger(__name__)




def main(args=None) -> None:
    """Wrapper CLI that delegates all arguments to c7n.main."""
    if args is None:
        args = sys.argv[1:]

    from c7n.cli import main as c7n_main

    # Has no effect?

    c7n.resources.PROVIDER_NAMES += ('awsx',)
    # Initialize the awsx, appears to do nothing right now.
    initialize()

    c7n.resources.LOADED.add('awsx')


    # Do it the hard way because decorators are doing nothing.

    # providers.clouds.register('awsx', Awsx)
    # providers.clouds['awsx'].resources.register('sqs', SQS)

    assert "awsx" in providers.clouds,providers.clouds.keys()

    LOGGER.info("Delegating arguments: %s", args)

    # Call c7n's main function with the provided arguments
    result = c7n_main(args=args)
    logging.shutdown()
    return result


if __name__ == "__main__":
    main()