import asyncio
import os
import argparse
from dataclasses import dataclass
import py_nillion_client as nillion
from py_nillion_client import NodeKey, UserKey
from dotenv import load_dotenv
from cosmpy.aerial.client import LedgerClient
from cosmpy.aerial.wallet import LocalWallet
from cosmpy.crypto.keypairs import PrivateKey
from nillion_python_helpers import get_quote_and_pay, create_nillion_client, create_payments_config
import pytest


@dataclass
class NillionConfig:
    cluster_id: str
    grpc_endpoint: str
    chain_id: str
    program_name: str = 'ticket_check'
    seed: str = "seed"

    @classmethod
    def from_env(cls):
        home = os.getenv("HOME")
        load_dotenv(f"{home}/.config/nillion/nillion-devnet.env")
        return cls(
            cluster_id=os.getenv("NILLION_CLUSTER_ID"),
            grpc_endpoint=os.getenv("NILLION_NILCHAIN_GRPC"),
            chain_id=os.getenv("NILLION_NILCHAIN_CHAIN_ID")
        )


class TicketRedemption:
    def __init__(self, config: NillionConfig, user_ticket, user_wallet):
        self.config = config
        self.user_ticket = user_ticket
        self.user_wallet = user_wallet

        # Initialize client
        self.client = create_nillion_client(
            UserKey.from_seed(config.seed),
            NodeKey.from_seed(config.seed)
        )

        # Get IDs from client
        self.user_id = self.client.user_id
        self.party_id = self.client.party_id  # This should be set now

        # Single store_id instead of lists
        self.store_id = None

        print(f"Initialized with User ID: {self.user_id}")
        print(f"Initialized with Party ID: {self.party_id}")

    def setup_payments(self):
        payments_config = create_payments_config(self.config.chain_id, self.config.grpc_endpoint)
        payments_client = LedgerClient(payments_config)
        payments_wallet = LocalWallet(
            PrivateKey(bytes.fromhex(os.getenv("NILLION_NILCHAIN_PRIVATE_KEY_0"))),
            prefix="nillion",
        )
        return payments_client, payments_wallet

    async def store_user_secrets(self, issuer_user_id: str, payments_client, payments_wallet):
        try:
            program_id = f"{issuer_user_id}/{self.config.program_name}"
            print(f"Using program ID: {program_id}")

            # Create secrets
            secrets = {
                'user_ticket': self.user_ticket,
                'user_wallet': self.user_wallet,
                'user_redeem': 1,
            }
            print(f"Created secrets: {secrets}")

            # Create stored secret
            stored_secret = nillion.NadaValues({
                k: nillion.SecretInteger(v) for k, v in secrets.items()
            })

            # Get quote and pay
            receipt = await get_quote_and_pay(
                self.client,
                nillion.Operation.store_values(stored_secret, ttl_days=5),
                payments_wallet,
                payments_client,
                self.config.cluster_id,
            )
            print("Payment completed")

            # Setup permissions
            permissions = nillion.Permissions.default_for_user(self.user_id)
            compute_permissions = {issuer_user_id: {program_id}}
            permissions.add_compute_permissions(compute_permissions)
            print(f"Permissions set for user: {issuer_user_id}")

            # Store values
            store_id = await self.client.store_values(
                self.config.cluster_id,
                stored_secret,
                permissions,
                receipt
            )
            print(f"Received store_id: {store_id}")

            # Store the single store_id
            self.store_id = store_id

            # Create the party_id:store_id string directly
            party_store_mapping = f"{self.party_id}:{self.store_id}"
            print(f"\n🎉 Storage successful:")
            print(f"Store ID: {self.store_id}")
            print(f"Party ID: {self.party_id}")
            print(f"Mapping: {party_store_mapping}")
            print(f"Compute permission granted to: {issuer_user_id}")

            return store_id, party_store_mapping

        except Exception as e:
            print(f"Error in store_user_secrets: {str(e)}")
            raise