import click
import yaml
from conda_vendor.version import __version__
from conda_vendor.conda_lock_wrapper import CondaLockWrapper
from conda_lock.src_parser import LockSpecification
from pathlib import Path
from typing import List

def get_lock_spec_for_environment_file(environment_file) -> LockSpecification:

    lock_spec = CondaLockWrapper.parse_environment_file(environment_file)
    return lock_spec

def solve_environment(lock_spec, solver, platform):
    specs = get_specs(lock_spec)
    
    click.echo(f"Solving for Platform: {platform}")
    click.echo(f"Solving for Spec: {specs}")
    
    solve = CondaLockWrapper.solve_specs_for_arch(
            solver,
            lock_spec.channels,
            specs,
            platform)

    #print(solve)

def get_specs(lock_spec) -> List:
    versioned_deps = lock_spec.dependencies
    specs = []
    for dep in versioned_deps:
        if dep.version == '':
            specs.append(f"{dep.name}")
        else:
            specs.append(f"{dep.name}=={dep.version}")
    return specs

@click.group()
@click.version_option(__version__)
def main() -> None:
    """Display help and usage for subcommands, use: conda-vendor [COMMAND] --help"""
    pass

@click.command("vendor", help="Vendor a local channel given an environment file")
@click.option(
    "--file",
    default=None, 
    help="Path to environment.yaml or conda-lock.yaml")
@click.option(
    "--solver",
    default="conda",
    help="Solver to use. conda, mamba, micromamba")
@click.option(
    "--platform",
    "-p",
    default="linux-64", # TODO: add in fn to solve platform
    help="Platform to solve for.")
def vendor(file,solver, platform):

    click.echo(f"Vendoring Local Channel for {file}")
    
    # handle environment.yaml
    environment_yaml = Path(file)
    lock_spec = get_lock_spec_for_environment_file(environment_yaml)
    
    #click.echo(lock_spec)
    solve_environment(lock_spec, solver, platform)



main.add_command(vendor)

if __name__ == "main":
    main()
