from abc import ABC, abstractmethod
import os
from pathlib import Path
import yaml


# eats a meta_manifest shits custom one


class CustomManifest(ABC):
    def __init__(self, manifest_path=Path()):
        self.manifest_path = Path(manifest_path)
        self.manifest_root = self.manifest_path.parent
        self.custom_manifest = None
        self.meta_manifest = self.read_meta_manifest(self.manifest_path)

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
    def write_custom_manifest(self, output_file_dir=None):
        if output_file_dir is None:
            output_file_dir = self.manifest_root

        if self.custom_manifest is None:
            self.custom_manifest = self.format_custom_manifest()

        output_file_dir = output_file_dir / "ironbank_manifest.yaml"
        with open(output_file_dir, "w") as f:
            yaml.dump(self.custom_manifest, f, sort_keys=False)

    @staticmethod
    def strip_lead_underscore(in_str):
        if in_str.startswith("_"):
            return in_str.lstrip("_")
        else:
            return in_str

    def format_custom_manifest(self):
        i_bank_pkg_list = []

        for _, channel_dict in self.meta_manifest.items():
            for _, platform_dict in channel_dict.items():
                for package_dict in platform_dict["entries"]:
                    name = IBManifest.strip_lead_underscore(package_dict["name"])

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

        return iron_bank_manifest
