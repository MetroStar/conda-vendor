import json
import subprocess
import pathlib
import requests
import yaml
import hashlib
import sys
from conda_lock.conda_lock import solve_specs_for_arch
from conda_lock.src_parser.environment_yaml import parse_environment_file


class CondaLockWrapper:
    def __init__(self, platform="linux-64"):
        self.platform = platform

    def parse(self, environment_yml):
        lock_specs = parse_environment_file(environment_yml, self.platform)
        return lock_specs.specs

    def solve(self, specs):
        solved_env = solve_specs_for_arch(
            "conda", ["main"], specs=specs, platform="linux-64"
        )

        link_actions = solved_env["actions"]["LINK"]
        return link_actions

    def solution_from_environment(self, environment_yml):
        return self.solve(self.parse(environment_yml))


class CondaChannel:
    def __init__(
        self, platforms=["linux-64", "noarch"], channel_path=pathlib.Path("./")
    ):
        self.base_url = "https://repo.anaconda.com/pkgs/main/"
        self.platforms = platforms
        self._repodata_dict = None
        self.channel_root = pathlib.Path(channel_path)
        self.local_channel = self.channel_root / "local_channel"
        self.channel_info = {}
        for platform in platforms:
            self.channel_info[platform] = {
                "dir": self.local_channel / platform,
                "url": self.base_url + platform + "/repodata.json",
            }

    def create_directories(self):
        self.local_channel.mkdir(exist_ok=True)
        for platform, info in self.channel_info.items():
            info["dir"].mkdir(exist_ok=True)

    # needs test
    def fetch(self, requests=requests):
        repodata = {}
        for platform, channel in self.channel_info.items():
            result = requests.get(channel["url"])
            repodata[platform] = result.json()
        self._repodata_dict = repodata
        return repodata

    def filter_repodata(self, package_list, platform):
        repo_data = self._repodata_dict[platform]
        filtered_content = {
            "packages": {},
            "packages.conda": {},
            "info": repo_data["info"],
        }

        packages = repo_data["packages"]
        conda_packages = repo_data["packages.conda"]

        for pkg_name in package_list:
            if pkg_name in packages.keys():
                filtered_content["packages"][pkg_name] = packages[pkg_name]

            if pkg_name in conda_packages.keys():
                filtered_content["packages.conda"][pkg_name] = conda_packages[pkg_name]

        return filtered_content

    def filter_all_write_repodata(self, package_list):
        self.create_directories()
        for platform in self.channel_info.keys():
            repodata = self.filter_repodata(package_list, platform)
            write_path = self.channel_info[platform]["dir"] / "repodata.json"
            with open(write_path, "w") as f:
                f.write(json.dumps(repodata))

    # needs mock on test
    # this will perform a fetch
    def conda_vendor_artifacts_from_solutions(self, conda_solution, requests=requests):

        # go get the repodata
        self.fetch(requests=requests)

        print(f"channel_info: {self.channel_info}")

        complete_manifest_list = []
        for platform, info in self.channel_info.items():
            repodata = self._repodata_dict[platform]

            pkg_names = [
                link["dist_name"]
                for link in conda_solution
                if link["platform"] == platform
            ]
            # print(f'pkg_names: {pkg_names}')

            pkg_correct_extensions = self.create_dot_conda_and_tar_pkg_list(
                pkg_names, platform
            )
            # print(f'pkg_correct_Extensions: {pkg_correct_extensions}')

            manifest_list = self.format_manifest(
                pkg_correct_extensions, base_url=self.base_url, platform=platform
            )

            # print(f'manifest_list {manifest_list}')

            complete_manifest_list.extend(manifest_list)

        return {"resources": complete_manifest_list}

    def create_dot_conda_and_tar_pkg_list(self, match_list, platform):
        dot_conda_channel_pkgs = [
            pkg.split(".conda")[0]
            for pkg in self._repodata_dict[platform]["packages.conda"].keys()
        ]

        desired_pkg_extension_list = []
        for pkg in match_list:
            ext = ".conda" if pkg in dot_conda_channel_pkgs else ".tar.bz2"
            desired_pkg_extension_list.append(f"{pkg}{ext}")

        return desired_pkg_extension_list

    def format_manifest(self, pkg_extension_list, base_url, platform):
        manifest_list = []

        for pkg in pkg_extension_list:
            if pkg.endswith(".conda"):
                pkg_type = "packages.conda"
            else:
                pkg_type = "packages"
            print("REPODATA")

            manifest_list.append(
                {
                    "url": f"{base_url}/{platform}/{pkg}",
                    "name": f"{pkg}",
                    "validation": {
                        "type": "sha256",
                        "value": self._repodata_dict[platform][pkg_type][pkg]["sha256"],
                    },
                }
            )

        return manifest_list

    @staticmethod
    def download_and_validate(out, url, sha256, requests=requests):
        url_data = requests.get(url)
        with open(out, "wb") as f:
            f.write(url_data)

            calculated_sha = CondaChannel._calc_sha256(url_data)
            if sha256 != calculated_sha:
                raise RuntimeError(
                    f"SHA256 does not match for {out} calculated SHA: {calculated_sha}, "
                    "manifest SHA: {sha256}"
                )

    @staticmethod
    def _calc_sha256(byte_array):
        return hashlib.sha256(byte_array).hexdigest()

    # TODO: needs test
    def get_output_path(self, url):
        for platform, channel in self.channel_info.items():
            if platform in url:
                return channel["dir"]

        raise RuntimeError(f"no valid architecture found: {url}")
        return None

    def download_binaries(self, manifest_dict: dict, requests=requests) -> None:
        # TODO: validate the sha 256 in seperate function, Not currently validating files ONLY download.
        self.create_directories()
        resources_list = manifest_dict["resources"]
        for resource in resources_list:
            output_path = self.get_output_path(resource["url"])
            if resource["validation"]["type"] != "sha256":
                raise RuntimeError(
                    'invalid checksum type: {resource["validation"]["type"]}'
                )
            self.download_and_validate(
                output_path / resource["name"],
                resource["url"],
                resource["validation"]["value"],
                requests=requests,
            )


# needs to be pushed DO WE EVEN NEED THIS ? where is package_file_names_list
def fetch_repodata(package_file_names_list, requests=requests, platform="linux-64"):
    conda_channel = CondaChannel()
    conda_channel.fetch()
    filtered_content = conda_channel.filter_repodata(
        package_file_names_list, platform=platform
    )
    # TODO: we need to write this to the correct architecture repo so we can have a local channel
    return filtered_content


# TODO: need a function to write yaml dump probably just add out to this
# TODO: this should also make or use a function that makes a local_yaml. Lets just make sure we can resolve
def conda_vendor(
    environment_yml,
    outpath=pathlib.Path("./"),
    conda_lock_wrapper=CondaLockWrapper(),
    requests=requests,
    conda_channel = CondaChannel(platforms=["linux-64", "noarch"])
    
):
    # NOTE: if you pass none to not write yaml
    link_actions = conda_lock_wrapper.solution_from_environment(environment_yml)
    manifest = conda_channel.conda_vendor_artifacts_from_solutions(
        conda_solution=link_actions, requests=requests
    )
    print(manifest)
    outpath_file_name = outpath / "vendor_manifest.yaml"
    if outpath:
        with open(outpath_file_name, "w") as f:
            yaml.dump(manifest, f)

    return manifest


def parse_environment(environment_yml):
    parser = CondaLockWrapper()
    specs = parser.parse(environment_yml)
    return specs
