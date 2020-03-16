# Paste your version of blockchain.py from the client_mining_p
# folder here
from django.shortcuts import render
import datetime
import hashlib
import json
from uuid import uuid4
import socket
from urllib.parse import urlparse
from django.http import JsonResponse, HttpResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt #New
from .models import Chain

import hashlib
import json
from time import time
from uuid import uuid4
from datetime import date


class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []

        # Create the genesis block
        self.new_block(previous_hash=1, proof=100)

    def new_transaction(self, sender, recipient, amount):
        '''
        :param sender: <str> Address of the Recipient
        :param recipient: <str> Address of the Recipient
        :param amount: <int> Amount
        :return: <int> The index of the `block` that will hold this transaction
        '''
        day = date.today().strftime("%d/%m/%Y")
        self.current_transactions.append({
                                            'sender': sender,
                                            'recipient': recipient,
                                            'amount': amount,
                                            'date': day
                                        })
        return self.last_block['index'] + 1

    def new_block(self, proof, previous_hash=None):
        """
        Create a new Block in the Blockchain

        A block should have:
        * Index
        * Timestamp
        * List of current transactions
        * The proof used to mine this block
        * The hash of the previous block

        :param proof: <int> The proof given by the Proof of Work algorithm
        :param previous_hash: (Optional) <str> Hash of previous Block
        :return: <dict> New Block
        """

        block = {
            # TODO
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.last_block)
        }

        # Reset the current list of transactions
        self.current_transactions = []
        # Append the block to the chain
        self.chain.append(block)
        # Return the new block
        return block

    def hash(self, block):
        """
        Creates a SHA-256 hash of a Block

        :param block": <dict> Block
        "return": <str>
        """
        # Use json.dumps to convert json into a string
        # Use hashlib.sha256 to create a hash
        # It requires a `bytes-like` object, which is what
        # .encode() does.
        # It converts the Python string into a byte string.
        # We must make sure that the Dictionary is Ordered,
        # or we'll have inconsistent hashes

        # TODO: Create the block_string
        string_block = json.dumps(block, sort_keys=True)

        # TODO: Hash this string using sha256
        raw_hash = hashlib.sha256(string_block.encode())
        # By itself, the sha256 function returns the hash in a raw string
        # that will likely include escaped characters.
        # This can be hard to read, but .hexdigest() converts the
        # hash to a string of hexadecimal characters, which is
        # easier to work with and understand

        # TODO: Return the hashed block string in hexadecimal format
        hex_hash = raw_hash.hexdigest()
        return hex_hash

    @staticmethod
    def valid_proof(block_string, proof):
        """
        Validates the Proof:  Does hash(block_string, proof) contain 6
        leading zeroes?  Return true if the proof is valid
        :param block_string: <string> The stringified block to use to
        check in combination with `proof`
        :param proof: <int?> The value that when combined with the
        stringified previous block results in a hash that has the
        correct number of leading zeroes.
        :return: True if the resulting hash is a valid proof, False otherwise
        """
        guess = f'{block_string}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()

        return guess_hash[:6] == '000000'


    @property
    def last_block(self):
        return self.chain[-1]


# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')

# Instantiate the Blockchain
blockchain = Blockchain()

'''
Modify the mine endpoint to instead receive and validate or reject a new proof sent by a client.
It should accept a POST
Use data = request.get_json() to pull the data out of the POST
Note that request and requests both exist in this project
Check that 'proof', and 'id' are present
return a 400 error using jsonify(response) with a 'message'
Return a message indicating success or failure. Remember, a valid proof should fail for all senders except the first.
'''


@csrf_exempt
def mine(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        print(data)
        if data['proof'] and data['id']:
            proof = data['proof']
            id = data['id']
            last_block = blockchain.last_block
            last_block_str = json.dumps(blockchain.last_block, sort_keys=True)
            print('BLOCK STRING', last_block_str)
            valid = blockchain.valid_proof(last_block_str, proof)
            if valid is True:
                blockchain.new_transaction('0', id, 1)
                previous_hash = blockchain.hash(blockchain.last_block)
                created = blockchain.new_block(proof, previous_hash)
                response = {
                    'message': 'New Block Forged',
                    'block': created
                }
                new_blockchain = json.dumps(blockchain.chain)
                chain_to_db = Chain.objects.create(chain=new_blockchain)
                saved = chain_to_db.save()
                return JsonResponse(response)
                
            else:
                response = {
                    'message': 'Ya done goofed'
                }
                return JsonResponse(response, status=401)
                       
@csrf_exempt
def full_chain(request):
    if request.method == 'GET':
        latest_chain = Chain.objects.latest('id').chain
        response = {
            'chain': json.loads(latest_chain)
        }
        return JsonResponse(response)
@csrf_exempt
def last_block(request):
    if request.method == 'GET':
        response = {
        'last_block': blockchain.last_block
        }
        return JsonResponse(response)

@csrf_exempt
def receive_transaction(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        required = ['sender', 'recipient', 'amount']

        if not all(k in data for k in required):
            ## error
            response = { 'message': 'Missing values'}
            return JsonResponse(response, status=400)
    
    index = blockchain.new_transaction(data['sender'], data['recipient'], data['amount'])
    response = { 'message': f'Transaction will be added to block at index {index}'}
    return JsonResponse(response, status=201)
