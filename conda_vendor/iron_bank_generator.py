# this generates formatted text to insert into the DoD IronBank's 
# hardening_manifest.yaml "resources" block
import click
import sys
from ruamel.yaml import YAML

# dump ironbank resources yaml block to stdout
def yaml_dump_ironbank_manifest(fetch_action_packages):
    click.echo(click.style("You can copy this text below to your IronBank Hardening Manifest", bold=True, fg='cyan'))
    # IronBank formatted 'resources' block
    resources = {
        "resources": [],
    }
    
    for pkg in fetch_action_packages:
        validation = {
            "type": "sha256",
            "value": pkg["sha256"]
        }
        resource = {
            "url": pkg["url"],
            "filename": pkg["fn"],
            "validation": validation
        }

        resources["resources"].append(resource)
    yaml = YAML()
    with open("ib_manifest.yaml", 'w') as f:
        ironbank_resources = yaml.dump(resources, f)
