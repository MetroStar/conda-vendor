import argparse
import functools
import os
import pathlib
import sys
import yaml

# TODO:
#   needs better user experience

# TODO:
# do this better
''' Switch the comments on the following lines
    to build the conda-vendor wheel
'''
# from conda_vendor.core import (
from core import (
    get_manifest,
    create_manifest,
    get_local_environment_yaml,
    create_local_environment_yaml,
    create_local_channels,
    CondaChannel,
)

# manifest commands
class CommandManifest:
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

    def __init__(self, parent_parser, cmd_str):
        self.cmd_str = cmd_str
        parser = parent_parser.add_parser(cmd_str, help="mainifest commands")
        parser.add_argument("-f", "--file", type=str, help="environment.yaml file")
        parser.add_argument("--dry-run", action="store_true", help="print manifest")
        parser.add_argument(
            "-o", "--only-files", action="store_true", help="list all files in manifest"
        )
        parser.add_argument(
            "-m", "--manifest-filename", type=str, help="write manifest to this file"
        )

    def do_command(self, args, environment_yml):
        if args.dry_run:
            self.print(environment_yml)
        elif args.only_files:
            self.list_files(environment_yml)
        else:
            self.create(environment_yml, args.manifest_filename)


#  local_yaml commands
class CommandLocalYaml:
    @staticmethod
    def print(environment_yml, local_environment_name=None):
        conda_channel = CondaChannel(environment_yml)
        local_yaml = get_local_environment_yaml(
            conda_channel, local_environment_name=local_environment_name
        )
        yaml.safe_dump(local_yaml, sys.stdout, sort_keys=False)

    @staticmethod
    def create(
        environment_yml, local_environment_name=None, local_environment_filename=None
    ):

        conda_channel = CondaChannel(environment_yml)
        create_local_environment_yaml(
            conda_channel,
            local_environment_name=local_environment_name,
            local_environment_filename=local_environment_filename,
        )

    def __init__(self, parent_parser, cmd_str):
        self.cmd_str = cmd_str
        parser = parent_parser.add_parser(cmd_str, help="local yaml commands")
        parser.add_argument(
            "--dry-run", action="store_true", help="print local environment.yaml"
        )
        parser.add_argument("-f", "--file", type=str, help="environment.yaml file")
        parser.add_argument("-n", "--name", type=str, help="local environment name")
        parser.add_argument(
            "-e", "--environment-file", type=str, help="local environment filename"
        )

    def do_command(self, args, environment_yml):
        if args.dry_run:
            self.print(environment_yml, local_environment_name=args.name)
        else:
            self.create(
                environment_yml,
                local_environment_name=args.name,
                local_environment_filename=args.environment_file,
            )


# local channels commands
class CommandLocalChannels:
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
        channel_root=None,
    ):

        if not channel_root:
            conda_channel = CondaChannel(environment_yml)
        else:
            conda_channel = CondaChannel(environment_yml, channel_root=channel_root)

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
        parser.add_argument("-f", "--file", type=str, help="environment.yaml file")
        parser.add_argument(
            "--channel-root", type=str, help="create local directories here"
        )
        parser.add_argument(
            "-m", "--manifest-filename", type=str, help="write manifest to this file"
        )
        parser.add_argument("-n", "--name", type=str, help="local environment name")
        parser.add_argument(
            "-e", "--environment-file", type=str, help="local environment filename"
        )

    def __init__(self, parent_parser, cmd_str):
        self.cmd_str = cmd_str
        parser = parent_parser.add_parser(cmd_str, help="local channel commands")
        self.configure_parser(parser)

    def do_command(self, args, environment_yml):
        if args.dry_run:
            self.print(
                environment_yml,
                manifest_filename=args.manifest_filename,
                local_environment_name=args.name,
                local_environment_filename=args.environment_file,
                channel_root=args.channel_root,
            )
        else:
            self.create(
                environment_yml,
                manifest_filename=args.manifest_filename,
                local_environment_name=args.name,
                local_environment_filename=args.environment_file,
                channel_root=args.channel_root,
            )


def check_environment_yaml(filename: None):
    if not filename:
        sys.stderr.write("must supply environment.yml file.\n")
        sys.exit(1)

    environment_yml = pathlib.Path(filename)
    if not environment_yml.exists():
        sys.stderr.write(f"enviroment file '{str(filename)}' does not exist\n")
        sys.exit(1)

    return environment_yml


def cook_argv_for_default(sub_commands, default):
    cmd_match = list(map(lambda x: int(x in sub_commands), sys.argv))
    has_command = bool(functools.reduce(lambda a, b: a + b, cmd_match))
    if not has_command:
        sys.argv = [sys.argv[0], default] + sys.argv[1:]


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

    if not ("-h" in sys.argv or "--help" in sys.argv):
        cook_argv_for_default(list(sub_commands.keys()), "local_channels")

    args, rest = parser.parse_known_args()
    environment_yml = check_environment_yaml(args.file)
    if args.subcmd in sub_commands:
        sub_commands[args.subcmd].do_command(args, environment_yml)
        return

    sys.stderr.write("an error occured.\n")
    sys.exit(1)


if __name__ == "__main__":
    main()
