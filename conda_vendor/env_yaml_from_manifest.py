from pathlib import Path

import yaml


class YamlFromManifest:
    def __init__(self, channel_root, meta_manifest_path=Path()):
        self.meta_manifest_path = meta_manifest_path
        self.meta_manifest = self.load_manifest(self.meta_manifest_path)

    def load_manifest(self, meta_manifest_path):
        with open(meta_manifest_path) as f:
            return yaml.load(f, Loader=yaml.SafeLoader)

    def get_packages_from_manifest(self):
        i_bank_pkg_list = []
        for channel_dict in self.meta_manifest.values():
            for platform_dict in channel_dict.values():
                for package_dict in platform_dict["entries"]:
                    name = package_dict["name"]
                    version = package_dict["version"]
                    dep_entry = f"{name}={version}"
                    i_bank_pkg_list.append(dep_entry)
        i_bank_pkg_list
        return i_bank_pkg_list

    def get_local_channels_paths(self, channel_root: Path):
        channel_paths = [
            str(channel_root / f"local_{c}") for c in self.meta_manifest.keys()
        ]
        return channel_paths

    def create_yaml(self, channel_root, env_name):
        package_list = self.get_packages_from_manifest()
        channel_list = self.get_local_channels_paths(channel_root)
        env_yaml = {
            "name": env_name,
            "channels": channel_list,
            "dependencies": package_list,
        }
        fn = channel_root / f"local_{env_name}.yaml"
        with open(fn, "w") as f:
            yaml.dump(env_yaml, f, sort_keys=False)
        return env_yaml
