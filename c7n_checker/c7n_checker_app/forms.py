from django import forms


class YamlForm(forms.Form):
    yaml_content = forms.CharField(widget=forms.Textarea, label="YAML Content")
