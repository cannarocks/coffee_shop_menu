from crypt import methods
import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
@TODO uncomment the following line to initialize the database
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! Running this function will add one
'''
# db_drop_and_create_all()

# ROUTES
'''
GET /drinks
    it should be a public endpoint
    it should contain only the drink.short() data representation
returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
    or appropriate status code indicating reason for failure
'''


@app.route('/drinks')
def get_drinks():
    return jsonify({
        'success': True,
        'drinks': [drink.short() for drink in Drink.query.all()]
    }), 200


'''
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''


@app.route('/drinks-detail')
@requires_auth('get:drinks-detail')
def get_drinks_detail(payload):
    return jsonify({
        'success': True,
        'drinks': [drink.long() for drink in Drink.query.all()]
    }), 200


'''
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
'''


@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def add_new_drink(payload):
    # Check if the request is valid
    if not request.is_json:
        abort(400)

    # Get the request data
    req_data = request.get_json()

    # Check if the request data is valid
    if not ('title' in req_data and 'recipe' in req_data):
        abort(400)

    # Create a new drink
    new_drink = Drink(title=req_data['title'],
                      recipe=json.dumps(req_data['recipe']))

    # Try to insert the drink into the database
    try:
        new_drink.insert()
    except:
        abort(422)

    # Return the new drink
    return jsonify({
        'success': True,
        'drinks': [new_drink.long()]
    }), 200


'''
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''


@app.route('/drinks/<int:drink_id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drink(payload, drink_id):
    # Check if the request is valid
    if not request.is_json:
        abort(400)

    # Get the request data
    req_data = request.get_json()

    # Check if the request data is valid
    if not ('title' in req_data) and not ('recipe' in req_data):
        abort(400)

    # Get the drink
    drink = Drink.query.filter(Drink.id == drink_id).one_or_none()

    # Check if the drink exists
    if not drink:
        abort(404)

    # Update the drink
    if 'title' in req_data:
        drink.title = req_data['title']
    
    if 'recipe' in req_data:
        drink.recipe = json.dumps(req_data['recipe'])

    # Try to update the drink into the database
    try:
        drink.update()
    except:
        abort(422)

    # Return the drink
    return jsonify({
        'success': True,
        'drinks':   [drink.long()]
    }), 200


'''
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''


@app.route('/drinks/<int:drink_id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(payload, drink_id):
    # Check if drink exists
    drink = Drink.query.filter(Drink.id == drink_id).one_or_none()

    # Check if the drink exists
    if not drink:
        abort(404)

    # Delete the drink
    try:
        drink.delete()
    except:
        abort(422)

    # Return the deleted drink
    return jsonify({
        'success': True,
        'delete': drink_id
    }), 200


# Error Handling
'''
Error handling for unprocessable entity
'''


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


'''
Error handling for not found entity
'''


@app.errorhandler(404)
def not_found_error(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "Route not found, {error}".format(error=error)
    }), 404


@app.errorhandler(401)
def not_authorized(error):
    return jsonify({
        "success": False,
        "error": 401,
        "message": "Something went wrong: {error}".format(error=error)
    }), 401


@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "success": False,
        "error": 500,
        "message": "Something went wrong: {error}".format(error=error)
    }), 500


@app.errorhandler(405)
def not_allowed_error(error):
    return jsonify({
        "success": False,
        "error": 405,
        "message": "Something went wrong: {error}".format(error=error)
    }), 405


'''
error handler for AuthError
    error handler should conform to general task above
'''


@app.errorhandler(AuthError)
def auth_error(error):
    if 'description' in error.error:
        message = error.error['description']
    else:
        message = error

    return jsonify({
        "success": False,
        "error": error.status_code,
        "message": message
    }), error.status_code


if __name__ == "__main__":
    app.debug = True
    app.run()
