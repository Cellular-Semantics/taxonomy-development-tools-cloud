import os
import requests
import logging
from enum import Enum

from tdt_api.utils.command_line_utils import runcmd

from cachetools import TTLCache, cached

log = logging.getLogger(__name__)

# Create a cache with a time-to-live of 600 seconds (10 minutes)
cache = TTLCache(maxsize=100, ttl=600)

DEFAULT_USER = "visitor"


class Permissions(Enum):
    READ = 'read'
    WRITE = 'write'
    NO_ACCESS = 'no_access'

    def to_boolean(self):
        if self in {Permissions.READ, Permissions.NO_ACCESS}:
            return "TRUE"
        elif self == Permissions.WRITE:
            return "FALSE"


def init_taxonomy_folder(branch, repo_url, taxonomies_volume, taxonomy_dir):
    try:
        # Clone the repository
        runcmd(f"git clone {repo_url}", cwd=taxonomies_volume)

        # Navigate to the branch
        runcmd(f"git checkout {branch}", cwd=taxonomy_dir, supress_exceptions=True)

        # Run 'make init'
        runcmd(f"make init", cwd=taxonomy_dir)

        return {"message": "Repository cloned and initialized successfully."}, 200
    except Exception as e:
        log.error(f"An error occurred: {e}")
        return {"message": "An error occurred while processing the request."}, 500

@cached(cache)
def check_user_permission(repo_org:str, repo_name: str, user_id: str) -> tuple[Permissions, int]:
    """
    Check the permission of the user in the given repository.

    :param repo_org: GitHub organization name
    :param repo_name: GitHub repository name
    :param user_id: GitHub user id
    :return: Permission of the user in the repository: read, write, no_access
    """
    permission = Permissions.NO_ACCESS
    status_code = 403
    if repo_org and user_id != DEFAULT_USER:
        github_token = os.getenv('GITHUB_TOKEN')
        headers = {
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        url = f'https://api.github.com/repos/{repo_org}/{repo_name}/collaborators/{user_id}/permission'
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            permission = response.json().get('user').get('permissions')
            if permission.get("push", False):
                permission = Permissions.WRITE
            else:
                permission = Permissions.READ
        else:
            print(response.json())
            log.error(f"An error occurred: {response.json()}")
        status_code = response.status_code
    return permission, status_code


def is_user_member_of_org(orgs, user_id):
    """
    Check if the user is a member of any of the given organizations.

    :param orgs: List of GitHub organization names
    :param user_id: GitHub user id
    :return: True if the user is a member of any organization, False otherwise
    """
    github_token = os.getenv('GITHUB_TOKEN')
    headers = {
        'Authorization': f'token {github_token}',
        'Accept': 'application/vnd.github.v3+json'
    }

    for org in orgs:
        url = f'https://api.github.com/orgs/{org}/members/{user_id}'
        response = requests.get(url, headers=headers)
        if response.status_code == 204:
            return True
    return False
