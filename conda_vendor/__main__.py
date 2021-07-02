import argparse
import sys
import pathlib
import yaml

import conda_vendor.core

#manifest commands
def manifest_print(environment_yml):
    #print(conda_vendor.core.get_manifest(environment_yml))
    manifest_yaml = conda_vendor.core.get_manifest(environment_yml)
    yaml.safe_dump(manifest_yaml, sys.stdout, sort_keys=False)

def manifest_create(environment_yml):
    conda_vendor.core.create_manifest(environment_yml)

def manifest_list_files(environment_yml):
    manifest_yaml = conda_vendor.core.get_manifest(environment_yml)
    for resource in manifest_yaml["resources"]:
        print(resource['name'])


#  local_yaml commands
def local_yaml_print(environment_yml):
    local_yaml = conda_vendor.core.get_local_environment_yaml(environment_yml)
    yaml.safe_dump(local_yaml, sys.stdout, sort_keys=False)

def local_yaml_create(environment_yml):
    conda_vendor.core.create_local_environment_yaml(environment_yml)


#local channels commands
def local_channels_create(environment_yml):
    conda_vendor.core.create_local_channels(environment_yml)


def main():
    parser = argparse.ArgumentParser(description="text here")
    parser.add_argument("-f", "--file", type=str, 
        help="environment.yaml file")

    sub_parsers = parser.add_subparsers(help='some string', dest='subcmd')
    
    manifest_parser = sub_parsers.add_parser('manifest', 
        help='mainifest commands')
    manifest_parser.add_argument('-p','--print', action='store_true',
        help="print manifest" )
    manifest_parser.add_argument('-c','--create', action='store_true',
        help="create manifest")
    manifest_parser.add_argument('-o','--only-files', action='store_true',
        help='list all files in manifest')
    #TODO: create subparser to name local env yaml
    local_yml_parser = sub_parsers.add_parser('local_yml', 
        help='local yaml commands')
    local_yml_parser.add_argument('-p','--print', action='store_true',
        help="print local environment.yaml" )
    local_yml_parser.add_argument('-c','--create', action='store_true',
        help="create local environment.yaml")


    local_channels_parser = sub_parsers.add_parser('local_channels',
        help='local channel commands')
    local_channels_parser.add_argument('-c', '--create', action='store_true',
        help='create local channel data')


    args = parser.parse_args()

    if not args.file:
        sys.stderr.write('must supply yml file.')
        sys.exit(1)

    environment_yml = pathlib.Path(args.file)
    if not environment_yml.exists():
        sys.stderr.write('enviroment file does not exist')
        sys.exit(1)

    print(args)

    if args.subcmd == 'manifest':
        if args.print:
            manifest_print(environment_yml)
        elif args.create:
            manifest_create(environment_yml)
        elif args.only_files:
            manifest_list_files(environment_yml)
        else:
            #default subcommand just print
            manifest_print(environment_yml)
        return

    elif args.subcmd == 'local_yml':
        if args.print:
            local_yaml_print(environment_yml)
        elif args.create:
            local_yaml_create(environment_yml)
        else:
            local_yaml_print(environment_yml)
        return

    elif args.subcmd == 'local_channels':
        local_channels_create(environment_yml)

    else:
        print('unrecognized commad')
        sys.exit(1)



if __name__ == '__main__':
    main()