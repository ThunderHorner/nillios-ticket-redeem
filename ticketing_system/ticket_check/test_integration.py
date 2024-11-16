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

        return {
            'user_id': initial_data['user_id'],
            'store_id': initial_data['store_id']
        }

    except Exception as e:
        print(f"\n❌ Registration failed: {e}")
        raise


def redeem_ticket(user_id: str, store_id: str, ticket_id: int, wallet_id: int):
    """Redeem a ticket using passed parameters"""
    try:
        print("\n2. Redeem Ticket...")
        redeem_response = requests.post(
            f"{BASE_URL}/redeem",
            json={
                "user_id": user_id,
                "store_id": store_id,
                "ticket_id": ticket_id,
                "wallet_id": wallet_id
            }
        )
        redeem_data = redeem_response.json()
        print(f"Redeem Response: {json.dumps(redeem_data, indent=2)}")

        if redeem_data['status'] != 'success':
            raise Exception(f"Redemption failed: {redeem_data.get('message')}")

        return {
            'store_id': redeem_data['store_id'],
            'party_ids_to_store_ids': redeem_data['party_ids_to_store_ids']
        }

    except Exception as e:
        print(f"\n❌ Redemption failed: {e}")
        raise


def verify_ticket(store_id: str, party_ids_to_store_ids: str):
    """Verify a ticket using passed parameters"""
    try:
        print("\n3. Verify Ticket...")
        verify_response = requests.post(
            f"{BASE_URL}/verify",
            json={
                "store_id": store_id,
                "party_ids_to_store_ids": party_ids_to_store_ids
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
            ticket_id = random.randint(1, 10000)
            wallet_id = random.randint(1, 10000)

            # Step 1: Register ticket
            reg_data = register_ticket(ticket_id, wallet_id)
            time.sleep(2)

            # Step 2: Redeem ticket
            redeem_data = redeem_ticket(
                user_id=reg_data['user_id'],
                store_id=reg_data['store_id'],
                ticket_id=ticket_id,
                wallet_id=wallet_id
            )
            time.sleep(2)

            # Step 3: Verify ticket
            verify_data = verify_ticket(
                store_id=redeem_data['store_id'],
                party_ids_to_store_ids=redeem_data['party_ids_to_store_ids']
            )

            assert verify_data['result']["status"] == 1, "Verification failed"
            print(f"\n✅ Test {i + 1} completed successfully!")

        except Exception as e:
            print(f"\n❌ Test {i + 1} failed: {e}")
            raise