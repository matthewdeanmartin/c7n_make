import sys
import logging

from c7n.cli import main as c7n_main

LOGGER = logging.getLogger(__name__)


def main(args=None) -> None:
    """Wrapper CLI that delegates all arguments to c7n.main."""
    if args is None:
        args = sys.argv[1:]
    LOGGER.info("Delegating arguments: %s", args)
    # Call c7n's main function with the provided arguments
    result = c7n_main(args=args)
    logging.shutdown()
    return result


if __name__ == "__main__":
    main()
