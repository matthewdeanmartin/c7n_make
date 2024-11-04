import sys
import yaml
import logging
from pathlib import Path
from typing import Any, Union, Optional
import tomlkit

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Define types for clarity
YamlContent = Union[dict[str, Any], list[Any]]


def load_yaml_content(input_data: str) -> list[YamlContent]:
    """Parses YAML content, potentially with multiple documents."""
    try:
        return list(yaml.safe_load_all(input_data))
    except yaml.YAMLError as e:
        LOGGER.error("Error parsing YAML: %s", e)
        sys.exit(1)


def load_config(config_path: Path) -> dict[str, bool]:
    """Loads the configuration file to get linting rules.

    Args:
        config_path (Path): Path to the config file.

    Returns:
        dict[str, bool]: A dictionary of rule names and their enabled status.
    """
    try:
        with config_path.open("r", encoding="utf-8") as f:
            config = tomlkit.parse(f.read())
        return config.get("rules", {})
    except (FileNotFoundError, tomlkit.exceptions.ParseError) as e:
        LOGGER.error("Error loading config file: %s", e)
        sys.exit(1)


def lint_require_description(content: YamlContent) -> bool:
    """Check if each policy has a description."""
    for policy in content.get("policies", []):
        if "description" not in policy:
            LOGGER.warning("Policy %s is missing a description.", policy.get("name"))
            return False
    return True


def lint_allowed_actions(content: YamlContent, allowed_actions: list[str]) -> bool:
    """Check if policy actions are restricted to allowed ones (e.g., tag or notify)."""
    valid = True
    for policy in content.get("policies", []):
        for action in policy.get("actions", []):
            if action not in allowed_actions:
                LOGGER.warning("Policy %s uses forbidden action: %s", policy.get("name"), action)
                valid = False
    return valid


def lint_require_document_separator(input_data: str) -> bool:
    """Ensure YAML document starts with `---`."""
    if not input_data.strip().startswith("---"):
        LOGGER.warning("YAML document does not start with '---'.")
        return False
    return True


def lint_require_comments(input_data: str) -> bool:
    """Check if YAML contains any comments."""
    if "#" not in input_data:
        LOGGER.warning("No comments found in YAML document.")
        return False
    return True


def lint_require_version_comment(input_data: str) -> bool:
    """Check if a Cloud Custodian version comment is present."""
    if "# Cloud Custodian version" not in input_data:
        LOGGER.warning("No Cloud Custodian version comment found.")
        return False
    return True


def lint_cloud_custodian_file(input_data: str, config_path: Optional[Path] = None) -> None:
    """Lint a Cloud Custodian YAML configuration file.

    Args:
        input_data (str): YAML content as a string.
        config_path (Optional[Path]): Path to a config file for enabled rules.
    """
    config = load_config(config_path) if config_path else {}

    # Parse YAML content
    yaml_documents = load_yaml_content(input_data)

    # Apply rules based on configuration
    for doc in yaml_documents:
        if config.get("require_description", True):
            lint_require_description(doc)

        if config.get("allowed_actions", True):
            allowed_actions = config.get("allowed_actions_list", ["tag", "notify"])
            lint_allowed_actions(doc, allowed_actions)

        if config.get("require_document_separator", True):
            lint_require_document_separator(input_data)

        if config.get("require_comments", True):
            lint_require_comments(input_data)

        if config.get("require_version_comment", True):
            lint_require_version_comment(input_data)


def read_input(source: Union[str, Path]) -> str:
    """Reads YAML input from a file or stdin.

    Args:
        source (Union[str, Path]): File path or text piped from stdin.

    Returns:
        str: Content of the YAML file or piped text.
    """
    if isinstance(source, Path) or Path(source).exists():
        with Path(source).open("r", encoding="utf-8") as f:
            return f.read()
    return source  # Assume source is YAML content directly


if __name__ == "__main__":
    # Example usage
    import argparse

    parser = argparse.ArgumentParser(description="Lint a Cloud Custodian YAML file.")
    parser.add_argument(
        "source",
        help="File name or YAML content. If content is piped, it will be treated as YAML directly."
    )
    parser.add_argument(
        "--config",
        type=str,
        default="custodian_linter_config.toml",
        help="Path to the configuration file (default: custodian_linter_config.toml)"
    )

    args = parser.parse_args()

    config_path = Path(args.config)
    yaml_content = read_input(args.source)
    lint_cloud_custodian_file(yaml_content, config_path=config_path)
