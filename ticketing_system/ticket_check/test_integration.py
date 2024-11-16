import random

import requests
import json
import time

# API base URL
BASE_URL = "http://localhost:5001/api"


def register_ticket(ticket_id: int, wallet_id: int):
    """Register a new ticket and return the registration data"""
    try:
        print("\n1. Initial Setup...")
        initial_response = requests.post(
            f"{BASE_URL}/initial",
            json={
                "ticket_id": ticket_id,
                "ticket_owner": wallet_id,
                "is_redeemed": 0
            }
        )
        initial_data = initial_response.json()
        print(f"Initial Response: {json.dumps(initial_data, indent=2)}")

        if initial_data['status'] != 'success':
            raise Exception(f"Initial setup failed: {initial_data.get('message')}")

        return initial_data

    except Exception as e:
        print(f"\n❌ Registration failed: {e}")
        raise


def redeem_ticket(initial_data: dict, ticket_id: int, wallet_id: int):
    """Redeem a ticket using the initial registration data"""
    try:
        print("\n2. Redeem Ticket...")
        redeem_response = requests.post(
            f"{BASE_URL}/redeem",
            json={
                "user_id": initial_data['user_id'],
                "store_id": initial_data['store_id'],
                "ticket_id": ticket_id,
                "wallet_id": wallet_id
            }
        )
        redeem_data = redeem_response.json()
        print(f"Redeem Response: {json.dumps(redeem_data, indent=2)}")

        if redeem_data['status'] != 'success':
            raise Exception(f"Redemption failed: {redeem_data.get('message')}")

        return redeem_data

    except Exception as e:
        print(f"\n❌ Redemption failed: {e}")
        raise


def verify_ticket(redeem_data: dict):
    """Verify a ticket using the redemption data"""
    try:
        print("\n3. Verify Ticket...")
        verify_response = requests.post(
            f"{BASE_URL}/verify",
            json={
                "store_id": redeem_data['store_id'],
                "party_ids_to_store_ids": redeem_data['party_ids_to_store_ids']
            }
        )
        verify_data = verify_response.json()
        print(f"Verify Response: {json.dumps(verify_data, indent=2)}")

        if verify_data['status'] != 'success':
            raise Exception(f"Verification failed: {verify_data.get('message')}")

        return verify_data

    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        raise


if __name__ == "__main__":
    for i in range(200):
        try:
            TICKET_ID = random.randint(1, 10000)
            WALLET_ID = random.randint(1, 10000)

            # Step 1: Register ticket
            initial_data = register_ticket(TICKET_ID, WALLET_ID)
            time.sleep(2)  # Small delay between requests

            # Step 2: Redeem ticket
            redeem_data = redeem_ticket(initial_data, TICKET_ID, WALLET_ID)
            time.sleep(2)  # Small delay between requests

            # Step 3: Verify ticket
            verify_data = verify_ticket(redeem_data)
            assert verify_data['result']["status"] == 1, f"Verification failed"
            print("\n✅ All tests completed successfully!")

        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            raise