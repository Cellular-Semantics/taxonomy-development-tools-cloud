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

update_taxonomies_model = api.model('UpdateTaxonomies', {
    'repositories': fields.List(fields.String, required=True, example=[
        "https://github.com/brain-bican/human-brain-cell-atlas_v1_neurons",
        "https://github.com/brain-bican/human-brain-cell-atlas_v1_non-neuronal",
        "https://github.com/brain-bican/whole_mouse_brain_taxonomy",
        "https://github.com/Cellular-Semantics/human-neocortex-non-neuronal-cells",
        "https://github.com/Cellular-Semantics/human-neocortex-mge-derived-interneurons",
        "https://github.com/Cellular-Semantics/human-neocortex-it-projecting-excitatory-neurons",
        "https://github.com/Cellular-Semantics/human-neocortex-deep-layer-excitatory-neurons",
        "https://github.com/Cellular-Semantics/human-neocortex-cge-derived-interneurons",
        "https://github.com/brain-bican/human-neocortex-middle-temporal-gyrus",
        "https://github.com/Cellular-Semantics/nhp_basal_ganglia_macaque_taxonomy",
        "https://github.com/Cellular-Semantics/nhp_basal_ganglia_human_taxonomy",
    ]),
    'tdt_version': fields.String(required=True, example="2.0.0"),
    'admin_secret': fields.String(required=True, example="your_admin_secret")
})

@api.route('/update_taxonomies', methods=['POST'])
class UpdateTaxonomiesEndpoint(Resource):

    @api.expect(update_taxonomies_model, validate=True)
    @api.doc(description="Update taxonomies to the given version of the TDT.")
    def post(self):
        """
        Update taxonomies to the given version of the TDT.
        :return:
        """
        data = request.get_json()
        repo_urls = data.get('repositories')
        tdt_version = data.get('tdt_version')
        admin_secret = data.get('admin_secret')

        if admin_secret != ADMIN_SECRET:
            raise ApiException("Invalid admin secret.", 403)
        elif not repo_urls or not tdt_version:
            raise ApiException("Invalid request data. Required fields are 'repositories' and 'tdt_version'.", 400)

        for repo_url in repo_urls:
            if not str(repo_url).endswith(".git"):
                repo_url = repo_url + ".git"
            repo_name = str(repo_url).split("/")[-1].split(".")[0]
            taxonomy_dir = os.path.join(TAXONOMIES_VOLUME, repo_name)

            if not os.path.exists(taxonomy_dir):
                log.info(f"Taxonomy {repo_name} does not exist. Initializing...")
                # TODO switch to main branch on production
                init_taxonomy_folder("cloud", repo_url, TAXONOMIES_VOLUME, taxonomy_dir)
                log.info(f"Taxonomy {repo_name} initialized successfully.")

            update_run_sh(taxonomy_dir, tdt_version)

            runcmd("bash run.sh make upgrade", cwd=taxonomy_dir)
            # runcmd(f"git commit -a --message 'TDT upgrade to v{tdt_version}'", cwd=taxonomy_dir)
            # runcmd("git push", cwd=taxonomy_dir)

            log.info(f"Taxonomy {repo_name} updated to TDT version {tdt_version}.")
        return "Taxonomies updated successfully.", 200


def update_run_sh(taxonomy_dir, tdt_version):
    """
    Update run.sh file to use the given version of the TDT.
    :param taxonomy_dir: run.sh file directory
    """
    run_sh_path = os.path.join(taxonomy_dir, 'run.sh')
    if not os.path.exists(run_sh_path):
        log.error(f"{run_sh_path} does not exist.")
        raise ApiException(f"{run_sh_path} does not exist.", 500)

    try:
        with open(run_sh_path, 'r') as file:
            lines = file.readlines()

        with open(run_sh_path, 'w') as file:
            for line in lines:
                if line.startswith("IMAGE=${IMAGE:-taxonomy-development-tools"):
                    file.write("IMAGE=${IMAGE:-taxonomy-development-tools:" + tdt_version + "}\n")
                else:
                    file.write(line)
    except Exception as e:
        log.error(f"An error occurred while updating run.sh: {e}")
        raise ApiException("An error occurred while updating run.sh.", 500)