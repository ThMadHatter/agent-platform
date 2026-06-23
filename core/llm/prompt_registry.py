import os
from jinja2 import Environment, FileSystemLoader, select_autoescape
from typing import Any, Dict

class PromptRegistry:
    def __init__(self, template_dirs: list[str]):
        self.env = Environment(
            loader=FileSystemLoader(template_dirs),
            autoescape=select_autoescape()
        )

    def render(self, template_name: str, **kwargs) -> str:
        template = self.env.get_template(template_name)
        return template.render(**kwargs)
