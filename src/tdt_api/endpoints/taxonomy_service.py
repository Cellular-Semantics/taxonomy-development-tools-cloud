import os
import flask
import logging
import subprocess
from flask_restx import Resource
from tdt_api.restx import api
from flask import send_from_directory, request, make_response, jsonify
from tdt_api.exception.api_exception import ApiException
from tdt_api.utils.command_line_utils import runcmd
from tdt_api.utils.github_utils import check_user_permission, Permissions, init_taxonomy_folder
from tdt_api.utils.jwt_utils import get_session_info


api = api.namespace('api', description='Taxonomy API')
log = logging.getLogger(__name__)

TAXONOMIES_VOLUME = os.getenv('TAXONOMIES_VOLUME')
RLTBL_DB = '.relatable/relatable.db'


@api.route('/taxonomies', methods=['GET'])
class TaxonomiesEndpoint(Resource):

    def get(self):
        """
        Taxonomies listing

        Returns the metadata of all registered taxonomies.
        """
        response = flask.jsonify("Taxonomies listing")
        return response

@api.route('/session_info/<string:repo_name>', methods=['GET'])
class GetSessionInfoEndpoint(Resource):

    def get(self, repo_name):
        """
        Get session information

        Returns the user, repo_org, and permission level.
        """
        user, email, repo_org = get_session_info(request)
        permission, status_code = check_user_permission(repo_org, repo_name, user)
        return {
            "user": user,
            "repo_org": repo_org,
            "permission": permission.value,
            "tdt_web": os.getenv('TDT_WEB', '')
        }, status_code

@api.route('/check_permissions/<string:repo_org>/<string:repo_name>/<string:user_id>', methods=['GET'])
class CheckPermissionsEndpoint(Resource):

    def get(self, repo_org, repo_name, user_id):
        """
        Check user permissions for a given repository.

        Returns the permission level (read, write, none) for the user.
        """
        permission, status_code = check_user_permission(repo_org, repo_name, user_id)
        return permission.value, status_code


@api.route('/browser/<string:taxonomy>/<path:path>', methods=['GET', 'POST'])
class BrowserEndpoint(Resource):

    def get(self, taxonomy, path):
        print(f"browse {taxonomy}/{path}")
        taxonomy_dir = os.path.join(TAXONOMIES_VOLUME, taxonomy)
        nanobot_db_path = os.path.join(taxonomy_dir, RLTBL_DB)

        if not os.path.exists(nanobot_db_path):
            runcmd("make init", cwd=taxonomy_dir)
            print(f"Taxonomy {taxonomy} initialized successfully.")

        user, email, repo_org = get_session_info(request)
        permission, status_code = check_user_permission(repo_org, taxonomy, user)

        return rltbl(request,'GET', taxonomy, path, user, permission.to_boolean())

    def post(self, taxonomy, path):
        print(f"browse {taxonomy}/{path}")
        taxonomy_dir = os.path.join(TAXONOMIES_VOLUME, taxonomy)
        nanobot_db_path = os.path.join(taxonomy_dir, RLTBL_DB)

        if not os.path.exists(nanobot_db_path):
            runcmd("make init", cwd=taxonomy_dir)
            print(f"Taxonomy {taxonomy} initialized successfully.")

        user, email, repo_org = get_session_info(request)
        permission, status_code = check_user_permission(repo_org, taxonomy, user)

        return rltbl(request, 'POST', taxonomy, path, user, permission.to_boolean())

@api.route('/init_taxonomy/<string:taxonomy>', methods=['GET'])
class InitTaxonomyEndpoint(Resource):

    def get(self, taxonomy):
        print(f"init {taxonomy}")
        taxonomy_dir = os.path.join(TAXONOMIES_VOLUME, taxonomy)
        runcmd("make init", cwd=taxonomy_dir)
        return "Success"


@api.route('/add_taxonomy', methods=['POST'])
class AddTaxonomyEndpoint(Resource):

    def post(self):
        data = request.get_json()
        repo_url = data.get('repo_url')
        branch = data.get('branch', 'main')
        if not str(repo_url).endswith(".git"):
            repo_url = repo_url + ".git"
        repo_name = str(repo_url).split("/")[-1].split(".")[0]
        taxonomy_dir = os.path.join(TAXONOMIES_VOLUME, repo_name)
        if os.path.exists(taxonomy_dir):
            return {"message": "Repository already cloned and initialized."}, 200
        else:
            return init_taxonomy_folder(branch, repo_url, TAXONOMIES_VOLUME, taxonomy_dir)

def rltbl(api_request, method, taxonomy, path, username, readonly="TRUE"):
    """Call Relatable as a CGI script."""
    path = f'/{path}'
    data = api_request.get_data().decode('utf-8')

    env={
        'GATEWAY_INTERFACE': 'CGI/1.1',
        'REQUEST_METHOD': method,
        'PATH_INFO': path,
        'QUERY_STRING': api_request.query_string.decode('utf-8'),
        'CONTENT_TYPE': api_request.headers.get('content-type') or "text/html",
        'RLTBL_READONLY': readonly,
        'RLTBL_USER': username,
        'RLTBL_ROOT': os.getenv("RLTBL_ROOT") + taxonomy,
        # 'RLTBL_ROOT': "/api/browser/" + taxonomy,
        # 'RLTBL_ROOT': "/tdt_api/browser/" + taxonomy,  # for PROD
        'RLTBL_GIT_AUTHOR': username,
    }
    print("USER is: " + username)
    # print("RLTBL", env, data, type(data))
    taxonomy_dir = os.path.join(TAXONOMIES_VOLUME, taxonomy)
    result = subprocess.run(
        [os.path.join(taxonomy_dir, 'bin/rltbl')],
        cwd=f'{TAXONOMIES_VOLUME}/{taxonomy}/',
        env=env,
        input=data or '',
        text=True,
        capture_output=True
    )

    if result.returncode != 0:
        log.error("Error running rltbl")
        log.error("Return code: " + str(result.returncode))
        log.error("Stderr: " + str(result.stderr))
        raise ApiException("Error running rltbl", 500)

    status = 200
    headers = {}
    body = []
    reading_headers = True
    for line in result.stdout.splitlines():
        if reading_headers and line.strip() == '':
            reading_headers = False
            continue
        if reading_headers:
            name, value = line.split(': ', 1)
            if name.lower() == 'status':
                status = value
            if name.lower() in ['vary', 'cookie', 'set-cookie']:
                pass
            else:
                headers[name] = value
        else:
            body.append(line)
    return make_response(('\n'.join(body), status, headers))
