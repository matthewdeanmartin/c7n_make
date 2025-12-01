import logging
from pathlib import Path
from typing import List

from docutils.core import publish_doctree
from docutils.nodes import literal_block
from ruamel.yaml import YAML


LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

import ast
import textwrap


def extract_docstrings(source_code: str) -> List[str]:
    """Extracts all docstrings from the given Python source code.

    Args:
        source_code: A string containing the Python source code.

    Returns:
        A list of cleaned docstring blocks found in the source code.
    """
    docstrings = []
    parsed_ast = ast.parse(source_code)

    for node in ast.walk(parsed_ast):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
            docstring = ast.get_docstring(node)
            if docstring:
                # Clean up indentation for the docstring
                cleaned_docstring = textwrap.dedent(docstring)
                docstrings.append(cleaned_docstring)

    return docstrings


def fix_policies_file(file_path: Path) -> None:
    """
    Reads a YAML file, checks for the 'policies:' header, and ensures the
    content is a list under the 'policies' key.

    Args:
        file_path (Path): The path to the file that needs to be fixed.
    """
    # Step 1: Read the file
    try:
        with file_path.open("r", encoding="utf-8") as file:
            yaml = YAML(typ='rt')
            data = yaml.load(file)
    except FileNotFoundError:
        LOGGER.error(f"File not found: {file_path}")
        return
    except Exception as e:
        LOGGER.error(f"Error reading YAML file {file_path}: {e}")
        return

    # Step 2: Check if 'policies:' header exists
    if 'policies' not in data:
        LOGGER.info("'policies:' header missing, adding it.")
        # If the data is a dictionary, convert it to a list of one dictionary
        if isinstance(data, dict):
            data = {'policies': [data]}
            LOGGER.info("Converted dictionary to a list under 'policies:'")
        # If the data is a list, nest it under 'policies'
        elif isinstance(data, list):
            data = {'policies': data}
            LOGGER.info("Wrapped list under 'policies:'")
        else:
            LOGGER.error("Unexpected YAML structure. Expected a list or dict.")
            return

    # Step 3: Write the corrected data back to the file
    try:
        with file_path.open("w", encoding="utf-8") as file:
            yaml.dump(data, file)
        LOGGER.info(f"File corrected and saved: {file_path}")
    except Exception as e:
        LOGGER.error(f"Error writing YAML file {file_path}: {e}")


# def fix_policies_file(file_path: Path) -> None:
#     """
#     Reads a file, checks for the 'policies:' header, and corrects leading spaces in the policies section.
#
#     Args:
#         file_path (Path): The path to the file that needs to be fixed.
#     """
#     # Step 1: Read the file
#     try:
#         with file_path.open("r", encoding="utf-8") as file:
#             lines = file.readlines()
#     except FileNotFoundError:
#         LOGGER.error(f"File not found: {file_path}")
#         return
#
#     has_header = False
#     corrected_lines = []
#
#     # Constants for formatting
#     correct_header = "policies:\n"
#
#     # Step 2: Process each line
#     for line in lines:
#         if not line.startswith("    ") and line != "" and not line.startswith("policies:"):
#             # probably not yaml
#             continue
#         stripped_line = line.lstrip()
#
#         # Check if the 'policies:' header is present
#         if stripped_line.startswith("policies:"):
#             has_header = True
#             corrected_lines.append(correct_header)
#             continue
#
#         # Add unmodified lines
#         corrected_lines.append(line)
#
#     # Step 3: Add the header if it was missing
#     if not has_header:
#         LOGGER.info(f"'policies:' header missing, adding it.")
#         corrected_lines.insert(0, correct_header)
#
#     # Step 4: Write the corrected lines back to the file
#     with file_path.open("w", encoding="utf-8") as file:
#         file.writelines(corrected_lines)
#
#     LOGGER.info(f"File corrected and saved: {file_path}")

def yaml_blocks_in_rst_string(rst_content: str) -> List[str]:
    # Parse the RST content into a document tree
    doctree = publish_doctree(rst_content)

    yaml_blocks = []

    # Traverse the document tree to find YAML code blocks
    for node in doctree.traverse(literal_block):
        # Check if the code block is labeled as YAML
        if 'yaml' in node.get('classes', []):
            # Collect the raw text of the code block
            print(node)
            yaml_blocks.append(node.astext())

    return yaml_blocks


def extract_code_blocks_from_rst(file_path: Path) -> List[str]:
    """
    Extract YAML code blocks from reStructuredText (reST) docstrings in the given file.
    Start a new block if 'policies:' is found and terminate if a line with '\"\"\"' is encountered.

    Args:
        file_path (Path): The path to the Python source file.

    Returns:
        List[str]: A list of extracted YAML code blocks.
    """

    all_yaml_blocks = []

    with file_path.open('r', encoding="utf-8") as file:
        lines_text = file.read()
        if "─▶" in lines_text:
            fixed_lines = []
            for line in lines_text.split("\n"):
                if "─▶" in line:
                    line = line.split("─▶")[0] + "\n"
                fixed_lines.append(line)
            lines_text = "\n".join(fixed_lines)

        docstrings_blocks = extract_docstrings(lines_text)
        for docstring in docstrings_blocks:
            yaml_blocks = yaml_blocks_in_rst_string(docstring)
            all_yaml_blocks.extend(yaml_blocks)

    return all_yaml_blocks


def save_yaml_snippets(source_directory: Path, destination_dir: Path, source_file: Path,
                       yaml_blocks: List[str]) -> None:
    """
    Save extracted YAML blocks into separate .yml files in the destination directory,
    while preserving the source file's directory structure.

    Args:
        destination_dir (Path): The base directory where YAML files should be saved.
        source_file (Path): The source Python file from which YAML was extracted.
        yaml_blocks (List[str]): A list of YAML snippets to be saved.
    """
    relative_path = source_file.relative_to(source_directory)
    file_stem = relative_path.stem
    relative_dir = relative_path.parent

    # Ensure the corresponding sub-directory in the destination exists
    destination_subdir = destination_dir / relative_dir
    destination_subdir.mkdir(parents=True, exist_ok=True)

    for index, yaml_content in enumerate(yaml_blocks, start=1):
        yaml_filename = f"{file_stem}_{index}.yml"
        yaml_file_path = destination_subdir / yaml_filename

        # Write the YAML content to the file
        with yaml_file_path.open("w", encoding="utf-8") as yaml_file:
            yaml_file.write(yaml_content)

        LOGGER.info(f"Saved YAML block to: {yaml_file_path}")
        fix_policies_file(yaml_file_path)


def process_py_files(source_dir: Path, destination_dir: Path) -> None:
    """
    Walk through the source directory, find .py files, extract YAML blocks,
    and save them to the destination directory, preserving the folder structure.

    Args:
        source_dir (Path): The root directory to search for .py files.
        destination_dir (Path): The directory where extracted YAML files will be saved.
    """
    # Recursively search for Python files in the source directory
    for py_file in source_dir.rglob("*.py"):
        LOGGER.info(f"Processing file: {py_file}")
        try:
            # Extract YAML code blocks from the Python file
            yaml_blocks = extract_code_blocks_from_rst(py_file)

            if yaml_blocks:
                # Save extracted YAML blocks to destination directory
                save_yaml_snippets(source_dir, destination_dir, py_file, yaml_blocks)
            else:
                LOGGER.info(f"No YAML blocks found in {py_file}")

        except Exception as e:
            LOGGER.error(f"Failed to process {py_file}: {e}")


if __name__ == "__main__":
    # Define source and destination directories
    # source_directory = Path(r"C:\github\cloud-custodian\c7n")  # Replace with the actual source directory
    # destination_directory = Path("examples_from_src")  # Replace with the actual destination directory
    #
    # # Start processing Python files
    # process_py_files(source_directory, destination_directory)
    #
    # # Start the validation process
    # validate_yaml_files_in_folder(destination_directory)

    print(yaml_blocks_in_rst_string("""Filter an EC2 instance that has an IAM instance profile that contains an IAM role that has
       a specific managed IAM policy. If an EC2 instance does not have a profile or the profile
       does not contain an IAM role, then it will be treated as not having the policy.

:example:

.. code-block:: yaml

    policies:
      - name: ec2-instance-has-admin-policy
        resource: aws.ec2
        filters:
          - type: has-specific-managed-policy
            value: admin-policy

:example:

Check for EC2 instances with instance profile roles that have an
attached policy matching a given list:

.. code-block:: yaml

    policies:
      - name: ec2-instance-with-selected-policies
        resource: aws.ec2
        filters:
          - type: has-specific-managed-policy
            op: in
            value:
              - AmazonS3FullAccess
              - AWSOrganizationsFullAccess

:example:

Check for EC2 instances with instance profile roles that have
attached policy names matching a pattern:

.. code-block:: yaml

    policies:
      - name: ec2-instance-with-full-access-policies
        resource: aws.ec2
        filters:
          - type: has-specific-managed-policy
            op: glob
            value: "*FullAccess"

Check for EC2 instances with instance profile roles that have
attached policy ARNs matching a pattern:

.. code-block:: yaml

    policies:
      - name: ec2-instance-with-aws-full-access-policies
        resource: aws.ec2
        filters:
          - type: has-specific-managed-policy
            key: PolicyArn
            op: regex
            value: "arn:aws:iam::aws:policy/.*FullAccess"
    """))
