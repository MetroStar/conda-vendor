import argparse
import sys
import pathlib
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

    def add_command(self, parser):
        manifest_parser = parser.add_parser('manifest',
            help='mainifest commands')
        manifest_parser.add_argument('-f', '--file', type=str,
            help='environment.yaml file')
        manifest_parser.add_argument('-p','--print', action='store_true',
            help='print manifest' )
        manifest_parser.add_argument('-c','--create', action='store_true',
            help='create manifest')
        manifest_parser.add_argument('-o', '--only-files', action='store_true',
            help='list all files in manifest')
        manifest_parser.add_argument('-m', '--manifest-filename', type=str,
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

    def add_command(self, parser):
        local_yml_parser = parser.add_parser('local_yml',
            help='local yaml commands')
        local_yml_parser.add_argument('-p','--print', action='store_true',
            help='print local environment.yaml' )
        local_yml_parser.add_argument('-c','--create', action='store_true',
            help='create local environment.yaml')
        local_yml_parser.add_argument('-f', '--file', type=str,
            help='environment.yaml file')
        local_yml_parser.add_argument('-n', '--name', type=str,
            help='local environment name')
        local_yml_parser.add_argument('-e', '--environment-file', type=str,
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
            local_environment_filename=None):

        conda_vendor.core.create_local_channels(environment_yml,
                manifest_filename=manifest_filename,
                local_environment_name=local_environment_name,
                local_environment_filename=local_environment_filename)

    @staticmethod
    def dry_run(environment_yml, *,
            manifest_filename=None,
            local_environment_name=None,
            local_environment_filename=None):
        print('dry-run')

    def add_command(self, parser):
        local_channels_parser = parser.add_parser('local_channels',
            help='local channel commands')
        local_channels_parser.add_argument('-c', '--create', action='store_true',
            help='create local channel data')
        local_channels_parser.add_argument('--dry-run', action='store_true',
            help='local environment filename')
        local_channels_parser.add_argument('-f', '--file', type=str,
            help='environment.yaml file')
        local_channels_parser.add_argument('-m', '--manifest-filename', type=str,
             help='write manifest to this file')
        local_channels_parser.add_argument('-n', '--name', type=str,
            help='local environment name')
        local_channels_parser.add_argument('-e', '--environment-file', type=str,
            help='local environment filename')

    def do_command(self, args, environment_yml):
        if args.dry_run:
            self.dry_run(environment_yml,
                    manifest_filename=args.manifest_filename,
                    local_environment_name=args.name,
                    local_environment_filename=args.environment_file)
        else:
            self.create(environment_yml,
                    manifest_filename=args.manifest_filename,
                    local_environment_name=args.name,
                    local_environment_filename=args.environment_file)


def main():
    parser = argparse.ArgumentParser(
            description='conda-vendor creates a local conda environment')

    manifest = CommandManifest()
    local_yaml = CommandLocalYaml()
    local_channels = CommandLocalChannels()

    sub_parsers = parser.add_subparsers(
        help='some string',
        dest='subcmd')
    manifest.add_command(sub_parsers)
    local_yaml.add_command(sub_parsers)
    local_channels.add_command(sub_parsers)

    args, rest = parser.parse_known_args()
    print(f'args: {args}')
    print(f'rest: {rest}')
    print()

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

    if args.subcmd == 'manifest':
        manifest.do_command(args, environment_yml)
        return
    elif args.subcmd == 'local_yml':
        local_yaml.do_command(args, environment_yml)
        return
    elif args.subcmd == 'local_channels':
        local_channels.do_command(args, environment_yml)
        return

    print('no explicit subcommand')
    sys.exit(1)


if __name__ == '__main__':
    main()
