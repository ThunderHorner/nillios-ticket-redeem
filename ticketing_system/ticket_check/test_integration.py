import requests
import json
import time

# API base URL
BASE_URL = "http://localhost:5001/api"


def register_ticket_in_nillios(ticket_id: int, owner: int):
    initial_data = requests.post(
        f"{BASE_URL}/initial",
        json={
            "ticket_id": ticket_id,
            "ticket_owner": owner,
            "is_redeemed": 0
        }
    ).json()
    print(f"Initial Registration: {json.dumps(initial_data, indent=2)}")
    return {
        'user_id': initial_data['user_id'],
        'store_id': initial_data['store_id'],
        'ticket_id': ticket_id
    }


def redeem_ticket(user_wallet: int, store_id: str, ticket_id: int):
    redeem_data = requests.post(
        f"{BASE_URL}/redeem",
        json={
            "ticket_id": ticket_id,
            "wallet_id": user_wallet,
            "is_redeemed": 1,
            "store_id": store_id
        }
    ).json()
    print(f"Redeem Response: {json.dumps(redeem_data, indent=2)}")
    return {
        'store_id': redeem_data.get('store_id'),
        'party_ids_to_store_ids': redeem_data.get('party_ids_to_store_ids')
    }


def verify_response(store_id, party_ids_to_store_ids: str):
    verify_data = requests.post(
        f"{BASE_URL}/verify",
        json={
            "store_id": store_id,
            "party_ids_to_store_ids": party_ids_to_store_ids
        }
    ).json()
    print(f"Verify Response: {json.dumps(verify_data, indent=2)}")
    return verify_data


if __name__ == "__main__":
    for i in range(1):
        try:
            # Step 1: Register ticket
            register_data = register_ticket_in_nillios(i, i + 1)  # using i+1 for owner
            time.sleep(2)

            # Step 2: Redeem ticket using the same owner ID
            redeem_data = redeem_ticket(i + 1, register_data['store_id'], i)  # using i+1 for wallet
            time.sleep(2)

            # Step 3: Verify ticket using redeem store_id
            verify_data = verify_response(redeem_data['store_id'], redeem_data['party_ids_to_store_ids'])
            time.sleep(2)

            print(f"\nTest {i} completed\n{'=' * 50}\n")

        except Exception as e:
            print(f"Error in test {i}: {str(e)}")
            continue