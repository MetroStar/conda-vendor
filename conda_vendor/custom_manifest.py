import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)


class CustomManifest(ABC):
    def __init__(self, manifest_path=Path()):
        self.manifest_path = Path(manifest_path)
        self.manifest_root = self.manifest_path.parent
        self.custom_manifest = None
        self.meta_manifest = self.read_meta_manifest(self.manifest_path)
        logger.info(f"Input Manifest : {str(self.manifest_path.absolute())}")

    def read_meta_manifest(self, manifest_path):
        with open(self.manifest_path) as f:
            return yaml.load(f, Loader=yaml.SafeLoader)

    @abstractmethod
    def write_custom_manifest(self, output_path=None):
        pass

    @abstractmethod
    def format_custom_manifest(self):
        pass


class IBManifest(CustomManifest):
    def write_custom_manifest(self, output_file_path=None):
        if output_file_path is None:
            output_file_path = self.manifest_root / "ironbank_manifest.yaml"

        self.format_custom_manifest()

        logger.info(f"Output Custom Manifest : {str(output_file_path.absolute())}")
        with open(output_file_path, "w") as f:
            yaml.dump(self.custom_manifest, f, sort_keys=False)

    @staticmethod
    def strip_lead_underscore(in_str):
        if in_str.startswith("_"):
            return in_str.lstrip("_")
        else:
            return in_str

    def format_custom_manifest(self):
        if self.custom_manifest is not None:
            return self.custom_manifest

        i_bank_pkg_list = []

        for _, channel_dict in self.meta_manifest.items():
            for _, platform_dict in channel_dict.items():
                for package_dict in platform_dict["entries"]:
                    name = IBManifest.strip_lead_underscore(package_dict["fn"])

                    i_bank_entry = {
                        "url": package_dict["url"],
                        "filename": name,
                        "validation": {
                            "type": "sha256",
                            "value": package_dict["sha256"],
                        },
                    }
                    i_bank_pkg_list.append(i_bank_entry)
        iron_bank_manifest = {"resources": i_bank_pkg_list}
        self.custom_manifest = iron_bank_manifest
        return iron_bank_manifest
