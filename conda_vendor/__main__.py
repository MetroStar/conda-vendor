from conda_vendor.cli import (
    create_meta_manifest_from_env_yml,
    create_local_channels_from_meta_manifest,
    create_ironbank_from_meta_manifest,
    create_yaml_from_manifest,
)

import click


@click.group()
def cli():
    pass


@click.command(help="creates a meta-manifest file from an environment yaml file")
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
def create_manifests(environment_yaml, manifest_root, manifest_filename):

    click.echo(manifest_root)
    click.echo(manifest_filename)
    environment_yaml = Path(environment_yaml)
    manifest_root = Path(manifest_root)

    create_meta_manifest_from_env_yml(
        environment_yaml, manifest_root, manifest_filename
    )


@click.command(help="create local channels from an input meta-manifest file")
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


cli.add_command(create_manifests)
cli.add_command(create_channels)


if __name__ == "__main__":
    cli()
