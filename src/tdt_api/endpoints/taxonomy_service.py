import os
import flask
import logging
import subprocess
import jwt
from flask_restx import Resource
from tdt_api.restx import api
from flask import send_from_directory, request, make_response, jsonify
from tdt_api.exception.api_exception import ApiException
from tdt_api.utils.command_line_utils import runcmd
from tdt_api.utils.github_utils import check_user_permission, Permissions, init_taxonomy_folder

api = api.namespace('api', description='Taxonomy API')
log = logging.getLogger(__name__)

TAXONOMIES_VOLUME = os.getenv('TAXONOMIES_VOLUME')
RLTBL_DB = '.relatable/relatable.db'
DEFAULT_USER = "default_user"


@api.route('/taxonomies', methods=['GET'])
class TaxonomiesEndpoint(Resource):

    def get(self):
        """
        Taxonomies listing

        Returns the metadata of all registered taxonomies.
        """
        response = flask.jsonify("Taxonomies listing")
        return response

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

        user, email, repo_org = get_session_info()
        permission, status_code = check_user_permission(repo_org, taxonomy, user)

        return rltbl(request,'GET', taxonomy, path, user, permission.to_boolean())

    def post(self, taxonomy, path):
        print(f"browse {taxonomy}/{path}")
        taxonomy_dir = os.path.join(TAXONOMIES_VOLUME, taxonomy)
        nanobot_db_path = os.path.join(taxonomy_dir, RLTBL_DB)

        if not os.path.exists(nanobot_db_path):
            runcmd("make init", cwd=taxonomy_dir)
            print(f"Taxonomy {taxonomy} initialized successfully.")

        user, email, repo_org = get_session_info()
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
    }
    print(env)
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


def get_session_info():
    token = request.args.get('token')
    user = DEFAULT_USER
    email = None
    repo_org = None
    if token:
        decoded = jwt.decode(token, os.getenv('TOKEN_SECRET'), algorithms=['HS256'])
        print("Session data :" + str(decoded))
        user = decoded.get('name')
        email = decoded.get('email')
        repo_org = decoded.get('repoOrg')

    return user, email, repo_org

def nanobot(method, taxonomy, path):
    """Call Nanobot as a CGI script
    for the given dataset, and path."""
    taxon_dir = f'{TAXONOMIES_VOLUME}/{taxonomy}/'
    # filepath = os.path.join(taxon_dir, path)
    # if path.endswith('.tsv') and os.path.isfile(filepath):
    #     send_from_directory(directory=taxon_dir, path=path)

    result = subprocess.run(
        [os.path.join(taxon_dir, 'build/nanobot')],
        cwd=f'{TAXONOMIES_VOLUME}/{taxonomy}/',
        env={
            'GATEWAY_INTERFACE': 'CGI/1.1',
            'REQUEST_METHOD': method,
            'PATH_INFO': path,
            'QUERY_STRING': request.query_string,
        },
        input=request.get_data(as_text=True),
        text=True,
        capture_output=True
    )
    reading_headers = True
    body = []
    response_status = None
    response_headers = dict()
    for line in result.stdout.splitlines():
        if reading_headers and line.strip() == '':
            reading_headers = False
            continue
        if reading_headers:
            name, value = line.split(': ', 1)
            if name == 'status':
                response_status = value
            else:
                response_headers[name] = value
        else:
            body.append(line)
    response = make_response('\n'.join(body))
    response.status_code = int(response_status.split(" ")[0]) if response_status else response.status_code
    response.headers.clear()
    for header in response_headers:
        response.headers.add(header, response_headers[header])
        if header.strip().lower() == "content-type":
            response.headers.add("Content-Type", response_headers[header])
    return response