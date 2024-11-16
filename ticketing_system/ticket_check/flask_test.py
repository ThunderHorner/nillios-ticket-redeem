# test_api.py
import requests
import json
import time

# API base URL
BASE_URL = "http://localhost:5001/api"

try:
    # Step 1: Initial Setup
    print("\n1. Initial Setup...")
    initial_response = requests.post(
        f"{BASE_URL}/initial",
        json={
            "ticket_id": 2,
            "ticket_owner": 8,
            "is_redeemed": 0
        }
    )
    initial_data = initial_response.json()
    print(f"Initial Response: {json.dumps(initial_data, indent=2)}")

    if initial_data['status'] != 'success':
        raise Exception(f"Initial setup failed: {initial_data.get('message')}")

    time.sleep(2)  # Small delay between requests

    # Step 2: Redeem Ticket using data from initial response
    print("\n2. Redeem Ticket...")
    redeem_response = requests.post(
        f"{BASE_URL}/redeem",
        json={
            "user_id": initial_data['user_id'],
            "store_id": initial_data['store_id'],
            "ticket_id":2,
            "wallet_id":8

        }
    )
    redeem_data = redeem_response.json()
    print(f"Redeem Response: {json.dumps(redeem_data, indent=2)}")

    if redeem_data['status'] != 'success':
        raise Exception(f"Redemption failed: {redeem_data.get('message')}")

    time.sleep(2)  # Small delay between requests

    # Step 3: Verify Ticket using data from redeem response
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

    print("\n✅ All tests completed successfully!")

except Exception as e:
    print(f"\n❌ Test failed: {e}")
    raise

if __name__ == "__main__":
    pass