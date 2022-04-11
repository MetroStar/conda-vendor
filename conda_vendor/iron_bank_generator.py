# this generates formatted text to insert into the DoD IronBank's 
# hardening_manifest.yaml "resources" block
import click

def pretty_print_ironbank_manifest(fetch_action_packages):

    #TODO: formatted YAML

    click.echo(click.style(fetch_action_packages, fg='yellow'))
