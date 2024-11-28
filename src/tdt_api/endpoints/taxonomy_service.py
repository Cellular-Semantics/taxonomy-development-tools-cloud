import os
import flask
import logging
import subprocess
from flask_restx import Resource
from tdt_api.restx import api
from flask import send_from_directory, request, make_response, jsonify
from tdt_api.exception.api_exception import ApiException

TAXONOMIES_VOLUME = '/code/taxonomies'

api = api.namespace('api', description='Taxonomy API')

log = logging.getLogger(__name__)

@api.route('/taxonomies', methods=['GET'])
class TaxonomiesEndpoint(Resource):

    def get(self):
        """
        Taxonomies listing

        Returns the metadata of all registered taxonomies.
        """
        response = flask.jsonify("Taxonomies listing")
        return response

@api.route('/browser/<string:taxonomy>/<path:path>', methods=['GET', 'POST'])
class NanobotEndpoint(Resource):

    def get(self, taxonomy, path):
        print(f"browse {taxonomy}/{path}")
        return nanobot('GET', taxonomy, path)

    def post(self, taxonomy, path):
        print(f"browse {taxonomy}/{path}")
        return nanobot('POST', taxonomy, path)

@api.route('/init_taxonomy/<string:taxonomy>', methods=['GET'])
class InitTaxonomyEndpoint(Resource):

    def get(self, taxonomy):
        print(f"init {taxonomy}")
        taxonomy_dir = os.path.join(TAXONOMIES_VOLUME, "human-neocortex-non-neuronal-cells")
        subprocess.run(['make', 'init'], cwd=taxonomy_dir, check=True)
        return flask.jsonify("Success")


@api.route('/add_taxonomy', methods=['POST'])
class AddTaxonomyEndpoint(Resource):

    def post(self):
        data = request.get_json()
        repo_url = data.get('repo_url', 'https://github.com/Cellular-Semantics/human-neocortex-non-neuronal-cells.git')
        branch = data.get('branch', 'main')
        taxonomy_dir = os.path.join(TAXONOMIES_VOLUME, "human-neocortex-non-neuronal-cells")

        try:
            # Clone the repository
            subprocess.run(['git', 'clone', repo_url, TAXONOMIES_VOLUME], check=True)

            # Navigate to the branch
            subprocess.run(['git', 'checkout', branch], cwd=taxonomy_dir, check=True)

            # Run 'make init'
            subprocess.run(['make', 'init'], cwd=taxonomy_dir, check=True)

            return jsonify({"message": "Repository cloned and initialized successfully."}), 200
        except subprocess.CalledProcessError as e:
            log.error(f"An error occurred: {e}")
            return jsonify({"message": "An error occurred while processing the request."}), 500

def nanobot(method, taxonomy, path):
    """Call Nanobot as a CGI script
    for the given dataset, and path."""
    taxon_dir = f'{TAXONOMIES_VOLUME}/{taxonomy}/'
    filepath = os.path.join(taxon_dir, path)
    if path.endswith('.tsv') and os.path.isfile(filepath):
        send_from_directory(directory=taxon_dir, path=path)

    # result = subprocess.run(
    #     [os.path.join(os.getcwd(), 'bin/nanobot')],
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
    for header in response_headers:
        response.headers.add(header, response_headers[header])
    return response