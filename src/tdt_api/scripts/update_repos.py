import os
import logging

from tdt_api.exception.api_exception import ApiException
from tdt_api.utils.command_line_utils import runcmd
from tdt_api.utils.github_utils import init_taxonomy_folder


log = logging.getLogger(__name__)

def update_repos(repositories, tdt_version, taxonomies_folder):
    """
    Updates taxonomies to the given version of the TDT.
    :return:
    """
    for repo_url in repositories:
        if not str(repo_url).endswith(".git"):
            repo_url = repo_url + ".git"
        repo_name = str(repo_url).split("/")[-1].split(".")[0]
        taxonomy_dir = os.path.join(taxonomies_folder, repo_name)

        if not os.path.exists(taxonomy_dir):
            log.info(f"Taxonomy {repo_name} does not exist. Initializing...")
            # Clone the repository
            runcmd(f"git clone {repo_url}", cwd=taxonomies_folder)

            # Navigate to the branch
            runcmd(f"git checkout {repositories[repo_url]}", cwd=taxonomy_dir, supress_exceptions=True)

            # Run 'make init'
            # runcmd(f"bash run.sh make init", cwd=taxonomy_dir)
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
                if " -ti " in line:
                    # don't run docker interactively and with tty
                    file.write(line.replace(' -ti ', ' '))
                else:
                    file.write(line)
    except Exception as e:
        log.error(f"An error occurred while updating run.sh: {e}")
        raise ApiException("An error occurred while updating run.sh.", 500)


repositories = {
    "https://github.com/brain-bican/human-brain-cell-atlas_v1_neurons.git": "cloud-rltbl",
    "https://github.com/brain-bican/human-brain-cell-atlas_v1_non-neuronal.git": "cloud-rltbl",
    "https://github.com/brain-bican/whole_mouse_brain_taxonomy.git": "cloud-rltbl",
    "https://github.com/Cellular-Semantics/human-neocortex-non-neuronal-cells.git": "cloud-rltbl",
    "https://github.com/Cellular-Semantics/human-neocortex-mge-derived-interneurons.git": "cloud-rltbl",
    "https://github.com/Cellular-Semantics/human-neocortex-it-projecting-excitatory-neurons.git": "cloud-rltbl",
    "https://github.com/Cellular-Semantics/human-neocortex-deep-layer-excitatory-neurons.git": "cloud-rltbl",
    "https://github.com/Cellular-Semantics/human-neocortex-cge-derived-interneurons.git": "cloud-rltbl",
    "https://github.com/brain-bican/human-neocortex-middle-temporal-gyrus.git": "cloud-rltbl",
    "https://github.com/Cellular-Semantics/nhp_basal_ganglia_macaque_taxonomy.git": "cloud-rltbl",
    "https://github.com/Cellular-Semantics/nhp_basal_ganglia_human_taxonomy.git": "cloud-rltbl",
}

update_repos(repositories, "2.1.0", "/Users/hk9/Downloads/tdt_cloud_rltbl")