import pytest
from dotenv import load_dotenv
import os
from tdt_api.utils.github_utils import check_user_permission, Permissions, is_user_member_of_org

load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))


@pytest.fixture
def github_token():
    return os.getenv('GITHUB_TOKEN')

def test_check_user_permission_read(github_token):
    repo_org = "brain-bican"
    repo_name = "whole_mouse_brain_taxonomy"
    user_id = "bicantester"

    permission, status_code = check_user_permission(repo_org, repo_name, user_id)

    assert status_code == 200
    assert permission == Permissions.READ

def test_check_user_permission_write(github_token):
    repo_org = "brain-bican"
    repo_name = "whole_mouse_brain_taxonomy"
    user_id = "tdt-robot"

    permission, status_code = check_user_permission(repo_org, repo_name, user_id)

    assert status_code == 200
    assert permission == Permissions.WRITE

def test_check_user_permission_no_access(github_token):
    repo_org = "microsoft"
    repo_name = "vscode"
    user_id = "tdt-robot"

    permission, status_code = check_user_permission(repo_org, repo_name, user_id)

    assert status_code == 403
    assert permission == Permissions.NO_ACCESS

def test_is_user_member_of_org_member(github_token):
    orgs = ["Cellular-Semantics", "microsoft"]
    user_id = "hkir-dev"

    result = is_user_member_of_org(orgs, user_id)
    assert result is True

def test_is_user_member_of_org_not_member(github_token):
    orgs = ["microsoft", "APPLE"]
    user_id = "tdt-robot"

    result = is_user_member_of_org(orgs, user_id)
    assert result is False