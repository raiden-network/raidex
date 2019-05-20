from flask import jsonify


def make_error_dict(status_code, message):
    return {
        'status': status_code,
        'message': message,
    }


def make_error_response(status_code, message):
    response = jsonify(make_error_dict(status_code, message))
    response.status_code = status_code
    return response


def bad_request(error):
        return make_error_response(400, 'The request was malformed: ' + str(error.description))


def not_found(error):
    return make_error_response(404, 'The resource was not found on the server: ' + str(error))


def internal_error(error):
    return make_error_response(500,
                               'The server enquoteed an internal error and was unable to complete your request: '
                               + str(error))
