import asyncio
import os
import argparse
from dataclasses import dataclass
from typing import Dict, List
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


class TicketComputation:
    def __init__(self, config: NillionConfig):
        self.config = config
        self.client = create_nillion_client(
            UserKey.from_seed(config.seed),
            NodeKey.from_seed(config.seed)
        )
        self.user_id = self.client.user_id
        self.party_id = self.client.party_id
        self.program_id = f"{self.user_id}/{config.program_name}"

    def setup_payments(self):
        payments_config = create_payments_config(self.config.chain_id, self.config.grpc_endpoint)
        payments_client = LedgerClient(payments_config)
        payments_wallet = LocalWallet(
            PrivateKey(bytes.fromhex(os.getenv("NILLION_NILCHAIN_PRIVATE_KEY_0"))),
            prefix="nillion",
        )
        return payments_client, payments_wallet

    def parse_party_store_ids(self, party_store_pairs: List[str]) -> Dict[str, str]:
        party_store_mapping = {}
        for pair in party_store_pairs:
            party_id, store_id = pair.split(":")
            party_store_mapping[party_id] = store_id
        return party_store_mapping

    def setup_compute_bindings(self, party_ids: List[str]) -> nillion.ProgramBindings:
        compute_bindings = nillion.ProgramBindings(self.program_id)

        # Add issuer bindings
        compute_bindings.add_input_party("Issuer", self.party_id)
        compute_bindings.add_output_party("Issuer", self.party_id)

        # Add user bindings
        for party_id in party_ids:
            compute_bindings.add_input_party("User", party_id)

        return compute_bindings

    async def perform_computation(self, store_id_1: str, party_store_mapping: Dict[str, str],
                                  payments_client, payments_wallet):
        print(f"Computing using program {self.program_id}")
        print(f"Party 1 secret store_id: {store_id_1}")

        compute_bindings = self.setup_compute_bindings(party_store_mapping.keys())
        compute_time_secrets = nillion.NadaValues({})

        receipt = await get_quote_and_pay(
            self.client,
            nillion.Operation.compute(self.program_id, compute_time_secrets),
            payments_wallet,
            payments_client,
            self.config.cluster_id,
        )

        store_ids = [store_id_1] + list(party_store_mapping.values())
        compute_id = await self.client.compute(
            self.config.cluster_id,
            compute_bindings,
            store_ids,
            compute_time_secrets,
            receipt,
        )

        print(f"The computation was sent to the network. compute_id: {compute_id}")
        return await self.wait_for_result()

    async def wait_for_result(self):
        while True:
            compute_event = await self.client.next_compute_event()
            if isinstance(compute_event, nillion.ComputeFinishedEvent):
                print(f"✅  Compute complete for compute_id {compute_event.uuid}")
                print(f"🖥️  The result is {compute_event.result.value}")
                return compute_event.result.value


def parse_args(args=None):
    parser = argparse.ArgumentParser(
        description="Create a secret on the Nillion network with set read/retrieve permissions"
    )
    parser.add_argument(
        "--store_id_1",
        required=True,
        type=str,
        help="Store ID of the 1st secret",
    )
    parser.add_argument(
        "--party_ids_to_store_ids",
        required=True,
        nargs="+",
        type=str,
        help="List of partyid:storeid pairs of the secrets, with each pair separated by a space",
    )
    return parser.parse_args(args)

