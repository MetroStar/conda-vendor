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
        # I dont think we need this
        # self.valid_platforms = [self.platform, "noarch"]
    
        
        # create from envirenment yaml
        self.manifest = self.load_manifest(manifest_path)
        self.channels = self.manifest.keys()
        
        parse_return = LockWrapper.parse(environment_yml, self.platform)

        self.all_repo_data = None
    #keep
    def load_manifest(self, manifest_path):
        with open(manifest_path) as f:
            return yaml.load(f, Loader=yaml.SafeLoader)  # Need to double check this

    def get_package_entry(self, filename):
        name_pieces = filename.split("-")
        version_start = [s[0].isdigit() for s in name_pieces].index(True)

        pkg = "-".join(name_pieces[:version_start])
        ver = name_pieces[version_start]
        return "=".join([pkg, ver]) 

    def fetch_and_filter(self, subdir, meta_manifest):
        # returns a channel specific repodata.json
        repo_data = {"info": {"subdir": subdir}, "packages": {}, "packages.conda": {}}

        if meta_manifest["repodata_url"] == []:
            return repo_data

        valid_names = [entry["fn"] for entry in meta_manifest["entries"]]

        repo_data_url = meta_manifest["repodata_url"][0]
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
        all_repo_data = {}
        for chan in self.channels:
            all_repo_data[chan] = {
                self.platform: self.fetch_and_filter(
                    self.platform, self.manifest[chan][self.platform]
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









