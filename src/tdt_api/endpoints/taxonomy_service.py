import flask
import logging
from flask_restx import Resource
from tdt_api.restx import api
from tdt_api.exception.api_exception import ApiException

ns = api.namespace('api', description='Taxonomy API')

log = logging.getLogger(__name__)

@ns.route('/taxonomies', methods=['GET'])
class TaxonomiesEndpoint(Resource):

    def get(self):
        """
        Taxonomies listing

        Returns the metadata of all registered taxonomies.
        """
        response = flask.jsonify("Taxonomies listing")
        return response
