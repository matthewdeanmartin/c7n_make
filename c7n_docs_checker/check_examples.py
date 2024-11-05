import multiprocessing
import os
import subprocess
import logging
from pathlib import Path
from typing import List

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

from docutils.core import publish_doctree
from docutils.nodes import literal_block


def extract_code_blocks_from_rst(file_path: Path) -> List[str]:
    # Read the RST file contents
    with file_path.open('r', encoding='utf-8') as file:
        rst_content = file.read()

    # Parse the RST content into a document tree
    doctree = publish_doctree(rst_content)

    yaml_blocks = []

    # Traverse the document tree to find YAML code blocks
    for node in doctree.traverse(literal_block):
        # Check if the code block is labeled as YAML
        if 'yaml' in node.get('classes', []):
            # Collect the raw text of the code block
            yaml_blocks.append(node.astext())

    return yaml_blocks



def go_extract() -> None:
    examples = {
        # "root": Path(r'C:\github\cloud-custodian\docs\source'), filters.rst is almonst entirely fragments.
        "kubernetes": Path(r'C:\github\cloud-custodian\docs\source\kubernetes'),
        "kubernetes_examples": Path(r'C:\github\cloud-custodian\docs\source\kubernetes\examples'),
        "developer": Path(r'C:\github\cloud-custodian\docs\source\developer'),
        "aws_examples": Path(r'C:\github\cloud-custodian\docs\source\aws\examples'),
        "aws_quickstart": Path(r'C:\github\cloud-custodian\docs\source\quickstart'),
        "aws_topics": Path(r'C:\github\cloud-custodian\docs\source\aws\topics'),
        "aws": Path(r'C:\github\cloud-custodian\docs\source\aws'),
        "azure": Path(r'C:\github\cloud-custodian\docs\source\azure'),
        "azure_advanced": Path(r'C:\github\cloud-custodian\docs\source\azure\advanced'),
        "azure_configuration": Path(r'C:\github\cloud-custodian\docs\source\azure\configuration'),
        "azure_configuration_resources": Path(r'C:\github\cloud-custodian\docs\source\azure\configuration\resources'),
        "azure_examples_lna": Path(r'C:\github\cloud-custodian\docs\source\azure\examples\logicappnotifications'),
        # "azure_examples_lna_r": Path(r'C:\github\cloud-custodian\docs\source\azure\examples\logicappnotifications\resources'),
        "azure_examples": Path(r'C:\github\cloud-custodian\docs\source\azure\examples'),
        "gcp": Path(r'C:\github\cloud-custodian\docs\source\gcp'),
        "gcp_examples": Path(r'C:\github\cloud-custodian\docs\source\gcp\examples'),
        "gcp_policy": Path(r'C:\github\cloud-custodian\docs\source\gcp\policy'),
        "gcp_policy_resources": Path(r'C:\github\cloud-custodian\docs\source\gcp\policy\resources'),
        "oci": Path(r'C:\github\cloud-custodian\docs\source\oci'),
        "oci_examples": Path(r'C:\github\cloud-custodian\docs\source\oci\examples'),
        "oci_advanced": Path(r'C:\github\cloud-custodian\docs\source\oci\advanced'),
    }

    for name, path in examples.items():
        current_folder = path
        rst_files = current_folder.glob('*.rst')

        for rst_file in rst_files:
            # if not "Metadata" in rst_file.stem:
            #     continue
            yaml_blocks = extract_code_blocks_from_rst(rst_file)

            if yaml_blocks:
                for i, yaml_block in enumerate(yaml_blocks, start=1):
                    yaml_filename = f"examples/{name}/{rst_file.stem}_{i}.yaml" if len(
                        yaml_blocks) > 1 else f"examples/{name}/{rst_file.stem}.yaml"
                    os.makedirs(os.path.dirname(yaml_filename), exist_ok=True)
                    with open(yaml_filename, 'w', encoding="utf-8") as yaml_file:
                        yaml_file.write(yaml_block)
                        print(f"Extracted YAML block saved to {yaml_filename}")


def validate_file(file_path: Path) -> tuple[Path, bool, str]:
    """Validates a YAML file using the `custodian validate` command.

    Args:
        file_path (Path): Path to the YAML file.

    Returns:
        tuple[Path, bool, str]: The file path, validation status (True if passed, False if failed),
        and any error message if the validation failed.
    """
    LOGGER.info(f"Validating {file_path}...")

    full_text = file_path.read_text(encoding="utf-8")
    if "export OCI" in full_text:
        # Bash, not yaml
        return file_path, True, ""

    #
    if file_path.name in ["deployment_2.yaml"]:
        # This is a github action
        return file_path, True, ""

    if file_path.name in ["policyStructure.yaml"]:
        # Too heavily annotated
        return file_path, True, ""
    if "repos:" in full_text:
        # Precommit
        return file_path, True, ""
    if "apiVersion: rbac.authorization.k8s.io/v1" in full_text:
        # K8s
        return file_path, True, ""
    if "helm-values.yaml" in full_text:
        # Helm
        return file_path, True, ""

    if "account-service-limits" in full_text:
        # Helm
        return file_path, True, ""

    if "ec2-checker" in full_text:
        # Fixed but not merged.
        return file_path, True, ""

    if "remediate" in full_text:
        # Fixed but not merged. (Error on policy:remediate resource:aws.iam)
        return file_path, True, ""

    if "ec2-auto-tag-ownercontact" in full_text:
        # triple nested (yaml in python in rst) extractor can't handle this ...yet.
        return file_path, True, ""

    if "image: nginx:1.14.2" in full_text:
        # actually k8s yaml
        return file_path, True, ""

    # if "config_2.yaml" in str(file_path):
    #     # I'm stumped. I can't figure out how to fix this
    #     # I think it is buggy but can't figure out if it is a CC problem or a yaml policy problem.
    #     return file_path, True, ""
    #
    # if "securityhub_2.yaml" in str(file_path):
    #     # I'm stumped. I can't figure out how to fix this
    #     # hub-finding as a mode?
    #     return file_path, True, ""
    # if "update-cross-connect" in full_text:
    #     # Unknown action, valid alts are remove-tag, webhook
    #     return file_path, True, ""

    if "─▶" in full_text:
        # read file, remove anything after ─▶ in a line by line fashion
        # rewrite to same file
        with file_path.open('r', encoding="utf-8") as file:
            lines = file.readlines()
        with file_path.open('w', encoding="utf-8") as file:
            for line in lines:
                if "─▶" in line:
                    line = line.split("─▶")[0] + "\n"
                file.write(line)

    if not "policies:" in full_text:
        return revalidate_with_header(file_path)



    try:
        result = subprocess.run(
            ["custodian", "validate", str(file_path).replace("\\", "/")],
            check=True,
            capture_output=True,
            text=True,
            env=os.environ | {'AWS_DEFAULT_REGION': 'us-east-1'}
        )
        return file_path, True, ""
    except subprocess.CalledProcessError as e:
        if "Get the size of a group" in full_text:
            # Intensional fragment
            return file_path, True, ""

        if "Find expiry from tag contents" in full_text:
            # Intensional fragment
            return file_path, True, ""

        if "http://foo.com?hook-id=123" in full_text:
            # Intensional fragment
            return file_path, True, ""

        if "discard-percent: 20" in full_text:
            # Intensional fragment
            return file_path, True, ""

        if "discard-percent: 25" in full_text:
            # Intensional fragment
            return file_path, True, ""


        # Capture and return the error message

        # if ("Policy files top level keys" in e.stderr and
        #         ("lambda_2" in str(file_path) or "lambda_8" in str(file_path))):
        #     # Yaml fragment.
        #     return file_path, True, ""

        return file_path, False, e.stderr

def revalidate_with_header(file_path: Path) -> tuple[Path, bool, str]:
    # write a copy of the file in same place with name %_with_header.yaml
    # add a header to the file
    # Validate it.

    with file_path.open('r', encoding="utf-8") as file:
        full_text = file.read()
        if not "policies:" in full_text:
            indented_full_text = "\n".join(["  " + line for line in full_text.split("\n")])

            # add the `policies:` header line
            full_text = "policies:\n" + indented_full_text

            new_file_path = file_path.with_name(file_path.stem + "_with_header.yaml")
            with new_file_path.open('w', encoding="utf-8") as new_file:
                new_file.write(full_text)

    try:
        result = subprocess.run(
            ["custodian", "validate", str(new_file_path).replace("\\", "/")],
            check=True,
            capture_output=True,
            text=True,
            env=os.environ | {'AWS_DEFAULT_REGION': 'us-east-1'}
        )
        return file_path, True, ""
    except subprocess.CalledProcessError as e:
        # Capture and return the error message

        if ("Policy files top level keys" in e.stderr and
                ("lambda_2" in str(file_path) or "lambda_8" in str(file_path))):
            # Yaml fragment.
            return file_path, True, ""

        return file_path, False, e.stderr

def collect_yaml_files(folder: Path) -> List[Path]:
    """Collects all .yml and .yaml files from the specified folder and its subdirectories.

    Args:
        folder (Path): The root folder to start searching from.

    Returns:
        List[Path]: A list of paths to the found .yml and .yaml files.
    """
    yaml_files = list(folder.rglob("*.yml")) + list(folder.rglob("*.yaml"))
    return yaml_files


def validate_files_in_parallel(files: List[Path]) -> List[tuple[Path, bool, str]]:
    """Validates YAML files in parallel using available CPU cores.

    Args:
        files (List[Path]): List of YAML file paths to validate.

    Returns:
        List[tuple[Path, bool, str]]: A list of results, where each result is a tuple containing
        the file path, validation status, and an error message if any.
    """
    with multiprocessing.Pool() as pool:
        results = pool.map(validate_file, files)
    # results = []
    # for file in files:
    #     results.append(validate_file(file))
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


def validate_yaml_files_in_folder(parent_folder: Path) -> None:
    """Traverses through the parent folder and validates all .yml and .yaml files found within
    its subdirectories.

    Args:
        parent_folder (Path): The root folder to start searching for YAML files.
    """
    # Collect all .yml and .yaml files from the folder and its subdirectories
    yaml_files = collect_yaml_files(parent_folder)

    if not yaml_files:
        LOGGER.info(f"No YAML files found in {parent_folder}.")
        return

    LOGGER.info(f"Found {len(yaml_files)} YAML file(s) to validate.")

    # Validate files in parallel
    results = validate_files_in_parallel(yaml_files)

    # Collect failures
    failures = [result for result in results if not result[1]]

    # Print out the results of failed validations
    print_failures(failures)


if __name__ == "__main__":
    go_extract()
    # Define the parent folder containing all subfolders
    parent_folder = Path("examples")

    # Start the validation process
    validate_yaml_files_in_folder(parent_folder)
