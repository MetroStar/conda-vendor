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

# see https://stackoverflow.com/questions/21371809/cleanly-setting-max-retries-on-python-requests-get-or-post-method
def improved_download(url):
    session = requests.Session()
    retry = Retry(connect=5, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session.get(url)


class CondaChannel:
    def __init__(self, *, channel_root=Path(), meta_manifest_path=None):

        self.channel_root = Path(channel_root)
        logger.info(f"channel_root : {self.channel_root.absolute()}")
        self.meta_manifest = self.load_manifest(meta_manifest_path)
        self.channels = list(self.meta_manifest.keys())
        self.all_repo_data = None
        self.platform = self.get_platform_from_manifest()

    def load_manifest(self, manifest_path):
        with open(manifest_path) as f:
            return yaml.load(f, Loader=yaml.SafeLoader)

    def fetch_and_filter_repodata(self, conda_subdir, manifest_subset_metadata):
        # returns a channel specific repodata.json
        repo_data = {
            "info": {"subdir": conda_subdir},
            "packages": {},
            "packages.conda": {},
        }
        if manifest_subset_metadata["repodata_url"] == None:
            return repo_data

        valid_names = [entry["fn"] for entry in manifest_subset_metadata["entries"]]

        repo_data_url = manifest_subset_metadata["repodata_url"]
        logger.info(
            f"fetching repo data from :{repo_data_url} to subdir : {conda_subdir}"
        )
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

    def get_platform_from_manifest(self):

        first_channel = self.channels[0]
        platforms = set(self.meta_manifest[first_channel].keys())
        current_platform = set(platforms) - {"noarch"}
        return current_platform.pop()

    def get_all_repo_data(self):
        if self.all_repo_data:
            return self.all_repo_data
        # this is where
        all_repo_data = {}

        for chan in self.channels:
            all_repo_data[chan] = {
                self.platform: self.fetch_and_filter_repodata(
                    self.platform, self.meta_manifest[chan][self.platform]
                ),
                "noarch": self.fetch_and_filter_repodata(
                    "noarch", self.meta_manifest[chan]["noarch"]
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
        logger.info(f"Making directory {dest_dir.absolute()} ")
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
        logger.debug(f"downloading {url} to {out}")
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
        logger.info(
            "Creating directories and downloading packages locally. This may take a few minutes."
        )

        for chan, platform in self.meta_manifest.items():
            for conda_subdir, rest in platform.items():
                self.download_arch_binaries(chan, conda_subdir, rest["entries"])
