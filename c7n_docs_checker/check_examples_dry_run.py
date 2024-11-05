import multiprocessing
import subprocess
import logging
from pathlib import Path
from typing import List

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def validate_file(file_path: Path) -> tuple[Path, bool, str]:
    """Validates a YAML file using the `custodian validate` command.

    Args:
        file_path (Path): Path to the YAML file.

    Returns:
        tuple[Path, bool, str]: The file path, validation status (True if passed, False if failed),
        and any error message if the validation failed.
    """
    LOGGER.info(f"Validating {file_path}...")
    try:
        result = subprocess.run(
            ["custodian", "run", str(file_path), "--output-dir=state", "--dry-run", "--verbose"],
            check=True,
            capture_output=True,
            text=True
        )
        return file_path, True, ""
    except subprocess.CalledProcessError as e:
        # Capture and return the error message
        return file_path, False, e.stderr


def validate_files_in_parallel(folder: Path) -> List[tuple[Path, bool, str]]:
    """Validates all YAML files in the specified folder in parallel using available CPU cores.

    Args:
        folder (Path): Directory containing YAML files.

    Returns:
        List[tuple[Path, bool, str]]: A list of results, where each result is a tuple containing
        the file path, validation status, and an error message if any.
    """
    yaml_files = list(folder.glob("*.yaml"))
    with multiprocessing.Pool() as pool:
        results = pool.map(validate_file, yaml_files)
    return results


def print_failures(failures: List[tuple[Path, bool, str]]) -> None:
    """Prints out failed validations in a readable format.

    Args:
        failures (List[tuple[Path, bool, str]]): List of failed validation results.
    """
    if not failures:
        LOGGER.info("All files passed validation!")
        return

    LOGGER.error(f"{len(failures)} file(s) failed validation:")
    for file_path, _, error_msg in failures:
        LOGGER.error(f"File: {file_path}")
        LOGGER.error(f"Error: {error_msg}")
        LOGGER.error("-" * 40)


if __name__ == "__main__":
    folder = Path("examples")

    # Validate files in parallel
    results = validate_files_in_parallel(folder)

    # Collect failures
    failures = [result for result in results if not result[1]]

    # Print out the results of failed validations
    print_failures(failures)
