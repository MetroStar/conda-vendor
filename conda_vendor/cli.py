from pathlib import Path

from conda_vendor.conda_channel import CondaChannel
from conda_vendor.custom_manifest import IBManifest
from conda_vendor.env_yaml_from_manifest import YamlFromManifest
from conda_vendor.manifest import MetaManifest


def meta_manifest_from_env_yml(
    environment_yaml, manifest_root, manifest_filename, custom_platform=None,
):
    conda_channel = MetaManifest(
        environment_yaml, manifest_root=manifest_root, custom_platform=custom_platform,
    )
    conda_channel.create_manifest(manifest_filename=manifest_filename)


def local_channels_from_meta_manifest(channel_root, meta_manifest_path):
    conda_channel = CondaChannel(
        channel_root=channel_root, meta_manifest_path=meta_manifest_path
    )
    conda_channel.write_repo_data()
    conda_channel.download_binaries()


def ironbank_from_meta_manifest(meta_manifest_path, output_manifest_dir):
    custom_manifest = IBManifest(meta_manifest_path)
    custom_manifest.write_custom_manifest(output_manifest_dir)


def yaml_from_manifest(channel_root, meta_manifest_path, env_name):
    george_forge = YamlFromManifest(channel_root, meta_manifest_path=meta_manifest_path)
    george_forge.create_yaml(channel_root, env_name)
