import os
import hashlib
import base58
import ecdsa
import requests
from mnemonic import Mnemonic
from hdwallet import HDWallet
from hdwallet.symbols import BTC

# Generate mnemonic phrase and HD wallet
def generate_hd_wallet():
    mnemo = Mnemonic("english")
    mnemonic_phrase = mnemo.generate(strength=256)
    hd_wallet = HDWallet(symbol=BTC)
    hd_wallet.from_mnemonic(mnemonic_phrase)
    return hd_wallet, mnemonic_phrase

# Check balance of a Bitcoin address
def get_balance(address):
    try:
        response = requests.get(f"https://blockchain.info/q/addressbalance/{address}?confirmations=3")
        response.raise_for_status()
        balance = int(response.text) / 1e8  # Convert from satoshi to BTC
        return balance
    except requests.RequestException as e:
        print(f"Error checking balance for {address}: {e}")
        return -1

# Main script
def main():
    hd_wallet, mnemonic_phrase = generate_hd_wallet()
    private_key = hd_wallet.private_key()
    address = hd_wallet.p2pkh_address()
    balance = get_balance(address)
    
    if balance > 0:
        print(f"Address: {address}\nBalance: {balance} BTC\nMnemonic: {mnemonic_phrase}\nPrivate Key: {private_key}")

if __name__ == "__main__":
    main()
