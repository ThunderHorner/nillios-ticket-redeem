import asyncio
import os
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


class TicketStorage:
    def __init__(self, config: NillionConfig, ticket_id, ticket_owner, is_redeemed):
        self.config = config
        self.client = create_nillion_client(
            UserKey.from_seed(config.seed),
            NodeKey.from_seed(config.seed)
        )
        self.user_id = self.client.user_id
        self.program_path = f"../nada_programs/target/{config.program_name}.nada.bin"
        self.ticket_id = ticket_id
        self.ticket_owner = ticket_owner
        self.is_redeemed = is_redeemed

    def setup_payments(self):
        payments_config = create_payments_config(self.config.chain_id, self.config.grpc_endpoint)
        payments_client = LedgerClient(payments_config)
        payments_wallet = LocalWallet(
            PrivateKey(bytes.fromhex(os.getenv("NILLION_NILCHAIN_PRIVATE_KEY_0"))),
            prefix="nillion",
        )
        return payments_client, payments_wallet

    async def store_program(self, payments_client, payments_wallet):
        print("-----STORE PROGRAM")
        receipt = await get_quote_and_pay(
            self.client,
            nillion.Operation.store_program(self.program_path),
            payments_wallet,
            payments_client,
            self.config.cluster_id,
        )

        action_id = await self.client.store_program(
            self.config.cluster_id,
            self.config.program_name,
            self.program_path,
            receipt
        )

        program_id = f"{self.user_id}/{self.config.program_name}"
        print("Stored program. action_id:", action_id)
        print("Stored program_id:", program_id)
        return program_id

    async def store_secrets(self, program_id, payments_client, payments_wallet):
        print("-----STORE SECRETS")
        secrets = {
            'ticket_id': self.ticket_id,
            'ticket_owner': self.ticket_owner,
            'is_redeemed': self.is_redeemed,
        }
        permissions = nillion.Permissions.default_for_user(self.client.user_id)
        permissions.add_compute_permissions({self.client.user_id: {program_id}})

        stored_secret = nillion.NadaValues({
            k: nillion.SecretInteger(v) for k, v in secrets.items()
        })

        receipt = await get_quote_and_pay(
            self.client,
            nillion.Operation.store_values(stored_secret, ttl_days=5),
            payments_wallet,
            payments_client,
            self.config.cluster_id,
        )

        store_id = await self.client.store_values(
            self.config.cluster_id,
            stored_secret,
            permissions,
            receipt
        )

        secrets_string = ", ".join(f"{key}: {value}" for key, value in secrets.items())
        print(f"\n🎉1️⃣ Party Issuer stored {secrets_string} at store id: {store_id}")
        return store_id

