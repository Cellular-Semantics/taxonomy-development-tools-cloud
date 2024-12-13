import os
import requests
import logging
from enum import Enum

log = logging.getLogger(__name__)


class Permissions(Enum):
    READ = 'read'
    WRITE = 'write'
    NO_ACCESS = 'no_access'

def check_user_permission(repo_org:str, repo_name: str, user_id: str) -> tuple[Permissions, int]:
    """
    Check the permission of the user in the given repository.

    :param repo_org: GitHub organization name
    :param repo_name: GitHub repository name
    :param user_id: GitHub user id
    :return: Permission of the user in the repository: read, write, no_access
    """
    github_token = os.getenv('GITHUB_TOKEN')
    headers = {
        'Authorization': f'token {github_token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    url = f'https://api.github.com/repos/{repo_org}/{repo_name}/collaborators/{user_id}/permission'
    response = requests.get(url, headers=headers)
    permission = Permissions.NO_ACCESS
    if response.status_code == 200:
        permission = response.json().get('user').get('permissions')
        if permission.get("push", False):
            permission = Permissions.WRITE
        else:
            permission = Permissions.READ
    else:
        print(response.json())
        log.error(f"An error occurred: {response.json()}")
    return permission, response.status_code
