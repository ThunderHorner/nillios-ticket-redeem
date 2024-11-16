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
            '01_server_initial_data_set.py',
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
                'cmd': ' '.join(cmd),
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
        ticket_id = data.get('ticket_id')
        wallet_id = data.get('wallet_id')

        cmd = [
            'python3',
            '02_redeem_ticket.py',
            '--ticket_id', str(ticket_id),
            '--user_id_1', str(user_id),
            '--wallet_id', str(wallet_id),
            '--store_id_1', str(store_id)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        # Look for party_ids_to_store_ids in the output
        party_mapping = None
        for line in result.stdout.split('\n'):
            if '--party_ids_to_store_ids' in line:
                party_mapping = line.split('--party_ids_to_store_ids')[1].strip()

        if party_mapping:
            return jsonify({
                'cmd': ' '.join(cmd),
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
            '03_multi_party_compute.py',
            '--store_id_1', store_id,
            '--party_ids_to_store_ids', party_ids_to_store_ids
        ]
        print(cmd)
        print(cmd)
        print(cmd)
        print(cmd)
        print(cmd)

        result = subprocess.run(cmd, capture_output=True, text=True)

        return jsonify({
            'cmd': ' '.join(cmd),
            'status': 'success',
            'result':result.stdout,
            'store_id': store_id,
            'party_ids_to_store_ids': party_ids_to_store_ids
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


if __name__ == '__main__':
    app.run(debug=True, port=5001)