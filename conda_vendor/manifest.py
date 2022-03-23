import collections
import hashlib
import json
import logging
import os
import struct
import sys
from pathlib import Path
from ruamel.yaml import YAML
import requests
from conda_lock.conda_solver import solve_specs_for_arch
from conda_lock.src_parser import VersionedDependency, Selectors
from conda_lock.src_parser.environment_yaml import parse_environment_file
from conda_lock.models.channel import Channel
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from typing import Sequence, List

logger = logging.getLogger(__name__)


class LockWrapper:
    @staticmethod
    def parse(*args):
        return parse_environment_file(*args)

    @staticmethod
    def solve(*args, **kwargs):
        return solve_specs_for_arch(*args, **kwargs)


# see https://github.com/conda/conda/blob/248741a843e8ce9283fa94e6e4ec9c2fafeb76fd/conda/base/context.py#L51
def get_conda_platform(
    platform=sys.platform,
    custom_platform=None,
):

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


class MetaManifest:
    def __init__(
        self,
        environment_yml,
        *,
        manifest_root=Path(),
        custom_platform=None,
    ):
        self.manifest_root = Path(manifest_root)
        logger.info(f"manifest_root : {self.manifest_root.absolute()}")
        self.platform = get_conda_platform(custom_platform=custom_platform)

        self.valid_platforms = [self.platform, "noarch"]

        # create from envirenment yaml
        self.manifest = None
        parse_return = LockWrapper.parse(environment_yml)

        self.env_deps = {
            "dependencies": parse_return.dependencies,
            "channels": parse_return.channels,
        }

        logger.info(f"Using Environment :{environment_yml}")
        
        bad_channels = [Channel(url='defaults')]
        self.channels = []
        for channel in self.env_deps["channels"]:
            if channel.url == bad_channels[0].url:
                raise RuntimeError("default channels are not supported.")
            else:
                self.channels.append(channel)

        self.add_pip_dependency()

    def add_pip_question_mark(self):
        """
        Adds Pip as a dependency of python is in the environment and the environment variable
        CONDA_ADD_PIP_AS_PYTHON_DEPENDENCY=False is not set
        """
        if os.environ.get("CONDA_ADD_PIP_AS_PYTHON_DEPENDENCY", None) == "False":
            add_pip_dependency = False
        else:
            add_pip_dependency = True

        return add_pip_dependency

    def add_pip_dependency(self):
        add_pip_dependency = self.add_pip_question_mark()
        
        if add_pip_dependency is True:
            for versioned_dependency in self.env_deps["dependencies"]:
                if versioned_dependency.name == 'python':
                    logger.info("python dependency found in dependencies, adding pip VersionedDependency")
                    pip_versioned_dep = VersionedDependency(
                            name='pip',
                            manager='conda',
                            optional=False,
                            category='main',
                            extras=[],
                            selectors=Selectors(platform=None),
                            version='22.*',
                            build=None)
                    self.env_deps["dependencies"].append(pip_versioned_dep)
                else:
                    logger.info("python not found in dependencies, skip adding pip VersionedDependency")

    def get_manifest_filename(self, manifest_filename=None):
        if manifest_filename is None:
            manifest_filename = "meta_manifest.yaml"
        return manifest_filename

    def create_manifest(self, *, manifest_filename=None):
        manifest = self.get_manifest()

        manifest_filename = self.get_manifest_filename(
            manifest_filename=manifest_filename
        )

        cleaned_name = Path(manifest_filename).name
        outpath_file_name = self.manifest_root / cleaned_name
        logger.info(f"Creating Manifest {outpath_file_name.absolute()}")
        with open(outpath_file_name, "w") as f:
            YAML().dump(
                manifest,
                f,
            )
        #import pprint
        #import yaml
        #pprint.pprint(yaml.dump(manifest))
        return manifest

    # this function is what actually generates the 'meta-manifest' output 
    # structure
    def get_manifest(self):
        if self.manifest is None:

            def nested_dict():
                return collections.defaultdict(nested_dict)

            d = nested_dict()

            #
            fetch_actions = self.solve_environment()
            
            dependencies = []
            #TODO: this needs more debugging...
            for dep in fetch_actions:
                # each entry in the results returned from solve_environment() has
                # the following structure:
                # {arch, build, build_number, channel, constraints, depends, fn,
                #  license, md5, name, platform, sha256, size, subdir, timestamp,
                #  url, version}

                # only add the fields that we need. Update this as needed 
                dependency_entry = {
                        "name": dep["name"],
                        "version": dep["version"],
                        "sha256": dep["sha256"],
                        "url": dep["url"]}
                dependencies.append(dependency_entry)

            manifest_structure = {"dependencies": dependencies}
            
            self.manifest = manifest_structure

        return self.manifest

    def get_purl(self, fetch_entry):
        """
        Returns package url format based on item in fetch data
        see: https://github.com/package-url/purl-spec
        """
        return f"pkg:conda/{fetch_entry['name']}@{fetch_entry['version']}?url={fetch_entry['url']}"

    # return FETCH actions only
    def solve_environment(self):
        if "solution" not in self.env_deps:
            logger.info(
                f"Solving ENV \nChannels : {self.env_deps['channels']} \nspecs : {self.env_deps['dependencies']} \nplatform : {self.platform}"
            )
            
            # specs List(str) to pass to conda-lock 
            specs = []

            for spec in self.env_deps["dependencies"]:
                specs.append(f"{spec.name}={spec.version}")
            solution = LockWrapper.solve(
                "conda",
                self.env_deps["channels"],
                specs=specs,
                platform=self.platform,
            )
        
            self.env_deps["solution"] = solution

        logger.debug(f'Fetch results: {self.env_deps["solution"]["actions"]["FETCH"]}')
        
        # returns [{arch, build, build_number, channel, constraints, depends, fn,
        #           license, md5, name, platform, sha256, size, subdir, timestamp,
        #           url, version}]
        return self.env_deps["solution"]["actions"]["FETCH"]


def combine_metamanifests(manifest_paths):
    manifests = read_manifests(manifest_paths)

    combined = {}
    for manifest in manifests:
        for channel in manifest.keys():
            if not channel in combined.keys():
                combined[channel] = manifest[channel]
            else:
                for arch in manifest[channel].keys():
                    if arch in combined[channel].keys():
                        pkg_list = deduplicate_pkg_list(
                            combined[channel][arch]["entries"]
                            + manifest[channel][arch]["entries"]
                        )
                        combined[channel][arch]["entries"] = pkg_list
                    else:
                        combined[channel][arch]["entries"] = manifest[channel][arch][
                            "entries"
                        ]
                        combined[channel][arch]["repodata_url"] = manifest[channel][
                            arch
                        ]["repodata_url"]
    return combined


def deduplicate_pkg_list(package_list):
    seen_shas = set()
    deduped_list = []

    for package in package_list:
        if package["sha256"] not in seen_shas:
            deduped_list.append(package)
            seen_shas.add(package["sha256"])

    return deduped_list


def read_manifests(manifest_paths):
    manifest_list = []
    for manifest_path in manifest_paths:
        with open(manifest_path, "r") as f:

            manifest_list.append(YAML(typ="safe").load(f))

    return manifest_list


def write_combined_manifest(manifest_path, combined_manifest):
    with open(manifest_path, "w") as f:

        YAML().dump(
            combined_manifest,
            f,
        )

