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
    pass

#class CondaLockWrapper:
#    def __init__(self, environment_yml):
#        self.platform='linux-64'
#        parse_return = parse_environment_file(environment_yml, self.platform)
#        self.specs = parse_return.specs
#        self.channels = parse_return.channels
#
#    def solve(self):
#        solved_env = solve_specs_for_arch(
#            "conda", self.channels, specs=self.specs, platform=self.platform
#        )
#        self.solution = solved_env["actions"]["FETCH"]
#        return self.solution


class CondaChannel:
    def __init__(
        self,
        environment_yml,
        *,

        channel_root=pathlib.Path("./"),
        channel_name='local_channel'
    ):
        parse_return = parse_environment_file(environment_yml, 'linux-64')
        self.env = {
                'specs': parse_return.specs,
                'channels': parse_return.channels
                }
        with open(environment_yml) as f:
            self.env['environment'] = yaml.load(f, Loader=yaml.SafeLoader)

        self.platforms = ['linux-64', 'noarch']
        self.manifest = None

        self.channel_root = pathlib.Path(channel_root)
        self.channel_name = pathlib.PurePath(channel_name).name
        self.local_channel = self.channel_root / self.channel_name

        self._repodata_dict = None
        self._requires_fetch = True


#        self.channel_info = {}
#        for platform in platforms:
#            self.channel_info[platform] = {
#                "dir": self.local_channel / platform,
#                "url": self.base_url + platform + "/repodata.json",
#            }

    #TODO: make this idempotent
    def solve_environment(self):
        self.env['solution'] = solve_specs_for_arch(
            "conda", self.env['channels'], specs=self.env['specs'],
            platform='linux-64'
        )
        self.env['fetch_actions'] = solved_env["actions"]["FETCH"]
        return self.env['fetch_actions']

    def get_manifest(self):
        fetch_actions = self.solve_environment()
        vendor_manifest_list = []
        for conda_lock_fetch_info in fetch_actions:
            url = conda_lock_fetch_info['url']
            name = conda_lock_fetch_info['fn']
            validation_value = conda_lock_fetch_info['sha256']
            validation = {'type': 'sha256', 'value': validation_value}
            vendor_manifest_list.append(
                    {
                        'url': url,
                        'name': name,
                        'validation': validation
                    }
            )
        self.manifest = vendor_manifest_list
        return self.manifest

    def create_manifest(self, *, manifest_filename=None):
        manifest = get_manifest()

        if not manifest_filename:
            manifest_filename = 'vendor_manifest.yaml'

        cleaned_name = pathlib.PurePath(manifest_filename).name
        outpath_file_name = self.channel_root / cleaned_name
        with open(outpath_file_name, "w") as f:
            yaml.dump(manifest, f)
        return manifest

    def create_directories(self):
        self.local_channel.mkdir(parents=True, exist_ok=True)
        for platform, info in self.channel_info.items():
            info["dir"].mkdir(exist_ok=True)

    # needs test
    def fetch(self,  force=False):
        if not (force or self._requires_fetch):
            return

        repodata = {}
        for platform, channel in self.channel_info.items():
            result = requests.get(channel["url"])
            repodata[platform] = result.json()

        self._repodata_dict = repodata
        self._requires_fetch = False
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

    def generate_repodata(self, package_list):
        self.create_directories()

        for platform in self.channel_info.keys():
            repodata = self.filter_repodata(package_list, platform)
            write_path = self.channel_info[platform]["dir"] / "repodata.json"
            with open(write_path, "w") as f:
                f.write(json.dumps(repodata))


    def _fix_extensions(self, match_list, platform):
        dot_conda_channel_pkgs = [
            pkg.split(".conda")[0]
            for pkg in self._repodata_dict[platform]["packages.conda"].keys()
        ]

        desired_pkg_extension_list = []
        for pkg in match_list:
            ext = ".conda" if pkg in dot_conda_channel_pkgs else ".tar.bz2"
            desired_pkg_extension_list.append(f"{pkg}{ext}")

        return desired_pkg_extension_list

    def format_manifest(self, pkg_list, platform):
        manifest_list = []

        def pkg_type(pkg):
            return "packages.conda" if pkg.endswith(".conda") else "packages"

        for pkg in pkg_list:

            manifest_list.append(
                {
                    "url": f"{self.base_url}{platform}/{pkg}",
                    "name": f"{pkg}",
                    "validation": {
                        "type": "sha256",
                        "value": self._repodata_dict[platform][pkg_type(pkg)][pkg]["sha256"],
                    },
                }
            )

        return manifest_list


    # this will perform a fetch
    def generate_manifest(self, conda_solution ):
        self.fetch()

        complete_manifest_list = []
        for platform, info in self.channel_info.items():
            pkg_names = [
                link["dist_name"]
                for link in conda_solution
                if link["platform"] == platform
            ]

            pkg_correct_extensions = self._fix_extensions(pkg_names, platform)

            manifest_list = self.format_manifest(
                pkg_correct_extensions, platform=platform
            )

            complete_manifest_list.extend(manifest_list)

        return {"resources": complete_manifest_list}



    @staticmethod
    def download_and_validate(out, url, sha256):
        response = requests.get(url)
        url_data = response.content
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

    def download_binaries(self, manifest_dict: dict) -> None:
        # TODO: validate the sha 256 in seperate function, Not currently validating files ONLY download.
        self.create_directories()
        self.fetch()

#        print('beginning download: ')
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

            )
 #           print(f'downloading: {resource["url"]} to {output_path / resource["name"]}')



def default_conda_lock():
    return None #CondaLockWrapper()

def default_conda_channel():
    return None #CondaChannel(platforms=['linux-64', 'noarch'])

def get_manifest(environment_yml):
    conda_channel = CondaChannel(environment_yml)
    return conda_channel.get_manifest()

def create_manifest(
    environment_yml,
    *,
    manifest_filename=None
):
    conda_channel = CondaChannel(environment_yml)
    return conda_channel.create_manifest(environment_yml,
            manifest_filename=manifest_filename)

def get_local_environment_yaml(
    environment_yml,
    *,
    conda_channel=default_conda_channel(),
    local_environment_name=None
):
    with open(environment_yml, "r") as f:
        local_yml = yaml.load(f, Loader=yaml.SafeLoader)

    if not local_environment_name:
        local_environment_name = f"local_{local_yml['name']}"

    local_yml['name'] = local_environment_name
    local_yml["channels"] = [
            f"file://{conda_channel.local_channel.absolute()}",
            "nodefaults"
            ]
    return local_yml


def create_local_environment_yaml(
    environment_yml,
    *,
    conda_channel=default_conda_channel(),
    local_environment_name=None,
    local_environment_filename=None
):

    local_yml = get_local_environment_yaml(environment_yml,
            conda_channel=conda_channel,
            local_environment_name=local_environment_name)

    if not local_environment_filename:
        local_environment_filename='local_yaml.yaml'

    cleaned_name = pathlib.PurePath(local_environment_filename).name
    outpath_file_name = conda_channel.channel_root / cleaned_name
    with open(outpath_file_name, "w") as f:
        yaml.safe_dump(local_yml,f , sort_keys=False)


def create_local_channels(
    environment_yml,
    *,
    conda_lock=default_conda_lock(),
    conda_channel=default_conda_channel(),
    manifest_filename = None,
    local_environment_name = None,
    local_environment_filename = None,
):
    manifest = create_manifest(environment_yml,
            manifest_filename=manifest_filename
            )

    create_local_environment_yaml(environment_yml,
        conda_channel=conda_channel,
        local_environment_name=local_environment_name,
        local_environment_filename=local_environment_filename
        )

    conda_channel.download_binaries(manifest)
    package_list = [resource["name"] for resource in manifest["resources"]]
    conda_channel.generate_repodata(package_list)


def parse_environment(environment_yml):
    parser = CondaLockWrapper()
    specs = parser.parse(environment_yml)
    return specs

def fetch_repodata(package_file_names_list,  platform="linux-64"):
    conda_channel = CondaChannel()
    conda_channel.fetch()
    filtered_content = conda_channel.filter_repodata(
        package_file_names_list, platform=platform
    )
    return filtered_content

