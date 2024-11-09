import sys
import os
import time
import hashlib
import binascii
import multiprocessing
from multiprocessing import Process, Queue
from multiprocessing.pool import ThreadPool
import threading
import base58
import ecdsa
import requests
import subprocess

def install_missing_packages():
try:
import base58
import ecdsa
import requests
except ImportError:
subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'base58==1.0.0'])
subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'ecdsa==0.13'])
subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'requests==2.19.1'])

install_missing_packages()

def generate_private_key():
return binascii.hexlify(os.urandom(32)).decode('utf-8')

def private_key_to_WIF(private_key):
var80 = "80" + str(private_key)
var = hashlib.sha256(binascii.unhexlify(hashlib.sha256(binascii.unhexlify(var80)).hexdigest())).hexdigest()
return str(base58.b58encode(binascii.unhexlify(str(var80) + str(var[0:8]))), 'utf-8')

def private_key_to_public_key(private_key):
sign = ecdsa.SigningKey.from_string(binascii.unhexlify(private_key), curve=ecdsa.SECP256k1)
return '04' + binascii.hexlify(sign.verifying_key.to_string()).decode('utf-8')

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

def get_balance(address):
time.sleep(0.2)
try:
response = requests.get(f"https://sochain.com/api/v2/address/BTC/{address}")
return float(response.json()['data']['balance'])
except:
return -1

def data_export(queue):
while True:
private_key = generate_private_key()
public_key = private_key_to_public_key(private_key)
address = public_key_to_address(public_key)
queue.put((private_key, address), block=False)

def worker(queue):
while True:
if not queue.empty():
data = queue.get(block=True)
balance = get_balance(data[1])
process(data, balance)

def process(data, balance):
private_key, address = data
if balance == 0.00000000:
print(f"{address:<34} : {balance}")
elif balance > 0.00000000:
with open("found.txt", "a") as file:
file.write(f"address: {address}\nprivate key: {private_key}\nWIF private key: {private_key_to_WIF(private_key)}\npublic key: {private_key_to_public_key(private_key).upper()}\nbalance: {balance}\n\n")

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

if __name__ == '__main__':
try:
pool = ThreadPool(processes=multiprocessing.cpu_count() * 2)
pool.map(thread, range(0, 1))
except:
pool.close()
exit()
