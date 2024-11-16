from flask import Flask, jsonify, request
import subprocess
import json

app = Flask(__name__)


@app.route('/api/initial', methods=['POST'])
def initial_setup():
    try:
        data = request.get_json()
        ticket_id = data.get('ticket_id', 1)
        ticket_owner = data.get('ticket_owner', 5)
        is_redeemed = data.get('is_redeemed', 0)

        cmd = [
            'python3',
            '/app/ticketing_system/ticket_check/01_server_initial_data_set.py',
            '--ticket_id', str(ticket_id),
            '--ticket_owner', str(ticket_owner),
            '--is_redeemed', str(is_redeemed)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        # Look for user_id and store_id in the output
        user_id = None
        store_id = None

        for line in result.stdout.split('\n'):
            if '--user_id_1' in line:
                user_id = line.split('--user_id_1')[1].split('--store_id_1')[0].strip()
                store_id = line.split('--store_id_1')[1].strip()

        if user_id and store_id:
            return jsonify({
                'status': 'success',
                'user_id': user_id,
                'store_id': store_id
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'Failed to get IDs: {result.stderr}'
            }), 500

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/redeem', methods=['POST'])
def redeem_ticket():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        store_id = data.get('store_id')

        cmd = [
            'python3',
            '/app/ticketing_system/ticket_check/02_redeem_ticket.py',
            '--user_id_1', user_id,
            '--store_id_1', store_id
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        # Look for party_ids_to_store_ids in the output
        party_mapping = None
        for line in result.stdout.split('\n'):
            if '--party_ids_to_store_ids' in line:
                party_mapping = line.split('--party_ids_to_store_ids')[1].strip()

        if party_mapping:
            return jsonify({
                'status': 'success',
                'store_id': store_id,
                'party_ids_to_store_ids': party_mapping
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'Failed to get party mapping: {result.stderr}'
            }), 500

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/verify', methods=['POST'])
def verify_ticket():
    try:
        data = request.get_json()
        store_id = data.get('store_id')
        party_ids_to_store_ids = data.get('party_ids_to_store_ids')

        cmd = [
            'python3',
            '/app/ticketing_system/ticket_check/03_multi_party_compute.py',
            '--store_id_1', store_id,
            '--party_ids_to_store_ids', party_ids_to_store_ids
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        return jsonify({
            'status': 'success',
            'result': result.stdout,
            'store_id': store_id,
            'party_ids_to_store_ids': party_ids_to_store_ids
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


if __name__ == '__main__':
    app.run(debug=True)