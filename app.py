from flask import Flask, request, jsonify, send_from_directory
import os
import requests
import time

app = Flask(__name__)

AUTHORIZED_USERS_FILE = 'authorized_users.txt'
AUTHORIZED_USER_IDS = set()
ADMIN_USER_IDS = [6905993209]

def load_authorized_users():
    if os.path.exists(AUTHORIZED_USERS_FILE):
        with open(AUTHORIZED_USERS_FILE, 'r') as file:
            return set(map(int, file.read().splitlines()))
    return set()

def save_authorized_users():
    with open(AUTHORIZED_USERS_FILE, 'w') as file:
        file.write('\n'.join(map(str, AUTHORIZED_USER_IDS)))

AUTHORIZED_USER_IDS = load_authorized_users()

@app.route('/')
def index():
    return send_from_directory('templates', 'index.html')

@app.route('/phone_number_form')
def phone_number_form():
    return send_from_directory('templates', 'phone_number_form.html')

@app.route('/success')
def success():
    return send_from_directory('templates', 'success.html')

@app.route('/phone_number', methods=['POST'])
def phone_number():
    data = request.json
    phone_number = data.get('phone_number')

    max_attempts = 3
    attempt = 0

    while attempt < max_attempts:
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Host': 'ibiza.ooredoo.dz',
            'Connection': 'Keep-Alive',
            'User-Agent': 'okhttp/4.9.3',
        }

        data = {
            'client_id': 'ibiza-app',
            'grant_type': 'password',
            'mobile-number': phone_number,
            'language': 'AR',
        }

        response = requests.post('https://ibiza.ooredoo.dz/auth/realms/ibiza/protocol/openid-connect/token', headers=headers, data=data)

        if 'ROOGY' in response.text:
            return jsonify({'status': 'success', 'message': 'OTP code sent. Enter OTP:'})
        else:
            attempt += 1
            if attempt < max_attempts:
                continue
            else:
                return jsonify({'status': 'error', 'message': 'Failed to verify phone number after {} attempts.'.format(max_attempts)}), 500

@app.route('/verify_otp', methods=['POST'])
def verify_otp():
    data = request.json
    phone_number = data.get('phone_number')
    otp = data.get('otp')

    max_attempts = 3
    attempt = 0

    while attempt < max_attempts:
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Host': 'ibiza.ooredoo.dz',
            'Connection': 'Keep-Alive',
            'User-Agent': 'okhttp/4.9.3',
        }

        data = {
            'client_id': 'ibiza-app',
            'otp': otp,
            'grant_type': 'password',
            'mobile-number': phone_number,
            'language': 'AR',
        }

        response = requests.post('https://ibiza.ooredoo.dz/auth/realms/ibiza/protocol/openid-connect/token', headers=headers, data=data)

        access_token = response.json().get('access_token')
        if access_token:
            url = 'https://ibiza.ooredoo.dz/api/v1/mobile-bff/users/mgm/info/apply'

            headers = {
                'Authorization': f'Bearer {access_token}',
                'language': 'AR',
                'request-id': 'ef69f4c6-2ead-4b93-95df-106ef37feefd',
                'flavour-type': 'gms',
                'Content-Type': 'application/json'
            }

            payload = {
                "mgmValue": "ABC"
            }

            counter = 0
            while counter < 12:
                response = requests.post(url, headers=headers, json=payload)

                if 'EU1002' in response.text:
                    return jsonify({'status': 'success', 'message': 'تم ارسال الانترنيت'})
                else:
                    counter += 1
                    time.sleep(5)

            return jsonify({'status': 'error', 'message': 'Failed to apply internet after 12 attempts.'}), 500
        else:
            attempt += 1
            if attempt < max_attempts:
                continue
            else:
                return jsonify({'status': 'error', 'message': 'Failed to verify OTP after {} attempts.'.format(max_attempts)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
    