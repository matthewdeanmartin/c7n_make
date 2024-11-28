import yaml


class FilterBuilder:
    """A builder class for defining filters in a Cloud Custodian policy."""

    def __init__(self, name):
        self.name = name
        self.params = {}

    def value(self, val):
        """Sets a value for a simple equality filter."""
        self.params["value"] = val
        return self

    def custom(self, **kwargs):
        """Sets custom parameters for the filter."""
        self.params.update(kwargs)
        return self

    def build(self):
        """Constructs the filter as a dictionary."""
        return {self.name: self.params} if self.params else self.name


class ActionBuilder:
    """A builder class for defining actions in a Cloud Custodian policy."""

    def __init__(self, action_type):
        self.action_type = action_type
        self.params = {}

    def set_key(self, key):
        """Sets a key for the action, such as in tagging actions."""
        self.params["key"] = key
        return self

    def set_value(self, value):
        """Sets a value for the action, such as in tagging actions."""
        self.params["value"] = value
        return self

    def custom(self, **kwargs):
        """Sets custom parameters for the action."""
        self.params.update(kwargs)
        return self

    def build(self):
        """Constructs the action as a dictionary."""
        return {self.action_type: self.params} if self.params else self.action_type


class PolicyBuilder:
    """A builder class for constructing Cloud Custodian policies."""

    def __init__(self, name):
        self.name = name
        self.resource_type = None
        self.execution_mode = None  # Renamed from `mode` to `execution_mode` to avoid conflict
        self.filters = []
        self.actions = []

    def resource(self, resource_type):
        """Sets the resource type for the policy."""
        self.resource_type = resource_type
        return self

    def mode(self, mode_type, **kwargs):
        """Sets the execution mode and any additional parameters."""
        self.execution_mode = {"type": mode_type}
        self.execution_mode.update(kwargs)
        return self

    def add_filter(self, filter_builder):
        """Adds a filter to the policy."""
        if isinstance(filter_builder, FilterBuilder):
            self.filters.append(filter_builder.build())
        return self

    def add_action(self, action_builder):
        """Adds an action to the policy."""
        if isinstance(action_builder, ActionBuilder):
            self.actions.append(action_builder.build())
        return self

    def build(self):
        """Constructs the policy as a dictionary."""
        policy = {
            "name": self.name,
            "resource": self.resource_type,
            "filters": self.filters,
            "actions": self.actions,
        }
        if self.execution_mode:
            policy["mode"] = self.execution_mode
        return policy

    def export_to_yaml(self):
        """Exports the policy to a YAML format string."""
        return yaml.dump({"policies": [self.build()]}, default_flow_style=False)

if __name__ == '__main__':
    def run():
        # Example usage
        policy = (
            PolicyBuilder("ec2-stop-policy")
            .resource("ec2")
            .mode("periodic", schedule="rate(5 minutes)")
            .add_filter(FilterBuilder("InstanceId").value("i-1234567890abcdef0"))
            .add_action(ActionBuilder("stop"))
            .add_action(ActionBuilder("tag").set_key("Owner").set_value("DevOps"))
        )

        # Export policy to YAML
        yaml_output = policy.export_to_yaml()
        print(yaml_output)
    run()