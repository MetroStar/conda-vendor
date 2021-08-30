import argparse
import functools
import os
from pathlib import Path
import sys
import yaml

# TODO:
#   needs better user experience

from conda_vendor.core import (
    get_manifest,
    create_manifest,
    get_local_environment_yaml,
    create_local_environment_yaml,
    create_local_channels,
    CondaChannel,
)

# manifest commands
# need
class CommandManifest:
    def __init__(self, parent_parser, cmd_str):
        self.cmd_str = cmd_str
        parser = parent_parser.add_parser(cmd_str, help="mainifest commands")
        parser.add_argument("-f", "--file", type=str, help="environment.yaml file")
        parser.add_argument("--dry-run", action="store_true", help="print manifest")
        parser.add_argument(
            "-o", "--only-files", action="store_true", help="list all files in manifest"
        )
        parser.add_argument(
            "-m",
            "--manifest-filename",
            type=Path,
            default=Path("./vendor_manifest.yaml"),
            help="write manifest to this file",
        )

    @staticmethod
    def print(environment_yml):
        conda_channel = CondaChannel(environment_yml)
        manifest_yaml = get_manifest(conda_channel)
        yaml.safe_dump(manifest_yaml, sys.stdout, sort_keys=False)

    @staticmethod
    def create(environment_yml, manifest_filename):
        conda_channel = CondaChannel(environment_yml)
        create_manifest(conda_channel, manifest_filename=manifest_filename)

    @staticmethod
    def list_files(environment_yml):
        conda_channel = CondaChannel(environment_yml)
        manifest_yaml = get_manifest(conda_channel)
        for resource in manifest_yaml["resources"]:
            print(resource["name"])

    def do_command(self, args, environment_yml):
        if args.dry_run:
            self.print(environment_yml)
        elif args.only_files:
            self.list_files(environment_yml)
        else:
            self.create(environment_yml, args.manifest_filename)


#  local_yaml commands
# keep
class CommandLocalYaml:
    def __init__(self, parent_parser, cmd_str):
        self.cmd_str = cmd_str
        parser = parent_parser.add_parser(cmd_str, help="local yaml commands")
        parser.add_argument(
            "--dry-run", action="store_true", help="print local environment.yaml"
        )
        parser.add_argument(
            "-f",
            "--file",
            type=Path,
            default=Path("./env.yaml"),
            help="environment.yaml file",
        )
        parser.add_argument("-n", "--name", type=str, help="local environment name")
        parser.add_argument(
            "-e", "--environment-file", type=str, help="local environment filename"
        )
        parser.add_argument(
            "--channel-root",
            type=Path,
            default=Path(),
            help="Parent path to local channel in local_yaml, useful if deployment path differs from channel creation",
        )

    @staticmethod
    def print(environment_yml, local_environment_name=None, channel_root=Path()):
        conda_channel = CondaChannel(environment_yml, channel_root=channel_root)
        local_yaml = get_local_environment_yaml(
            conda_channel, local_environment_name=local_environment_name
        )
        yaml.safe_dump(local_yaml, sys.stdout, sort_keys=False)

    @staticmethod
    def create(
        environment_yml,
        local_environment_name=None,
        local_environment_filename=None,
        channel_root=Path(),
    ):

        conda_channel = CondaChannel(environment_yml, channel_root=channel_root)
        create_local_environment_yaml(
            conda_channel,
            local_environment_name=local_environment_name,
            local_environment_filename=local_environment_filename,
        )

    def do_command(self, args):
        if args.dry_run:
            self.print(
                environment_yml=args.file,
                local_environment_name=args.name,
                channel_root=args.channel_root,
            )
        else:
            self.create(
                environment_yml=args.file,
                local_environment_name=args.name,
                local_environment_filename=args.environment_file,
                channel_root=args.channel_root,
            )


# local channels commands
class CommandLocalChannels:
    def __init__(self, parent_parser, cmd_str):
        self.cmd_str = cmd_str
        parser = parent_parser.add_parser(cmd_str, help="local channel commands")
        self.configure_parser(parser)

    @staticmethod
    def print(
        environment_yml,
        *,
        manifest_filename=None,
        local_environment_name=None,
        local_environment_filename=None,
        channel_root=None,
    ):
        print("not implemented")
        sys.exit(1)

    @staticmethod
    def create(
        environment_yml,
        *,
        manifest_filename=None,
        local_environment_name=None,
        local_environment_filename=None,
        channel_root=Path(),
        manifest_path=None,
    ):

        # TODO: problem with needing channel root to be included , this should be passed to the class type issue cant Path(None)
        # https://dusty.phillips.codes/2018/08/13/python-loading-pathlib-paths-with-argparse/
        conda_channel = CondaChannel(
            environment_yml, channel_root=channel_root, manifest_path=manifest_path
        )

        create_local_channels(
            conda_channel,
            manifest_filename=manifest_filename,
            local_environment_name=local_environment_name,
            local_environment_filename=local_environment_filename,
        )

    def configure_parser(self, parser):
        parser.add_argument(
            "--dry-run", action="store_true", help="local environment filename"
        )
        parser.add_argument(
            "-f",
            "--file",
            type=Path,
            default=Path("./env.yaml"),
            help="environment.yaml file",
        )
        parser.add_argument(
            "--channel-root",
            type=Path,
            default=Path(),
            help="create local directories here",
        )
        parser.add_argument(
            "-m", "--rename-manifest-file", type=str, help="write manifest to this file"
        )
        parser.add_argument("-n", "--name", type=str, help="local environment name")
        parser.add_argument(
            "-e", "--environment-file", type=str, help="local environment filename"
        )
        parser.add_argument(
            "-p",
            "--manifest-filepath",
            type=Path,
            default=Path("./vendor_manifest.yaml"),
            help="Full path to manifest file, skips inital solve",
        )

    def do_command(self, args):
        check_environment_yaml_or_manifest_yaml(args.file, args.manifest_filepath)
        if args.dry_run:
            self.print(
                args.file,
                manifest_filename=args.rename_manifest_file,
                local_environment_name=args.name,
                local_environment_filename=args.environment_file,
                channel_root=args.channel_root,
                manifest_path=args.manifest_filepath,
            )
        else:
            self.create(
                args.file,
                manifest_filename=args.rename_manifest_file,
                local_environment_name=args.name,
                local_environment_filename=args.environment_file,
                channel_root=args.channel_root,
                manifest_path=args.manifest_filepath,
            )


def check_environment_yaml_or_manifest_yaml(filename, manifest_filepath):

    fn_missing = not filename.exists()
    mfn_missing = not manifest_filepath.exists()

    if fn_missing and mfn_missing:
        sys.stderr.write(
            f"manifest_filepath exists :{manifest_filepath.exists()} filename exists :{filename.exists()} one of these files must exist!\n"
        )
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="conda-vendor creates a local conda environment"
    )
    sub_parsers = parser.add_subparsers(
        help="command options", dest="subcmd", required=False
    )

    sub_commands = {
        "manifest": CommandManifest(sub_parsers, "manifest"),
        "local_yaml": CommandLocalYaml(sub_parsers, "local_yaml"),
        "local_channels": CommandLocalChannels(sub_parsers, "local_channels"),
    }
    has_cmd = bool(set(sub_commands.keys()).intersection(set(sys.argv)))
    if not ("-h" in sys.argv or "--help" in sys.argv) and not has_cmd:
        sys.argv = [sys.argv[0], "local_channels"] + sys.argv[1:]

    args, rest = parser.parse_known_args()

    if args.subcmd in sub_commands:
        sub_commands[args.subcmd].do_command(args)
        return

    sys.stderr.write("an error occured.\n")
    sys.exit(1)


if __name__ == "__main__":
    main()
