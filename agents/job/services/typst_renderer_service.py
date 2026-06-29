import logging
import os
import json
import subprocess
from typing import Dict, Any, Optional
from core.config import settings

logger = logging.getLogger(__name__)

class TypstRendererService:
    def __init__(
        self,
        enabled: bool = False,
        binary: str = "typst",
        template_root: str = "/opt/cv/lavandula",
        template_main: str = "templates/main.typ",
        data_file: str = "templates/data.json",
        output_dir: str = "outputs",
        font_path: Optional[str] = None
    ):
        self.enabled = enabled
        self.binary = binary
        self.template_root = template_root
        self.template_main = os.path.join(template_root, template_main)
        self.data_file = os.path.join(template_root, data_file)
        self.output_dir = os.path.join(template_root, output_dir)
        self.font_path = font_path or template_root

    async def render(self, typst_data: Dict[str, Any], filename: str) -> Optional[str]:
        if not self.enabled:
            logger.info("Typst rendering is disabled.")
            return None

        try:
            os.makedirs(self.output_dir, exist_ok=True)

            with open(self.data_file, 'w') as f:
                json.dump(typst_data, f, indent=2)

            output_path = os.path.join(self.output_dir, filename)
            cmd = [
                self.binary, "compile",
                "--font-path", self.font_path,
                "--root", self.template_root,
                self.template_main,
                output_path
            ]

            logger.info(f"Running typst compile: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                logger.error(f"Typst compilation failed: {result.stderr}")
                return None

            return output_path
        except Exception as e:
            logger.error(f"Error during Typst rendering: {e}")
            return None
