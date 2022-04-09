import click
import yaml
import sys
import struct
import os
from conda_vendor.version import __version__
from conda_vendor.conda_lock_wrapper import CondaLockWrapper
from conda_lock.src_parser import LockSpecification
from conda_lock.conda_solver import DryRunInstall, VersionedDependency, FetchAction
from pathlib import Path
from typing import List

def get_lock_spec_for_environment_file(environment_file) -> LockSpecification:
    lock_spec = CondaLockWrapper.parse_environment_file(environment_file)
    return lock_spec


# create the vendored channel directory, given the name in the environment.yaml
def create_vendored_dir(environment_file, platform, desired_path=None):
    with open(environment_file, 'r') as env_file:
        try:
            environment_yaml = yaml.safe_load(env_file)
            environment_name = environment_yaml['name']
        except yaml.YAMLError as err:
            click.echo(err)
            sys.exit(f"Failed to read environment name from {environment_file}")
    
    # use current working directory if no path specified
    if desired_path == None:
        try:
            path = os.path.join(os.getcwd(), environment_name)
            os.mkdir(path)
            create_platform_dir(path, platform)
            create_noarch_dir(path)
        except FileExistsError as err:
            click.echo(err)
            sys.exit(f"Directory \"{environment_name}\" already exists")

def create_platform_dir(path, platform):
    try:
        platform_path = os.path.join(path, platform)
        os.mkdir(platform_path)
    except FileExistsError as err:
        click.echo(err)
        sys.exit(f"Directory \"{platform_path}\" already exists")

def create_noarch_dir(path):
    try:
        noarch_path = os.path.join(path, 'noarch')
        os.mkdir(noarch_path)
    except FileExistsError as err:
        click.echo(err)
        sys.exit(f"Directory \"{noarch_path}\" already exists")
   

def solve_environment(lock_spec, solver, platform) -> DryRunInstall:
    specs = get_specs(lock_spec)
    
    click.echo(f"Using Solver: {solver}")
    click.echo(f"Solving for Platform: {platform}")
    click.echo(f"Solving for Spec: {specs}")
    
    dry_run_install = CondaLockWrapper.solve_specs_for_arch(
            solver,
            lock_spec.channels,
            specs,
            platform)

    if not dry_run_install['success']:
        sys.exit("Failed to Solve for {specs}\n Using {solver} for {platform}")

    click.echo("Successfull Solve")

    return dry_run_install

# get formatted List(str) to pass to CondaLockWrapper.solve_specs_for_arch()
def get_specs(lock_spec) -> List:
    versioned_deps = lock_spec.dependencies
    specs = []
    for dep in versioned_deps:
        if dep.version == '':
            specs.append(f"{dep.name}")
        else:
            specs.append(f"{dep.name}=={dep.version}")
    return specs

# Only return packages in the FETCH action, which
# include all the entries form the packages repodata.json
def get_fetch_actions(dry_run_install) -> FetchAction: 
    fetch_actions = dry_run_install["actions"]["FETCH"]
    return fetch_actions


#see https://github.com/conda/conda/blob/248741a843e8ce9283fa94e6e4ec9c2fafeb76fd/conda/base/context.py#L51
def get_conda_platform(
    platform=sys.platform,
    custom_platform=None,
    ) -> str:

    if custom_platform is not None:
        return custom_platform

    _platform_map = {
        "linux2": "linux",
        "linux": "linux",
        "darwin": "osx",
        "win32": "win",
        "zos": "zos",
    }

    bits = struct.calcsize("P") * 8
    return f"{_platform_map[platform]}-{bits}"

@click.group()
@click.version_option(__version__)
def main() -> None:
    """Display help and usage for subcommands, use: conda-vendor [COMMAND] --help"""
    pass

@click.command("vendor", help="Vendor a local channel given an environment file")
@click.option(
    "--file",
    default=None, 
    help="Path to environment.yaml")
@click.option(
    "--solver",
    default="conda",
    help="Solver to use. conda, mamba, micromamba")
@click.option(
    "--platform",
    "-p",
    default=get_conda_platform(),
    help="Platform to solve for.")
def vendor(file,solver, platform):

    click.echo(f"Vendoring Local Channel for {file}")
    
    # handle environment.yaml
    environment_yaml = Path(file)
    create_vendored_dir(environment_yaml, platform)

    lock_spec = get_lock_spec_for_environment_file(environment_yaml)
    

    dry_run_install = solve_environment(lock_spec, solver, platform)
    
    fetch_action_packages = get_fetch_actions(dry_run_install)


main.add_command(vendor)

if __name__ == "main":
    main()
