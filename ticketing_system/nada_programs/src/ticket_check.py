# src/ticket_check.py
from nada_dsl import *


def nada_main():
    user = Party(name="User")
    issuer = Party(name="Issuer")


    # User inputs
    user_ticket = SecretInteger(Input(name="user_ticket", party=user))
    user_wallet = SecretInteger(Input(name="user_wallet", party=user))
    user_redeem = SecretInteger(Input(name="user_redeem", party=user))
    # Issuer confirms ticket details
    ticket_id = SecretInteger(Input(name="ticket_id", party=issuer))
    ticket_owner = SecretInteger(Input(name="ticket_owner", party=issuer))
    is_redeemed = SecretInteger(Input(name="is_redeemed", party=issuer))

    # Calculate differences
    ticket_diff = user_ticket - ticket_id  # 0 if tickets match
    owner_diff = user_wallet - ticket_owner  # 0 if owner matches

    # Final status calculation:
    # If ticket_diff and owner_diff are 0 (match) and not redeemed: status = 1
    # If ticket_diff and owner_diff are 0 (match) and redeemed: status = 2
    # Otherwise (no match): status = 0
    status = ticket_diff + owner_diff + is_redeemed + user_redeem

    return [Output(status, "status", party=issuer)]