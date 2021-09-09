from pathlib import Path

import click
from conda_vendor.cli import (create_ironbank_from_meta_manifest,
                              create_local_channels_from_meta_manifest,
                              create_meta_manifest_from_env_yml,
                              create_yaml_from_manifest)
from conda_vendor.version import __version__


@click.group()
@click.version_option(__version__)
def cli():
    pass


@click.command(help="meta-manifest file from an environment yaml file")
@click.option(
    "--environment-yaml",
    default="environment.yaml",
    help="path to input conda environment yaml file",
)
@click.option(
    "--manifest-root", default="./", help="directory where manifest will be output"
)
@click.option(
    "--manifest-filename",
    default="meta_manifest.yaml",
    help="filename of output manifest",
)
def create_meta_manifest(environment_yaml, manifest_root, manifest_filename):

    click.echo(manifest_root)
    click.echo(manifest_filename)
    environment_yaml = Path(environment_yaml)
    manifest_root = Path(manifest_root)

    create_meta_manifest_from_env_yml(
        environment_yaml, manifest_root, manifest_filename
    )


@click.command(help="local channels from meta-manifest file")
@click.option(
    "--channel-root",
    default="./local_channel",
    help="directory where local channels will be output",
)
@click.option(
    "--meta-manifest-path",
    default="./meta_manifest.yaml",
    help="path to meta manifest file",
)
def create_channels(channel_root, meta_manifest_path):
    channel_root = Path(channel_root)
    meta_manifest_path = Path(meta_manifest_path)
    create_local_channels_from_meta_manifest(channel_root, meta_manifest_path)


@click.command(help="custom manifest from meta-manifest file")
@click.option(
    "--manifest-type", default="iron-bank", help="type of custom manifest to create"
)
@click.option(
    "--meta-manifest-path",
    default="./meta_manifest.yaml",
    help="path to meta manifest file",
)
@click.option(
    "--output-manifest-path",
    default="./",
    help="output manifest path",
)
def create_custom_manifest(manifest_type, meta_manifest_path, output_manifest_path):
    meta_manifest_path = Path(meta_manifest_path)
    output_manifest_path = Path(output_manifest_path)

    if manifest_type == "iron-bank":
        create_ironbank_from_meta_manifest(
            meta_manifest_path=meta_manifest_path,
            output_manifest_dir=output_manifest_path,
        )
    else:
        error_str = f'Manifest type "{manifest_type}" not supported'
        raise TypeError(error_str)


@click.command(
    help="""conda environment.yaml file based on the metamanifest, 
    and path to the local channels"""
)
@click.option(
    "--channel-root",
    default="./local_channel",
    help="directory where local channels are stored, and directory where the environment yaml will be output",
)
@click.option(
    "--meta-manifest-path",
    default="./meta_manifest.yaml",
    help="path to meta manifest file",
)
@click.option(
    "--env-name",
    default="conda-vendor-env",
    help="name of conda environment defined in yaml",
)
def create_local_yaml(channel_root, meta_manifest_path, env_name):
    channel_root = Path(channel_root)
    meta_manifest_path = Path(meta_manifest_path)
    create_yaml_from_manifest(channel_root, meta_manifest_path, env_name)


cli.add_command(create_meta_manifest)
cli.add_command(create_channels)
cli.add_command(create_custom_manifest)
cli.add_command(create_local_yaml)


if __name__ == "__main__":
    cli()
