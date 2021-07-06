import argparse
import os
import pathlib
import sys
import yaml

import conda_vendor.core


#manifest commands
class CommandManifest:
    @staticmethod
    def print(environment_yml):
        manifest_yaml = conda_vendor.core.get_manifest(environment_yml)
        yaml.safe_dump(manifest_yaml, sys.stdout, sort_keys=False)

    @staticmethod
    def create(environment_yml, manifest_filename):
        conda_vendor.core.create_manifest(environment_yml,
                manifest_filename=manifest_filename)

    @staticmethod
    def list_files(environment_yml):
        manifest_yaml = conda_vendor.core.get_manifest(environment_yml)
        for resource in manifest_yaml['resources']:
            print(resource['name'])

    def __init__(self, parent_parser, cmd_str):
        self.cmd_str = cmd_str
        parser = parent_parser.add_parser(cmd_str,
            help='mainifest commands')
        parser.add_argument('-f', '--file', type=str,
            help='environment.yaml file')
        parser.add_argument('-p','--print', action='store_true',
            help='print manifest' )
        parser.add_argument('-c','--create', action='store_true',
            help='create manifest')
        parser.add_argument('-o', '--only-files', action='store_true',
            help='list all files in manifest')
        parser.add_argument('-m', '--manifest-filename', type=str,
            help='write manifest to this file')

    def do_command(self, args, environment_yml):
        if args.print:
            self.print(environment_yml)
        elif args.create:
            self.create(environment_yml, args.manifest_filename)
        elif args.only_files:
            self.list_files(environment_yml)
        else:
            #default subcommand just print
            self.print(environment_yml)


#  local_yaml commands
class CommandLocalYaml:
    @staticmethod
    def print(environment_yml, local_environment_name=None):
        local_yaml = conda_vendor.core.get_local_environment_yaml(environment_yml,
                local_environment_name=local_environment_name)
        yaml.safe_dump(local_yaml, sys.stdout, sort_keys=False)

    @staticmethod
    def create(environment_yml,
            local_environment_name=None,
            local_environment_filename=None):
        conda_vendor.core.create_local_environment_yaml(environment_yml,
                local_environment_name=local_environment_name,
                local_environment_filename=local_environment_filename)

    def __init__(self, parent_parser, cmd_str):
        self.cmd_str = cmd_str
        parser = parent_parser.add_parser(cmd_str,
            help='local yaml commands')
        parser.add_argument('-p','--print', action='store_true',
            help='print local environment.yaml' )
        parser.add_argument('-c','--create', action='store_true',
            help='create local environment.yaml')
        parser.add_argument('-f', '--file', type=str,
            help='environment.yaml file')
        parser.add_argument('-n', '--name', type=str,
            help='local environment name')
        parser.add_argument('-e', '--environment-file', type=str,
            help='local environment filename')

    def do_command(self, args, environment_yml):
        if args.print:
            self.print(environment_yml,
                    local_environment_name=args.name)
        elif args.create:
            self.create(environment_yml,
                    local_environment_name=args.name,
                    local_environment_filename=args.environment_file)
        else:
            self.print(environment_yml,
                    local_environment_name=args.name)


#local channels commands
class CommandLocalChannels:

    @staticmethod
    def create(environment_yml, *,
            manifest_filename=None,
            local_environment_name=None,
            local_environment_filename=None,
            local_directory=None):

        if not local_directory:
            conda_vendor.core.create_local_channels(environment_yml,
                    manifest_filename=manifest_filename,
                    local_environment_name=local_environment_name,
                    local_environment_filename=local_environment_filename)
        else:
            local_path = pathlib.Path(local_directory)
            l_dir, l_name = os.path.split(local_path.absolute())

            conda_channel = conda_vendor.core.CondaChannel(
                    platforms=['linux-64', 'noarch'],
                    channel_root=l_dir,
                    channel_name=l_name)

            conda_vendor.core.create_local_channels(environment_yml,
                    conda_channel = conda_channel,
                    manifest_filename=manifest_filename,
                    local_environment_name=local_environment_name,
                    local_environment_filename=local_environment_filename)


    def configure_parser(self, parser):
        parser.add_argument('-c', '--create', action='store_true',
            help='create local channel data')
#        parser.add_argument('--dry-run', action='store_true',
#            help='local environment filename')
        parser.add_argument('-f', '--file', type=str,
            help='environment.yaml file')
        parser.add_argument('-l', '--local-dir', type=str,
            help='create local directories here')
        parser.add_argument('-m', '--manifest-filename', type=str,
            help='write manifest to this file')
        parser.add_argument('-n', '--name', type=str,
            help='local environment name')
        parser.add_argument('-e', '--environment-file', type=str,
            help='local environment filename')

    def __init__(self, parent_parser, cmd_str):
        self.cmd_str = cmd_str
        parser = parent_parser.add_parser(cmd_str,
            help='local channel commands')
        self.configure_parser(parser)

    def do_command(self, args, environment_yml):
        self.create(environment_yml,
                manifest_filename=args.manifest_filename,
                local_environment_name=args.name,
                local_environment_filename=args.environment_file,
                local_directory=args.local_dir)

def main():
    parser = argparse.ArgumentParser(
            description='conda-vendor creates a local conda environment')
    sub_parsers = parser.add_subparsers(
        help='command options',
        dest='subcmd',
        required=False)

    sub_commands = {
            'manifest': CommandManifest(sub_parsers, 'manifest'),
            'local_yml': CommandLocalYaml(sub_parsers, 'local_yml'),
            'local_channels': CommandLocalChannels(sub_parsers, 'local_channels')
            }

    # main parser arguments are if no subcommand is specified
    # default to create local channels
    sub_commands['local_channels'].configure_parser(parser)

    args, rest = parser.parse_known_args()
    if not args.file:
        if not rest:
            sys.stderr.write('must supply environment.yml file.\n')
            sys.exit(1)
        elif rest[0]:
            args.file = rest[0]
        else:
            sys.stderr.write('must supply environment.yml file.\n')
            sys.exit(1)

    environment_yml = pathlib.Path(args.file)
    if not environment_yml.exists():
        sys.stderr.write(f'enviroment file \'{str(args.file)}\' does not exist\n')
        sys.exit(1)

    if args.subcmd in sub_commands:
        sub_commands[args.subcmd].do_command(args, environment_yml)
        return

    # no explicit subcommand - do local_channels
    sub_commands['local_channels'].do_command(args, environment_yml)
    return


if __name__ == '__main__':
    main()
