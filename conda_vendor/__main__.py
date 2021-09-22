from pathlib import Path

import click
from conda_vendor.cli import (
    ironbank_from_meta_manifest,
    local_channels_from_meta_manifest,
    meta_manifest_from_env_yml,
    yaml_from_manifest,
)
from conda_vendor.version import __version__

import logging

logger = logging.getLogger(__name__)


def set_logging_verbosity(verbose):
    if verbose == True:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)


@click.group()
@click.version_option(__version__)
def cli():
    pass


@click.command(help="meta-manifest file from an environment yaml file")
@click.option("-v", "--verbose", is_flag=True, help="verbose logging", is_eager=True)
@click.option(
    "--environment-yaml",
    "-f",
    default="environment.yaml",
    help="path to input conda environment yaml file",
)
@click.option(
    "--manifest-root",
    "-o",
    default="./",
    help="directory where manifest will be output",
)
@click.option(
    "--manifest-filename",
    "-m",
    default="meta_manifest.yaml",
    help="filename of output manifest",
)
@click.option(
    "--custom-platform",
    "-c",
    default=None,
    type=click.Choice(["linux-64", "linux-32", "windows-64", "windows-32", "osx-64"]),
    help="Specify an alternate platform to use for the conda solve.",
)
def meta_manifest(
    verbose, environment_yaml, manifest_root, manifest_filename, custom_platform,
):
    set_logging_verbosity(verbose)
    click.echo(manifest_root)
    click.echo(manifest_filename)
    environment_yaml = Path(environment_yaml)
    manifest_root = Path(manifest_root)

    meta_manifest_from_env_yml(
        environment_yaml, manifest_root, manifest_filename, custom_platform,
    )


@click.command(help="local channels from meta-manifest file")
@click.option("-v", "--verbose", is_flag=True, help="verbose logging", is_eager=True)
@click.option(
    "--channel-root",
    "-c",
    default="./local_channel",
    help="directory where local channels will be output",
)
@click.option(
    "--meta-manifest-path",
    "-m",
    default="./meta_manifest.yaml",
    help="path to meta manifest file",
)
def channels(verbose, channel_root, meta_manifest_path):
    set_logging_verbosity(verbose)
    channel_root = Path(channel_root)
    meta_manifest_path = Path(meta_manifest_path)
    local_channels_from_meta_manifest(channel_root, meta_manifest_path)


@click.command(help="custom manifest from meta-manifest file")
@click.option("-v", "--verbose", is_flag=True, help="verbose logging", is_eager=True)
@click.option(
    "--manifest-type", default="iron-bank", help="type of custom manifest to create"
)
@click.option(
    "--meta-manifest-path",
    "-m",
    default="./meta_manifest.yaml",
    help="path to meta manifest file",
)
@click.option(
    "--output-manifest-path", "-o", default="./", help="output manifest path",
)
def custom_manifest(verbose, manifest_type, meta_manifest_path, output_manifest_path):
    set_logging_verbosity(verbose)
    meta_manifest_path = Path(meta_manifest_path)
    output_manifest_path = Path(output_manifest_path)

    if manifest_type == "iron-bank":
        ironbank_from_meta_manifest(
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
@click.option("-v", "--verbose", is_flag=True, help="verbose logging", is_eager=True)
@click.option(
    "--channel-root",
    default="./local_channel",
    help="directory where local channels are stored, and directory where the environment yaml will be output",
)
@click.option(
    "--meta-manifest-path",
    "-m",
    default="./meta_manifest.yaml",
    help="path to meta manifest file",
)
@click.option(
    "--env-name",
    "-n",
    default="conda-vendor-env",
    help="name of conda environment to be defined in yaml",
)
def local_yaml(verbose, channel_root, meta_manifest_path, env_name):
    set_logging_verbosity(verbose)
    channel_root = Path(channel_root)
    meta_manifest_path = Path(meta_manifest_path)
    yaml_from_manifest(channel_root, meta_manifest_path, env_name)


cli.add_command(meta_manifest)
cli.add_command(channels)
cli.add_command(custom_manifest)
cli.add_command(local_yaml)


if __name__ == "__main__":
    cli()
