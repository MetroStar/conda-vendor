import hashlib
import json
import logging
import pathlib
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
    def __init__(
        self,
        environment_yml,
        *,
        channel_root=pathlib.Path("./"),
    ):
        self.platform = get_conda_platform()
        parse_return = LockWrapper.parse(environment_yml, self.platform)
        self.env_deps = {"specs": parse_return.specs, "channels": parse_return.channels}
        with open(environment_yml) as f:
            self.env_deps["environment"] = yaml.load(f, Loader=yaml.SafeLoader)

        self.valid_platforms = [self.platform, "noarch"]

        bad_channels = ["nodefaults"]
        self.channels = [
            chan
            for chan in self.env_deps["environment"]["channels"]
            if chan not in bad_channels
        ]

        if "defaults" in self.channels:
            raise RuntimeError("default channels are not supported.")

        self.manifest = None
        self.extended_data = None
        self.all_repo_data = None
        self.channel_root = pathlib.Path(channel_root)
        logging.info(f"channel_root : {self.channel_root.absolute()}")

    def solve_environment(self):
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
        if self.extended_data:
            return self.extended_data

        fetch_data = self.solve_environment()
        extended_data = {}

        for chan in self.channels:
            extended_data[chan] = {
                self.platform: {"repodata_url": [], "entries": []},
                "noarch": {"repodata_url": [], "entries": []},
            }

        for entry in fetch_data:
            (channel, subdir) = entry["channel"].split("/")[-2:]
            extended_data[channel][subdir]["repodata_url"].append(
                entry["channel"] + "/repodata.json"
            )
            extended_data[channel][subdir]["entries"].append(entry)

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

        fetch_actions = self.solve_environment()
        vendor_manifest_list = []
        for conda_lock_fetch_info in fetch_actions:
            url = conda_lock_fetch_info["url"]
            name = conda_lock_fetch_info["fn"]
            validation_value = conda_lock_fetch_info["sha256"]
            validation = {"type": "sha256", "value": validation_value}
            vendor_manifest_list.append(
                {"url": url, "name": name, "validation": validation}
            )
        self.manifest = {"resources": vendor_manifest_list}
        return self.manifest

    def create_manifest(self, *, manifest_filename=None):
        manifest = self.get_manifest()

        if not manifest_filename:
            manifest_filename = "vendor_manifest.yaml"

        cleaned_name = pathlib.PurePath(manifest_filename).name
        outpath_file_name = self.channel_root / cleaned_name
        logging.info(f"Creating Manifest {outpath_file_name.absolute()}")
        with open(outpath_file_name, "w") as f:
            yaml.dump(manifest, f, sort_keys=False)
        return manifest

    def get_local_environment_yaml(self, *, local_environment_name=None):

        local_yml = self.env_deps["environment"].copy()
        if not local_environment_name:
            local_environment_name = f"local_{local_yml['name']}"
        local_yml["name"] = local_environment_name
        channel_paths = []
        for chan in self.channels:
            local_chan = self.channel_root / self.local_channel_name(chan)
            channel_paths.append(f"file://{local_chan.absolute()}")
        channel_paths.append("nodefaults")

        local_yml["channels"] = channel_paths
        return local_yml

    def create_local_environment_yaml(
        self, *, local_environment_name=None, local_environment_filename=None
    ):
        local_yml = self.get_local_environment_yaml(
            local_environment_name=local_environment_name
        )

        if not local_environment_filename:
            local_environment_filename = "local_yaml.yaml"

        cleaned_name = pathlib.PurePath(local_environment_filename).name
        outpath_file_name = self.channel_root / cleaned_name
        logging.info(f"Creating local_env_yaml :  {outpath_file_name.absolute()} ")
        with open(outpath_file_name, "w") as f:
            yaml.safe_dump(local_yml, f, sort_keys=False)
        return local_yml

    def fetch_and_filter(self, subdir, extended_repo_data):

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
    def download_and_validate(out: pathlib.Path, url, sha256):
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
    conda_channel.write_repo_data()
    conda_channel.download_binaries()
