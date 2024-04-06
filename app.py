import json

from flask import Flask, send_file, request

import dbmanager
import utils
from data import CampusAccount, RolesManager

app = Flask(__name__)


@app.route('/campus/api/v1/health', methods=["GET"])
def health():
    return json.dumps({"status": "OK"})


@app.route('/campus/api/v1/login', methods=["POST"])
def login():
    data = request.json
    email = data.get('email')
    password_raw = data.get('password_raw')
    ip_address = request.remote_addr
    user_agent = request.user_agent.string

    if not dbmanager.account_exists(email):
        return (json.dumps({'message': 'account does not exist'}), 404, {
            'message': 'account does not exist'
        })
    result = CampusAccount.login(email, password_raw, ip_address, user_agent)
    if isinstance(result, utils.OpStatus):
        return (json.dumps({'message': result.message}), 400, {
            'message': result.message
        })
    return (json.dumps({'api_key': result}), 200, {'message': 'OK'})


@app.route('/campus/api/v1/register', methods=["POST"])
def register():
    data = request.json
    email = data.get('email')
    first_name = data.get('first_name')
    second_name = data.get('second_name')
    third_name = data.get('third_name')
    university = int(data.get('university'))
    password_raw = data.get('password_raw')
    ip_address = request.remote_addr
    user_agent = request.user_agent.string

    if dbmanager.account_exists(email):
        return (json.dumps({'message': 'account already exists'}), 409, {
            'message': 'account already exists'
        })
    result = CampusAccount.register(first_name, second_name, third_name, email, password_raw, university,
                                    ip_address, user_agent)
    if isinstance(result, utils.OpStatus):
        return (json.dumps({'message': result.message}), 400, {
            'message': result.message
        })
    else:
        return (json.dumps({'api_key': result}), 200, {
            'message': 'OK'
        })


# @app.route('/campus/api/v1/my_sessions', methods=["POST"])
# def get_sessions():
#     pass

@app.route('/campus/api/v1/set_my_profile_info', methods=["POST"])
def set_user_profile():
    data = request.json
    api_key = data.get('api_key')
    email = data.get('email')
    first_name = data.get('first_name')
    second_name = data.get('second_name')
    third_name = data.get('third_name')
    university = int(data.get('university'))

    if email is not None and not utils.email_is_valid(email):
        return (json.dumps({'message': "invalid email"}), 400, {
            'message': "invalid email"
        })

    account = CampusAccount.get_from_api_key(api_key)
    if account is None:
        return (json.dumps({'message': "account not found"}), 400, {
            'message': "account not found"
        })
    else:
        account.edit(first_name, second_name, third_name, email, university)
        return (json.dumps({'message': "OK"}), 200, {
            'message': "OK"
        })


@app.route('/campus/api/v1/get_user_profile', methods=["POST"])
def get_user_profile():
    data = request.json
    user_id = data.get('user_id')
    api_key = data.get('api_key')
    as_role = data.get('as_role')

    by_account = CampusAccount.get_from_api_key(api_key)
    if by_account is not None:
        if RolesManager.validate_role(as_role) and by_account.get_role_name() == as_role:
            target_account = CampusAccount.get_by_id(user_id)
            if target_account is None:
                return (json.dumps({'message': "account not found"}), 400, {
                    'message': "account not found"
                })
            else:
                return target_account.get_info_json_as(as_role)
        else:
            return (json.dumps({'message': "invalid role"}), 400, {
                'message': "invalid role"
            })
    else:
        return (json.dumps({'message': "account not found"}), 400, {
            'message': "account not found"
        })


@app.route('/campus/api/v1/get_my_profile', methods=["POST"])
def get_my_profile():
    data = request.json
    api_key = data.get('api_key')
    account = CampusAccount.get_from_api_key(api_key)
    if account is None:
        return 200
    return account.account_info_json_self()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
