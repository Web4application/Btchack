## Overview

The Btchack project is an automated Bitcoin wallet generator that focuses on creating random Bitcoin wallet addresses, generating their private keys, and checking the balance of these addresses in real-time. 
This project primarily demonstrates the potential security risks and vulnerabilities associated with blockchain technology.
# Components:

## Wallet Generation: 

The script generates random private keys and corresponding Bitcoin wallet addresses using cryptographic functions.
## Balance Check:

It checks the balance of the generated wallets using public blockchain APIs.

## Automation: 
The process is automated to continuously generate new wallets and check their balances without manual intervention.

 ## How It Works:

# Generate Private Key: 
Uses a cryptographic function to create a random 256-bit private key.
# Derive Public Key:
Converts the private key into a corresponding public key using elliptic curve cryptography.
Generate Bitcoin Address: The public key is transformed into a Bitcoin wallet address.

# Check Balance:
The script uses a blockchain API to check if the generated wallet address has any balance.
Logging and Storing Results: If a wallet with a balance is found, the relevant information (private key, public key, address, balance) is logged and stored.
