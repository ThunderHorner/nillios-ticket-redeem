# app.py
from flask import Flask, jsonify, request
import asyncio
from ticket_storage import TicketStorage, NillionConfig
from ticket_redemption import TicketRedemption
from ticket_computation import TicketComputation

app = Flask(__name__)

# Initialize config
config = NillionConfig.from_env()


@app.route('/api/initial', methods=['POST'])
def initial_setup():
    try:
        # Get parameters from request JSON
        data = request.get_json()
        ticket_id = data.get('ticket_id', 1)  # default to 1 if not provided
        ticket_owner = data.get('ticket_owner', 5)  # default to 5 if not provided
        is_redeemed = data.get('is_redeemed', 0)  # default to 0 if not provided

        # Create event loop for async operations
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Initialize storage with provided values
        storage = TicketStorage(config, ticket_id=ticket_id, ticket_owner=ticket_owner, is_redeemed=is_redeemed)
        payments_client, payments_wallet = storage.setup_payments()

        # Run async operations
        program_id = loop.run_until_complete(storage.store_program(payments_client, payments_wallet))
        store_id = loop.run_until_complete(storage.store_secrets(program_id, payments_client, payments_wallet))

        return jsonify({
            'status': 'success',
            'user_id': storage.user_id,
            'store_id': store_id,
            'ticket_details': {
                'ticket_id': ticket_id,
                'ticket_owner': ticket_owner,
                'is_redeemed': is_redeemed
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/redeem/<user_id>/<store_id>', methods=['POST'])
def redeem_ticket(user_id, store_id):
    try:
        # Get parameters from request JSON
        data = request.get_json()
        user_ticket = data.get('user_ticket', 1)  # default to 1 if not provided
        user_wallet = data.get('user_wallet', 5)  # default to 5 if not provided

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Initialize redemption with provided values
        redemption = TicketRedemption(config, user_ticket=user_ticket, user_wallet=user_wallet)
        payments_client, payments_wallet = redemption.setup_payments()

        # Store user secrets
        store_id_result = loop.run_until_complete(
            redemption.store_user_secrets(user_id, payments_client, payments_wallet)
        )

        party_ids_to_store_ids = " ".join(
            [f"{party_id}:{store_id}" for party_id, store_id in zip(redemption.party_ids, redemption.store_ids)]
        )

        return jsonify({
            'status': 'success',
            'store_id_1': store_id,
            'party_ids_to_store_ids': party_ids_to_store_ids,
            'ticket_details': {
                'user_ticket': user_ticket,
                'user_wallet': user_wallet
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/verify/<store_id>/<party_store_ids>', methods=['POST'])
def verify_ticket(store_id, party_store_ids):
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        computation = TicketComputation(config)
        payments_client, payments_wallet = computation.setup_payments()

        # Parse party_store_ids string into list
        party_store_list = party_store_ids.split()
        party_store_mapping = computation.parse_party_store_ids(party_store_list)

        result = loop.run_until_complete(
            computation.perform_computation(
                store_id,
                party_store_mapping,
                payments_client,
                payments_wallet
            )
        )

        return jsonify({
            'status': 'success',
            'computation_result': result
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


if __name__ == '__main__':
    app.run(debug=True)