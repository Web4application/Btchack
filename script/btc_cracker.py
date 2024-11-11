import sys
import os
import time
import hashlib
import binascii
import multiprocessing
from multiprocessing import Process, Queue
from multiprocessing.pool import ThreadPool
import base58
import ecdsa
import requests
import subprocess
from mnemonic import Mnemonic
from hdwallet import HDWallet
from hdwallet.symbols import BTC
import logging
import webbrowser
import random
import json
from qiskit import QuantumCircuit, Aer, execute
from qiskit.visualization import plot_histogram
from PySimpleGUI import PySimpleGUI as sg

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define paths for image files if needed
PAYPAL_IMG = 'paypal.png'
BITCOIN_IMG = 'bitcoin.png'

# Function to install missing packages
def install_missing_packages():
    try:
        import base58
        import ecdsa
        import requests
        from mnemonic import Mnemonic
        from hdwallet import HDWallet
    except ImportError:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'base58==1.0.0'])
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'ecdsa==0.13'])
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'requests==2.19.1'])
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'mnemonic==0.18'])
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'hdwallet==1.1.1'])
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'qiskit')

install_missing_packages()

# Generate mnemonic phrase and HD wallet
def generate_hd_wallet():
    mnemo = Mnemonic("english")
    mnemonic_phrase = mnemo.generate(strength=256)
    hd_wallet = HDWallet(symbol=BTC)
    hd_wallet.from_mnemonic(mnemonic_phrase)
    return hd_wallet, mnemonic_phrase

# Generate private key
def generate_private_key():
    return binascii.hexlify(os.urandom(32)).decode('utf-8')

# Convert private key to Wallet Import Format (WIF)
def private_key_to_WIF(private_key):
    var80 = "80" + str(private_key)
    var = hashlib.sha256(binascii.unhexlify(hashlib.sha256(binascii.unhexlify(var80)).hexdigest())).hexdigest()
    return str(base58.b58encode(binascii.unhexlify(str(var80) + str(var[0:8]))), 'utf-8')

# Convert private key to public key
def private_key_to_public_key(private_key):
    sign = ecdsa.SigningKey.from_string(binascii.unhexlify(private_key), curve=ecdsa.SECP256k1)
    return '04' + binascii.hexlify(sign.verifying_key.to_string()).decode('utf-8')

# Convert public key to Bitcoin address
def public_key_to_address(public_key):
    alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    var = hashlib.new('ripemd160')
    var.update(hashlib.sha256(binascii.unhexlify(public_key.encode())).digest())
    doublehash = hashlib.sha256(hashlib.sha256(binascii.unhexlify(('00' + var.hexdigest()).encode())).digest()).hexdigest()
    address = '00' + var.hexdigest() + doublehash[0:8]
    n = int(address, 16)
    output = []
    while n > 0:
        n, remainder = divmod(n, 58)
        output.append(alphabet[remainder])
    return ''.join(output[::-1])

# Check balance of a Bitcoin address
def get_balance(address):
    time.sleep(0.2)
    try:
        response = requests.get(f"https://blockchain.info/q/addressbalance/{address}?confirmations=3")
        response.raise_for_status()
        balance = int(response.text) / 1e8  # Convert from satoshi to BTC
        return balance
    except requests.RequestException as e:
        logging.error(f"Error checking balance for {address}: {e}")
        return -1

# Export data to queue
def data_export(queue):
    while True:
        hd_wallet, mnemonic_phrase = generate_hd_wallet()
        private_key = hd_wallet.private_key()
        public_key = hd_wallet.public_key()
        address = hd_wallet.p2pkh_address()
        queue.put((mnemonic_phrase, private_key, address), block=False)

# Worker process to handle data and check balances
def worker(queue):
    while True:
        if not queue.empty():
            data = queue.get(block=True)
            balance = get_balance(data[2])
            process(data, balance)

# Process and print/save the results
def process(data, balance):
    mnemonic_phrase, private_key, address = data
    if balance == 0.00000000:
        logging.info(f"{address:<34} : {balance}")
    elif balance > 0.00000000:
        with open("found.txt", "a") as file:
            file.write(f"address: {address}\nprivate key: {private_key}\nWIF private key: {private_key_to_WIF(private_key)}\npublic key: {private_key_to_public_key(private_key).upper()}\nbalance: {balance}\nmnemonic phrase: {mnemonic_phrase}\n\n")
        logging.info(f"Found a wallet with balance! Address: {address}, Balance: {balance} BTC")

# Thread management function
def thread(iterator):
    processes = []
    data = Queue()
    data_factory = Process(target=data_export, args=(data,))
    data_factory.daemon = True
    processes.append(data_factory)
    data_factory.start()
    work = Process(target=worker, args=(data,))
    work.daemon = True
    processes.append(work)
    work.start()
    data_factory.join()

# Create the main window
def create_main_window(settings):
    sg.theme(settings['theme'])

    menu_def = [['&Menu', ['&Settings', 'E&xit']]]

    layout = [
        [sg.Menu(menu_def)],
        [sg.Text('Number of mnemonic words', size=(30,1), font=('Comic sans ms', 10)),
         sg.Spin(values=('12', '15', '18', '21', '24'), size=(3,1), key='num_words')],
        [sg.Button('', key='paypal', size=(12,1), font=('Helvetica', 9), button_color=(sg.theme_background_color(), sg.theme_background_color()),
                   image_filename=PAYPAL_IMG, image_size=(80, 50), image_subsample=2, border_width=0),
         sg.Button('', key='bitcoin', size=(12,1), font=('Helvetica', 9), button_color=(sg.theme_background_color(), sg.theme_background_color()),
                   image_filename=BITCOIN_IMG, image_size=(80, 60), image_subsample=2, border_width=0)],
        [sg.Text('This program has been running for... ', size=(30,1), font=('Comic sans ms', 10)),
         sg.Text('', size=(30,1), font=('Comic sans ms', 10), key='_DATE_')],
        [sg.Text('')],
        [sg.Output(size=(87, 20), font=('Comic sans ms', 8), key='out')],
        [sg.Text('Select passwords file', size=(15,1), font=('Comic sans ms', 10)), sg.Input(size=(67, 1), key='-in-'), sg.FileBrowse()],
        [sg.Button('Start/Stop', font=('Comic sans ms', 10))]
    ]

    return sg.Window('Bitcoin wallet cracker', layout=layout, default_element_size=(9,1))

# Load settings