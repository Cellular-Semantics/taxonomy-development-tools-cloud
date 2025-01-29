import os
import flask
import logging
import subprocess
from flask_restx import Resource, fields
from tdt_api.restx import api
from flask import send_from_directory, request, make_response, jsonify
from tdt_api.exception.api_exception import ApiException
from tdt_api.utils.command_line_utils import runcmd
from tdt_api.utils.github_utils import init_taxonomy_folder


TAXONOMIES_VOLUME = os.getenv('TAXONOMIES_VOLUME')
ADMIN_SECRET = os.getenv('ADMIN_SECRET')

api = api.namespace('admin_api', description='TDT Admin API')

log = logging.getLogger(__name__)

init_taxonomies_model = api.model('InitTaxonomies', {
    'repositories': fields.Raw(required=True, example={
        "https://github.com/brain-bican/human-brain-cell-atlas_v1_neurons.git": "cloud",
        "https://github.com/brain-bican/human-brain-cell-atlas_v1_non-neuronal.git": "cloud-rltbl",
        "https://github.com/brain-bican/whole_mouse_brain_taxonomy.git": "cloud",
        "https://github.com/Cellular-Semantics/human-neocortex-non-neuronal-cells.git": "cloud",
        "https://github.com/Cellular-Semantics/human-neocortex-mge-derived-interneurons.git": "cloud",
        "https://github.com/Cellular-Semantics/human-neocortex-it-projecting-excitatory-neurons.git": "cloud",
        "https://github.com/Cellular-Semantics/human-neocortex-deep-layer-excitatory-neurons.git": "cloud",
        "https://github.com/Cellular-Semantics/human-neocortex-cge-derived-interneurons.git": "cloud",
        "https://github.com/brain-bican/human-neocortex-middle-temporal-gyrus.git": "cloud",
        "https://github.com/Cellular-Semantics/nhp_basal_ganglia_macaque_taxonomy.git": "cloud",
        "https://github.com/Cellular-Semantics/nhp_basal_ganglia_human_taxonomy.git": "cloud"
    }),
    'admin_secret': fields.String(required=True, example="your_admin_secret")
})

reload_taxonomy_model = api.model('ReloadTaxonomy', {
    'repository': fields.String(required=True, example="https://github.com/brain-bican/human-brain-cell-atlas_v1_neurons"),
    'branch': fields.String(required=True, example="cloud"),
    'admin_secret': fields.String(required=True, example="your_admin_secret")
})

@api.route('/init_taxonomies', methods=['POST'])
class InitTaxonomiesEndpoint(Resource):

    @api.expect(init_taxonomies_model, validate=True)
    @api.doc(description="Initializes the taxonomies folder structure in the server.")
    def post(self):
        data = request.get_json()
        repo_urls = data.get('repositories')
        admin_secret = data.get('admin_secret')

        if admin_secret != ADMIN_SECRET:
            raise ApiException("Invalid admin secret.", 403)
        elif not repo_urls:
            raise ApiException("Invalid request data. 'repositories' is mandatory data.", 400)

        for repo_url in repo_urls:
            if not str(repo_url).endswith(".git"):
                repo_url = repo_url + ".git"
            repo_name = str(repo_url).split("/")[-1].split(".")[0]
            taxonomy_dir = os.path.join(TAXONOMIES_VOLUME, repo_name)
            check_directory_traversal_attack(repo_name, taxonomy_dir)

            if not os.path.exists(taxonomy_dir):
                log.info(f"Taxonomy {repo_name} does not exist. Initializing...")
                branch = repo_urls[repo_url]
                init_taxonomy_folder(branch, repo_url, TAXONOMIES_VOLUME, taxonomy_dir)
                log.info(f"Taxonomy {repo_name} initialized successfully.")

        return "Taxonomies updated successfully.", 200


@api.route('/reload_taxonomy', methods=['POST'])
class ReloadTaxonomy(Resource):

    @api.expect(reload_taxonomy_model, validate=True)
    @api.doc(description="Reloads the given taxonomy in the server.")
    def post(self):
        data = request.get_json()
        repo_url = data.get('repository')
        branch = data.get('branch')
        admin_secret = data.get('admin_secret')

        if admin_secret != ADMIN_SECRET:
            raise ApiException("Invalid admin secret.", 403)

        if not str(repo_url).endswith(".git"):
            repo_url = repo_url + ".git"
        repo_name = str(repo_url).split("/")[-1].split(".")[0]
        taxonomy_dir = os.path.join(TAXONOMIES_VOLUME, repo_name)
        check_directory_traversal_attack(repo_name, taxonomy_dir)

        if os.path.exists(taxonomy_dir):
            # delete taxonomy folder
            runcmd(f"rm -rf {taxonomy_dir}")
            log.info(f"Taxonomy {repo_name} deleted successfully.")

        init_taxonomy_folder(branch, repo_url, TAXONOMIES_VOLUME, taxonomy_dir)
        log.info(f"Taxonomy {repo_name} initialized successfully.")

        return "Taxonomies updated successfully.", 200

def check_directory_traversal_attack(folder_name, target_dir, safe_dir=TAXONOMIES_VOLUME):
    """
    Check if there is a directory traversal attack in the given folder name. If the target directory is not a subdirectory of the safe directory, raise an exception.
    :param folder_name: provided folder name
    :param target_dir: directory to check
    :param safe_dir: safe directory that data can be stored
    :return:
    """
    if os.path.commonprefix(
            (os.path.realpath(target_dir), safe_dir)) != safe_dir:
        raise ApiException("Invalid repository name: " + folder_name, 400)

