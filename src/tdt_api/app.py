import os
from flask import Flask, Blueprint
from restx import api
from tdt_api.endpoints.taxonomy_service import api as api_namespace
from tdt_api.endpoints.admin_service import api as admin_api_namespace
from flask_cors import CORS
from dotenv import load_dotenv

app = Flask(__name__)
CORS(app)
app.config["CORS_HEADERS"] = "Content-Type"

# Get URL prefix from environment variable or uses root ('/') by default
url_prefix = os.environ.get("TDT_URL_PREFIX", "")

blueprint = Blueprint("tdt", __name__, url_prefix=url_prefix)


def initialize_app(flask_app):
    api.init_app(blueprint)
    api.add_namespace(api_namespace)
    api.add_namespace(admin_api_namespace)
    flask_app.register_blueprint(blueprint)


def main():
    if os.path.exists('.env'):
        load_dotenv('.env')

    initialize_app(app)
    app.run(host="0.0.0.0", port=8080, debug=False)


if __name__ == "__main__":
    main()