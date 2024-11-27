import logging
from http import HTTPStatus

from flask_restx import Api
from tdt_api.exception.api_exception import ApiException

log = logging.getLogger(__name__)



api = Api(version='1.0.0', title='TDT RESTFUL API',
          description='TDT cloud service API',
          environ='development')


@api.errorhandler
def default_error_handler(e):
    message = 'An unhandled exception occurred.'
    log.exception(message)

    return {'message': message}, HTTPStatus.INTERNAL_SERVER_ERROR


@api.errorhandler(ApiException)
def handle_bad_request(error):
    log.exception(error.message)

    return {'message': error.message}, error.status_code


@api.errorhandler(ValueError)
def handle_value_error(error):
    log.exception(str(error))

    return {'message': str(error)}, HTTPStatus.BAD_REQUEST