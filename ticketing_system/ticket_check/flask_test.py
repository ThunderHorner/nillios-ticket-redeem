# test_api.py
import requests
import json
import time
from typing import Dict, Any


class TicketAPITester:
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = {}

    def initial_setup(self, ticket_id: int = 123, ticket_owner: int = 456) -> Dict[str, Any]:
        """
        Test the initial setup endpoint
        """
        print("\n1. Testing Initial Setup...")
        endpoint = f"{self.base_url}/api/initial"
        payload = {
            "ticket_id": ticket_id,
            "ticket_owner": ticket_owner,
            "is_redeemed": 0
        }

        response = self.session.post(endpoint, json=payload)
        result = response.json()

        print(f"Initial Setup Response: {json.dumps(result, indent=2)}")

        if response.status_code == 200 and result['status'] == 'success':
            self.results['user_id'] = result['user_id']
            self.results['store_id'] = result['store_id']
            return result
        else:
            raise Exception(f"Initial setup failed: {result}")

    def redeem_ticket(self, user_ticket: int = 123, user_wallet: int = 456) -> Dict[str, Any]:
        """
        Test the redeem ticket endpoint using results from initial setup
        """
        print("\n2. Testing Ticket Redemption...")
        if not all(k in self.results for k in ['user_id', 'store_id']):
            raise Exception("Missing required data from initial setup")

        endpoint = f"{self.base_url}/api/redeem/{self.results['user_id']}/{self.results['store_id']}"
        payload = {
            "user_ticket": user_ticket,
            "user_wallet": user_wallet
        }

        response = self.session.post(endpoint, json=payload)
        result = response.json()

        print(f"Redeem Ticket Response: {json.dumps(result, indent=2)}")

        if response.status_code == 200 and result['status'] == 'success':
            self.results['party_ids_to_store_ids'] = result['party_ids_to_store_ids']
            return result
        else:
            raise Exception(f"Ticket redemption failed: {result}")

    def verify_ticket(self) -> Dict[str, Any]:
        """
        Test the verify ticket endpoint using results from redemption
        """
        print("\n3. Testing Ticket Verification...")
        if not all(k in self.results for k in ['store_id', 'party_ids_to_store_ids']):
            raise Exception("Missing required data from ticket redemption")

        endpoint = f"{self.base_url}/api/verify/{self.results['store_id']}/{self.results['party_ids_to_store_ids']}"

        response = self.session.post(endpoint)
        result = response.json()

        print(f"Verify Ticket Response: {json.dumps(result, indent=2)}")

        if response.status_code == 200 and result['status'] == 'success':
            return result
        else:
            raise Exception(f"Ticket verification failed: {result}")

    def run_full_test(self, ticket_id: int = 123, ticket_owner: int = 456) -> Dict[str, Any]:
        """
        Run all tests in sequence
        """
        try:
            print("Starting Full Test Sequence...")
            print("=" * 50)

            # Step 1: Initial Setup
            initial_result = self.initial_setup(ticket_id, ticket_owner)
            print("\nInitial Setup Successful!")
            print(f"User ID: {self.results['user_id']}")
            print(f"Store ID: {self.results['store_id']}")

            # Small delay between requests
            time.sleep(5)

            # Step 2: Redeem Ticket
            redeem_result = self.redeem_ticket(ticket_id, ticket_owner)
            print("\nTicket Redemption Successful!")
            print(f"Party IDs to Store IDs: {self.results['party_ids_to_store_ids']}")

            time.sleep(5)

            # Step 3: Verify Ticket
            verify_result = self.verify_ticket()
            print("\nTicket Verification Successful!")
            print(f"Computation Result: {verify_result.get('computation_result')}")

            print("\nFull Test Sequence Completed Successfully!")
            print("=" * 50)

            return {
                "initial": initial_result,
                "redeem": redeem_result,
                "verify": verify_result
            }

        except Exception as e:
            print(f"\n❌ Test sequence failed: {str(e)}")
            raise


if __name__ == "__main__":
    # Create tester instance
    tester = TicketAPITester()

    try:
        # Run the full test sequence with custom ticket values
        results = tester.run_full_test(
            ticket_id=789,
            ticket_owner=101112
        )
    except Exception as e:
        print(f"\nTest sequence failed: {e}")