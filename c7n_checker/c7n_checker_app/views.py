import os
import subprocess
import tempfile
from typing import Optional

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views import View

from c7n_checker.c7n_checker_app.forms import YamlForm


class ValidateYamlView(View):
    template_name = "checker.jinja2"

    def get(self, request: HttpRequest) -> HttpResponse:
        form = YamlForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request: HttpRequest) -> HttpResponse:
        form = YamlForm(request.POST)

        yaml_validation: Optional[str] = None
        validation_output: Optional[str] = None
        dry_run_output: Optional[str] = None


        if form.is_valid():
            yaml_content = form.cleaned_data["yaml_content"]
            yaml_validation = self.run_yaml_validate(yaml_content)
            validation_output = self.run_custodian_command(yaml_content, validate=True)
            dry_run_output = self.run_custodian_command(yaml_content, validate=False)

        return render(
            request,
            self.template_name,
            {
                "form": form,
                "validation_output": validation_output,
                "dry_run_output": dry_run_output,
                "yaml_validation_output": yaml_validation,
            },
        )

    def run_yaml_validate(self, yaml_content: str) -> str:
        """
        Validate yaml as yaml. Don't check schema
        """
        import yaml
        try:
            yaml.load(yaml_content, Loader=yaml.FullLoader)
        except yaml.YAMLError as exc:
            complaint = str(exc)
            return complaint
        # Blank means fine
        return ""

    def run_custodian_command(self, yaml_content: str, validate: bool) -> str:
        # Create a temporary file to store the YAML content
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.yaml') as temp_file:
            temp_file.write(yaml_content)
            temp_file_path = temp_file.name

        # Construct the command using the temporary file path
        if validate:
            command = ["custodian", "validate", "--verbose", temp_file_path]
        else:
            command = ["custodian", "run", "-s", "logs", "--verbose", temp_file_path]

        try:
            process = subprocess.run(
                command,
                text=True,
                capture_output=True,
                check=True,
                env=dict(os.environ) | {"AWS_PROFILE": "moto"}
            )
            return process.stdout + process.stderr
        except subprocess.CalledProcessError as e:
            return e.stdout + e.stderr
        finally:
            # Delete the temporary file after the command has been executed
            os.remove(temp_file_path)
