import collections
import hashlib
import json
import logging
import os
import struct
import sys
from pathlib import Path

import requests
import yaml
from conda_lock.conda_lock import solve_specs_for_arch
from conda_lock.src_parser.environment_yaml import parse_environment_file
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

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
    platform=sys.platform, custom_platform=None,
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
        self, environment_yml, *, manifest_root=Path(), custom_platform=None,
    ):
        self.manifest_root = Path(manifest_root)
        logger.info(f"manifest_root : {self.manifest_root.absolute()}")
        self.platform = get_conda_platform(custom_platform=custom_platform)

        self.valid_platforms = [self.platform, "noarch"]

        # create from envirenment yaml
        self.manifest = None
        parse_return = LockWrapper.parse(environment_yml, self.platform)

        self.env_deps = {
            "specs": parse_return.specs,
            "channels": parse_return.channels,
        }

        logger.info(f"Using Environment :{environment_yml}")
        with open(environment_yml) as f:
            self.env_deps["environment"] = yaml.load(f, Loader=yaml.SafeLoader)
        bad_channels = ["nodefaults"]
        self.channels = [
            chan
            for chan in self.env_deps["environment"]["channels"]
            if chan not in bad_channels
        ]
        if "defaults" in self.channels:
            raise RuntimeError("default channels are not supported.")

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
        dependencies = self.env_deps["environment"]["dependencies"].copy()
        has_python = "python" in "".join(dependencies)

        if add_pip_dependency is True and has_python:
            self.env_deps["environment"]["dependencies"].append("pip")

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
            yaml.dump(manifest, f, sort_keys=False)
        return manifest

    def get_manifest(self):
        if self.manifest is None:

            def nested_dict():
                return collections.defaultdict(nested_dict)

            d = nested_dict()

            fetch_actions = self.solve_environment()

            for chan in self.channels:  # edit to self.channels
                d[chan]["noarch"] = {"repodata_url": None, "entries": []}
                d[chan][self.platform] = {"repodata_url": None, "entries": []}

            for entry in fetch_actions:
                (channel, platform) = entry["channel"].split("/")[-2:]

                d[channel][platform][
                    "repodata_url"
                ] = f"{entry['channel']}/repodata.json"
                entry["purl"] = self.get_purl(entry)
                d[channel][platform]["entries"].append(entry)

            # Turns nested default dict into normal python dict
            self.manifest = json.loads(json.dumps(d))
        return self.manifest

    def get_purl(self, fetch_entry):
        """
        Returns package url format based on item in fetch data
        see: https://github.com/package-url/purl-spec
        """
        return f"pkg:conda/{fetch_entry['name']}@{fetch_entry['version']}?url={fetch_entry['url']}"

    def solve_environment(self):
        if "solution" not in self.env_deps:
            logger.info(
                f"Solving ENV \nChannels : {self.env_deps['channels']} \nspecs : {self.env_deps['specs']} \nplatform : {self.platform}"
            )
            solution = LockWrapper.solve(
                "conda",
                self.env_deps["channels"],
                specs=self.env_deps["specs"],
                platform=self.platform,
            )
            self.env_deps["solution"] = solution

        logger.debug(f'Fetch results: {self.env_deps["solution"]["actions"]["FETCH"]}')
        return self.env_deps["solution"]["actions"]["FETCH"]
