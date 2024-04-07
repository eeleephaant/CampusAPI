import json
from datetime import datetime

from flask import Flask, request

import dbmanager
import utils
from data import CampusAccount, RolesManager, EventsManager, Event, IndicatorsManager, Indicator, UniversityManager

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
    return (json.dumps({'api_key': result}),
            200,
            {'message': 'OK'})


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
@app.route('/campus/api/v1/edit_event', methods=["POST"])
def edit_event():
    data = request.json
    image = request.files['image']
    api_key = data.get('api_key')
    address = data.get('address')
    event_id = data.get('event_id')
    indicators_raw_list = data.get('indicators')
    title = data.get('title')
    description = data.get('description')
    start_date = data.get('start_date')

    indicators_list: list = None

    if start_date is not None:
        start_date = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S")

    if indicators_raw_list is not None:
        if indicators_raw_list is not list:
            return (json.dumps({'message': "indicators must be a list"}), 400, {
                'message': "indicators must be a list"
            })
        else:
            for indicator_id in indicators_raw_list:
                indicators_list.append(Indicator.get_by_id(indicator_id))

    account = CampusAccount.get_from_api_key(api_key)
    if account is None:
        return (json.dumps({'message': "account not found"}), 400, {
            'message': "account not found"
        })
    else:
        event = Event.get_by_id(event_id)
        if event is None:
            return (json.dumps({'message': "event not found"}), 400, {
                'message': "event not found"
            })
        if account.role_id == 3 or event.organizer_id == account.user_id:
            image_path = None
            if image is not None:
                image_path = f'./images/events_photos/{title}'
                image.save(image_path)
            EventsManager.edit_event(event_id, title, description, start_date, address, image_path, indicators_list)
            return (json.dumps({'message': "OK"}), 200, {
                'message': "OK"
            })
        else:
            return (json.dumps({'message': "you don't have permission"}), 400, {
                'message': "you don't have permission"
            })


@app.route('/campus/api/v1/get_event_list', methods=["POST"])
def get_event_list():
    data = request.json
    api_key = data.get('api_key')

    account = CampusAccount.get_from_api_key(api_key)
    if account is None:
        return (json.dumps({'message': "account not found"}), 400, {
            'message': "account not found"
        })
    else:
        result = EventsManager.get_event_list_as_json()
        return (result, 200, {
            'message': "OK"
        })


@app.route('/campus/api/v1/get_all_indicators', methods=["POST"])
def get_all_indicators():
    data = request.json
    api_key = data.get('api_key')

    account = CampusAccount.get_from_api_key(api_key)
    if account is None:
        return (json.dumps({'message': "account not found"}), 400, {
            'message': "account not found"
        })
    else:
        result = IndicatorsManager.get_all_indicators_as_json()
        return (result, 200, {
            'message': "OK"
        })


@app.route('/campus/api/v1/get_event', methods=["POST"])
def get_event():
    data = request.json
    api_key = data.get('api_key')
    event_id = data.get('event_id')

    account = CampusAccount.get_from_api_key(api_key)
    if account is None:
        return (json.dumps({'message': "account not found"}), 400, {
            'message': "account not found"
        })
    else:
        if account.role_id == 3 or account.role_id == 2:
            result = Event.get_by_id(event_id)
            return (result.get_json_info(), 200, {
                'message': "OK"
            })
        else:
            return (json.dumps({'message': "you don't have permission"}), 400, {
                'message': "you don't have permission"
            })


@app.route('/campus/api/v1/get_suggested_events', methods=["POST"])
def get_suggested_events():
    data = request.json
    api_key = data.get('api_key')

    account = CampusAccount.get_from_api_key(api_key)
    if account is None:
        return (json.dumps({'message': "account not found"}), 400, {
            'message': "account not found"
        })
    else:
        event_list = account.get_suggested_events()
        return (json.dumps({"events": [{"event.id": event.event_id} for event in event_list]}), 200, {
            'message': "OK"
        })


# @app.route('/campus/api/v1/load_test_results', methods=["POST"])
# def load_test_results():
#     data = request.json
#     api_key = data.get('api_key')
#     test_results = data.get('test_results')
#     if test_results is not dict:
#         return (json.dumps({'message': "test_results must be a json object"}), 400, {
#             'message': "test_results must be a json object"
#         })
#
#     test_type_id = int(test_results["test_type_id"])
#
#
#
#     account = CampusAccount.get_from_api_key(api_key)
#     if account is None:
#         return (json.dumps({'message': "account not found"}), 400, {
#             'message': "account not found"
#         })
#     else:
#         result = EventsManager.load_test_results()
#         return (result, 200, {
#             'message': "OK"
#         })


@app.route('/campus/api/v1/add_event', methods=["POST"])
def add_event():
    data = request.json
    image = request.files['image']
    api_key = data.get('api_key')
    address = data.get('address')
    title = data.get('title')
    description = data.get('description')
    start_date = data.get('start_date')

    account = CampusAccount.get_from_api_key(api_key)
    if account is None:
        return (json.dumps({'message': "account not found"}), 400, {
            'message': "account not found"
        })
    else:
        if account.role_id == 3:
            image_path = f'./images/events_photos/{title}'
            image.save(image_path)
            EventsManager.add_event(title, description, start_date, address, image_path, account.user_id)
            return (json.dumps({'message': "OK"}), 200, {
                'message': "OK"
            })
        else:
            return (json.dumps({'message': "you don't have permission"}), 400, {
                'message': "you don't have permission"
            })


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


@app.route('/campus/api/v1/users/set_indicators', methods=["POST"])
def set_indicators():
    data = request.json
    user_id = data.get('user_id')
    api_key = data.get('api_key')
    indicators_raw_list = data.get('indicators')

    indicators_list: list = None

    if indicators_raw_list is not None:
        if indicators_raw_list is not list:
            return (json.dumps({'message': "indicators must be a list"}), 400, {
                'message': "indicators must be a list"
            })
        else:
            for indicator_id in indicators_raw_list:
                indicators_list.append(Indicator.get_by_id(indicator_id))
    else:
        return (json.dumps({'message': "indicators must be"}), 400, {
            'message': "indicators must be"
        })

    by_account = CampusAccount.get_from_api_key(api_key)
    target_account = CampusAccount.get_by_id(user_id)

    if by_account is not None and target_account is not None:
        if target_account.role_id == 3:
            target_account.set_indicators(indicators_list)
            return (json.dumps({'message': "OK"}), 200, {
                'message': "OK"
            })
        else:
            return (json.dumps({'message': "you don't have permission"}), 400, {
                'message': "you don't have permission"
            })


@app.route('/campus/api/v1/users/get_profile', methods=["POST"])
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
        return (json.dumps({'message': "account not found"}), 400, {
            'message': "account not found"
        })
    return (account.account_info_json_self(), 200, {
        'message': "OK"
    })


@app.route('/campus/api/v1/get_all_universities', methods=["POST"])
def get_all_universities():
    data = request.json
    api_key = data.get('api_key')

    account = CampusAccount.get_from_api_key(api_key)
    if account is None:
        return (json.dumps({'message': "account not found"}), 400, {
            'message': "account not found"
        })
    else:
        result = UniversityManager.get_all_universities_as_json()
        return (result, 200, {
            'message': "OK"
        })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
