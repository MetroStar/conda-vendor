import hashlib
import json
import logging
import os
from pathlib import Path
import requests
import struct
import sys
import yaml
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from conda_lock.conda_lock import solve_specs_for_arch
from conda_lock.src_parser.environment_yaml import parse_environment_file


logging.basicConfig(level=logging.INFO)


class LockWrapper:
    @staticmethod
    def parse(*args):
        return parse_environment_file(*args)

    @staticmethod
    def solve(*args, **kwargs):
        return solve_specs_for_arch(*args, **kwargs)


# see https://stackoverflow.com/questions/21371809/cleanly-setting-max-retries-on-python-requests-get-or-post-method
def improved_download(url):
    session = requests.Session()
    retry = Retry(connect=5, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session.get(url)


# see https://github.com/conda/conda/blob/248741a843e8ce9283fa94e6e4ec9c2fafeb76fd/conda/base/context.py#L51
def get_conda_platform(platform=sys.platform):
    _platform_map = {
        "linux2": "linux",
        "linux": "linux",
        "darwin": "osx",
        "win32": "win",
        "zos": "zos",
    }

    bits = struct.calcsize("P") * 8
    return f"{_platform_map[platform]}-{bits}"


class CondaChannel:
    def __init__(self, environment_yml, *, channel_root=Path(), manifest_path=None):
        self.channel_root = Path(channel_root)
        logging.info(f"channel_root : {self.channel_root.absolute()}")
        self.platform = get_conda_platform()

        self.valid_platforms = [self.platform, "noarch"]
        if manifest_path is not None:
            # create channels from manifest
            logging.info(f"Using manifest :{manifest_path} ")
            self.manifest = self.load_manifest(manifest_path=manifest_path)

            environment_yaml = self.get_yaml_from_manifest(self.manifest)
            # TODO
            print("env", environment_yaml)
            self.env_deps = {
                "specs": environment_yaml["dependencies"],
                "channels": environment_yaml["channels"],
            }
            self.env_deps["environment"] = environment_yaml
            self.channels = environment_yaml["channels"]
        else:
            # create from envirenment yaml
            self.manifest = manifest_path
            parse_return = LockWrapper.parse(environment_yml, self.platform)
            self.env_deps = {
                "specs": parse_return.specs,
                "channels": parse_return.channels,
            }
            logging.info(f"Using Environment :{environment_yml}")
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

        self.extended_data = None
        self.all_repo_data = None

    def load_manifest(self, manifest_path):
        with open(manifest_path) as f:
            return yaml.load(f, Loader=yaml.SafeLoader)  # Need to double check this

    def get_package_entry(self, filename):
        name_pieces = filename.split("-")
        version_start = [s[0].isdigit() for s in name_pieces].index(True)

        pkg = "-".join(name_pieces[:version_start])
        ver = name_pieces[version_start]
        return "=".join([pkg, ver])

    def get_yaml_from_manifest(self, manifest: dict) -> dict:
        env_yaml = {"name": "conda_vendor_env", "channels": [], "dependencies": []}
        dep_list = []
        channel_list = []
        print("my_manifest", manifest)
        for entry in manifest["resources"]:
            print("entry", entry)
            channel_name, _, fn = entry["url"].split("/")[-3:]
            dep = self.get_package_entry(fn)

            channel_list.append(channel_name)
            dep_list.append(dep)

        env_yaml["channels"] = list(set(channel_list))
        env_yaml["dependencies"] = dep_list
        return env_yaml

    # this is run when not needed.
    def instantiate_conda_lock_fetch_from_manifest_file(self):
        # creates fetch if a manifest is present, but not when a fetch exists.
        if self.manifest is not None and "solution" not in self.env_deps.keys():
            fetch_data = []
            for entry in self.manifest["resources"]:
                url = entry["url"]
                channel, fn = os.path.split(url)
                sha256 = entry["validation"]["value"]

                temp = {}
                temp["url"] = url
                temp["channel"] = channel
                temp["fn"] = fn
                temp["sha256"] = sha256

                fetch_data.append(temp)
            self.env_deps["solution"] = {"actions": {"FETCH": fetch_data}}
            return {"actions": {"FETCH": fetch_data}}

    def solve_environment(self):
        # getting a manifest is dependent on this function having populated env_deps['solution']
        # we need this to not trigger if a manifest is already present

        self.instantiate_conda_lock_fetch_from_manifest_file()
        if not self.env_deps.get("solution", None):
            logging.info(
                f"Solving ENV | Channels : {self.env_deps['channels']} | specs : {self.env_deps['specs']} , platform : {self.platform}"
            )
            solution = LockWrapper.solve(
                "conda",
                self.env_deps["channels"],
                specs=self.env_deps["specs"],
                platform=self.platform,
            )
            self.env_deps["solution"] = solution
        return self.env_deps["solution"]["actions"]["FETCH"]

    def get_extended_data(self):
        # this is a data structure that stores info on where to get the
        # binaries and how to filter the upstream repodata.json.
        # we need this structure to filter the repodata
        if self.extended_data:
            return self.extended_data

        fetch_data = self.solve_environment()
        extended_data = {}
        # sets up repodata structure for each channel in the yaml
        for chan in self.channels:
            extended_data[chan] = {
                self.platform: {"repodata_url": [], "entries": []},
                "noarch": {"repodata_url": [], "entries": []},
            }
        # gets the channel url
        for entry in fetch_data:
            (channel, subdir) = entry["channel"].split("/")[-2:]
            extended_data[channel][subdir]["repodata_url"].append(
                entry["channel"] + "/repodata.json"
            )
            extended_data[channel][subdir]["entries"].append(entry)
        # gets the repodata url
        for chan in self.channels:
            for subdir in self.valid_platforms:
                extended_data[chan][subdir]["repodata_url"] = list(
                    set(extended_data[chan][subdir]["repodata_url"])
                )

        self.extended_data = extended_data
        return self.extended_data

    def get_manifest(self):
        if self.manifest:
            return self.manifest
        # unintended consequence
        fetch_actions = self.solve_environment()
        fetch_dict = {}
        for action in fetch_actions:
            action['purl'] = f"pkg:conda/{action['name']}@{action['version']}?url={action['url']}"
            fetch_dict[action['name']] = action
    
        self.manifest = fetch_dict
        return self.manifest

    def create_manifest(self, *, manifest_filename=None):
        # TODO: This will still create a manifest if creating from a manifest. Should probably be removed if creating from manifest.
        manifest = self.get_manifest()

        if not manifest_filename:
            manifest_filename = "vendor_manifest.yaml"

        cleaned_name = Path(manifest_filename).name
        outpath_file_name = self.channel_root / cleaned_name
        logging.info(f"Creating Manifest {outpath_file_name.absolute()}")
        with open(outpath_file_name, "w") as f:
            yaml.dump(manifest, f, sort_keys=False) 
        return manifest

    def get_local_environment_yaml(
        self, *, local_environment_name=None, destination_channel_root=None
    ):

        local_yml = self.env_deps["environment"].copy()
        if not local_environment_name:
            local_environment_name = f"local_{local_yml['name']}"
        local_yml["name"] = local_environment_name
        channel_paths = []

        yaml_channel_basepath = self.get_yaml_channel_basepath(destination_channel_root)

        for chan in self.channels:
            local_chan = yaml_channel_basepath / self.local_channel_name(chan)
            channel_paths.append(f"file://{local_chan.absolute()}")
        channel_paths.append("nodefaults")

        local_yml["channels"] = channel_paths
        return local_yml

    def get_yaml_channel_basepath(self, destination_channel_root=None):
        if destination_channel_root is not None:
            return destination_channel_root
        else:
            return self.channel_root

    def create_local_environment_yaml(
        self, *, local_environment_name=None, local_environment_filename=None
    ):
        local_yml = self.get_local_environment_yaml(
            local_environment_name=local_environment_name
        )

        if not local_environment_filename:
            local_environment_filename = "local_yaml.yaml"

        cleaned_name = Path(local_environment_filename).name
        outpath_file_name = self.channel_root / cleaned_name
        logging.info(f"Creating local_env_yaml :  {outpath_file_name.absolute()} ")
        with open(outpath_file_name, "w") as f:
            yaml.safe_dump(local_yml, f, sort_keys=False)
        return local_yml

    def fetch_and_filter(self, subdir, extended_repo_data):
        # returns a channel specific repodata.json
        repo_data = {"info": {"subdir": subdir}, "packages": {}, "packages.conda": {}}

        if not extended_repo_data["repodata_url"]:
            return repo_data

        valid_names = [entry["fn"] for entry in extended_repo_data["entries"]]

        repo_data_url = extended_repo_data["repodata_url"][0]
        logging.info(f"fetching repo data from :{repo_data_url} to subdir : {subdir}")
        live_repo_data_json = improved_download(repo_data_url).json()
        if live_repo_data_json.get("packages"):
            for name, entry in live_repo_data_json["packages"].items():
                if name in valid_names:
                    repo_data["packages"][name] = entry

        if live_repo_data_json.get("packages.conda"):
            for name, entry in live_repo_data_json["packages.conda"].items():
                if name in valid_names:
                    repo_data["packages.conda"][name] = entry

        return repo_data

    def get_all_repo_data(self):
        if self.all_repo_data:
            return self.all_repo_data
        # this is where
        extended_data = self.get_extended_data()
        all_repo_data = {}
        for chan in self.channels:
            all_repo_data[chan] = {
                self.platform: self.fetch_and_filter(
                    self.platform, extended_data[chan][self.platform]
                ),
                "noarch": self.fetch_and_filter(
                    "noarch", extended_data[chan]["noarch"]
                ),
            }
        self.all_repo_data = all_repo_data
        return self.all_repo_data

    def local_channel_name(self, chan: str):
        return "local_" + chan

    def local_dir(self, chan, subdir):
        chan_name = self.local_channel_name(chan)
        return self.channel_root / chan_name / subdir

    def make_local_dir(self, chan, subdir):
        dest_dir = self.local_dir(chan, subdir)
        dest_dir.mkdir(parents=True, exist_ok=True)
        logging.info(f"Making directory {dest_dir.absolute()} ")
        return dest_dir

    def write_arch_repo_data(self, chan, subdir, repo_data):
        dest_dir = self.make_local_dir(chan, subdir)
        dest_file = dest_dir / "repodata.json"
        with dest_file.open("w") as f:
            json.dump(repo_data, f)

    def write_repo_data(self):
        all_repo_data = self.get_all_repo_data()
        for chan, platform in all_repo_data.items():
            for subdir, repo_data in platform.items():
                self.write_arch_repo_data(chan, subdir, repo_data)

    @staticmethod
    def _calc_sha256(byte_array):
        return hashlib.sha256(byte_array).hexdigest()

    @staticmethod
    def download_and_validate(out: Path, url, sha256):
        logging.info(f"downloading {url} to {out}")
        response = improved_download(url)
        url_data = response.content
        with open(out, "wb") as f:
            f.write(url_data)

            calculated_sha = CondaChannel._calc_sha256(url_data)
            if sha256 != calculated_sha:
                raise RuntimeError(
                    f"SHA256 does not match for {out} calculated SHA: {calculated_sha}, "
                    f"manifest SHA: {sha256}"
                )

    def download_arch_binaries(self, chan, subdir, entries):
        dest_dir = self.make_local_dir(chan, subdir)
        for entry in entries:
            self.download_and_validate(
                dest_dir / entry["fn"], entry["url"], entry["sha256"]
            )

    def download_binaries(self):
        extended_data = self.get_extended_data()
        for chan, platform in extended_data.items():
            for subdir, rest in platform.items():
                self.download_arch_binaries(chan, subdir, rest["entries"])


def get_manifest(conda_channel: CondaChannel):
    return conda_channel.get_manifest()


def create_manifest(conda_channel: CondaChannel, *, manifest_filename=None):
    return conda_channel.create_manifest(manifest_filename=manifest_filename)


def get_local_environment_yaml(
    conda_channel: CondaChannel, *, local_environment_name=None
):
    return conda_channel.get_local_environment_yaml(
        local_environment_name=local_environment_name
    )


def create_local_environment_yaml(
    conda_channel: CondaChannel,
    *,
    local_environment_name=None,
    local_environment_filename=None,
):
    local_yaml = conda_channel.create_local_environment_yaml(
        local_environment_name=local_environment_name,
        local_environment_filename=local_environment_filename,
    )
    return local_yaml


# change to more comprehensive name
def create_local_channels(
    conda_channel: CondaChannel,
    *,
    manifest_filename=None,
    local_environment_name=None,
    local_environment_filename=None,
):
    conda_channel.create_manifest(manifest_filename=manifest_filename)

    conda_channel.create_local_environment_yaml(
        local_environment_name=local_environment_name,
        local_environment_filename=local_environment_filename,
    )
    # calls solve unintentionally re-writes the fetch when it doesnt need to.
    conda_channel.write_repo_data()
    conda_channel.download_binaries()
