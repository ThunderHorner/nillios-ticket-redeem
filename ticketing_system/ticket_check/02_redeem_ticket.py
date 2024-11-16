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
    def __init__(self, config: NillionConfig,user_ticket, user_wallet):
        self.config = config
        self.user_ticket = int(user_ticket)
        self.user_wallet = int(user_wallet)
        self.client = create_nillion_client(
            UserKey.from_seed(config.seed),
            NodeKey.from_seed(config.seed)
        )
        self.user_id = self.client.user_id
        self.party_id = self.client.party_id
        self.store_ids = []
        self.party_ids = []

    def setup_payments(self):
        payments_config = create_payments_config(self.config.chain_id, self.config.grpc_endpoint)
        payments_client = LedgerClient(payments_config)
        payments_wallet = LocalWallet(
            PrivateKey(bytes.fromhex(os.getenv("NILLION_NILCHAIN_PRIVATE_KEY_0"))),
            prefix="nillion",
        )
        return payments_client, payments_wallet

    async def store_user_secrets(self, issuer_user_id: str, payments_client, payments_wallet):
        program_id = f"{issuer_user_id}/{self.config.program_name}"

        secrets = {
            'user_ticket': self.user_ticket,
            'user_wallet': self.user_wallet,
            'user_redeem': 1,
        }

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

        permissions = nillion.Permissions.default_for_user(self.user_id)
        compute_permissions = {issuer_user_id: {program_id}}
        permissions.add_compute_permissions(compute_permissions)

        store_id = await self.client.store_values(
            self.config.cluster_id,
            stored_secret,
            permissions,
            receipt
        )

        self.store_ids.append(store_id)
        self.party_ids.append(self.party_id)

        print(f"\n🎉N Party User stored {secrets} at store id: {store_id}")
        print(f"\n🎉Compute permission on the secret granted to user_id: {issuer_user_id}")

        return store_id


def parse_args(args=None):
    parser = argparse.ArgumentParser(
        description="Create a secret on the Nillion network with set read/retrieve permissions"
    )
    parser.add_argument(
        "--ticket_id",
        required=True,
        type=str,
        help="User ID of the user who will compute with the secret being stored",
    )
    parser.add_argument(
        "--user_id_1",
        required=True,
        type=str,
        help="User ID of the user who will compute with the secret being stored",
    )
    parser.add_argument(
        "--wallet_id",
        required=True,
        type=str,
        help="User ID of the user who will compute with the secret being stored",
    )
    parser.add_argument(
        "--store_id_1",
        required=True,
        type=str,
        help="Store ID of the 1st secret",
    )
    return parser.parse_args(args)


async def main(args=None):
    parsed_args = parse_args(args)
    config = NillionConfig.from_env()
    redemption = TicketRedemption(config, parsed_args.ticket_id, parsed_args.wallet_id )

    payments_client, payments_wallet = redemption.setup_payments()
    store_id = await redemption.store_user_secrets(
        parsed_args.user_id_1,
        payments_client,
        payments_wallet
    )

    party_ids_to_store_ids = " ".join(
        [f"{party_id}:{store_id}" for party_id, store_id in zip(redemption.party_ids, redemption.store_ids)]
    )

    print("\n📋⬇️ Copy and run the following command to run multi party computation using the secrets")
    print(
        f"\npython3 03_multi_party_compute.py --store_id_1 {parsed_args.store_id_1} "
        f"--party_ids_to_store_ids {party_ids_to_store_ids}"
    )

    return [parsed_args.store_id_1, party_ids_to_store_ids]


if __name__ == "__main__":
    asyncio.run(main())


@pytest.mark.asyncio
async def test_main():
    pass