
from hashlib import sha256
import json
import time

from flask import Flask, request, jsonify


class Block:
    def __init__(self, index, transactions, timestamp, previous_hash):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.nonce = 0

    def compute_hash(self):
        """
        A function that return the hash of the block contents.
        """
        block_string = json.dumps(self.__dict__, sort_keys=True)
        return sha256(block_string.encode()).hexdigest()


class Blockchain:
    # difficulty of our PoW algorithm
    difficulty = 2

    def __init__(self):
        self.unconfirmed_transactions = []
        self.chain = []
        self.create_genesis_block()

    def create_genesis_block(self):
        """
        A function to generate genesis block and appends it to
        the chain. The block has index 0, previous_hash as 0, and
        a valid hash.
        """
        genesis_block = Block(0, [], time.time(), "0")
        genesis_block.hash = genesis_block.compute_hash()
        self.chain.append(genesis_block)

    @property
    def last_block(self):
        return self.chain[-1]

    def add_block(self, block, proof):
        """
        A function that adds the block to the chain after verification.
        Verification includes:
        * Checking if the proof is valid.
        * The previous_hash referred in the block and the hash of latest block
          in the chain match.
        """
        previous_hash = self.last_block.hash

        if previous_hash != block.previous_hash:
            return False

        block.hash = proof
        self.chain.append(block)
        return True



    def proof_of_work(self, block):
        """
        Function that tries different values of nonce to get a hash
        that satisfies our difficulty criteria.
        """
        block.nonce = 0

        computed_hash = block.compute_hash()
        while not computed_hash.startswith('0' * Blockchain.difficulty):
            block.nonce += 1
            computed_hash = block.compute_hash()

        return computed_hash

    def add_new_transaction(self, sender, recipient, amount):
        """
        Adds a new transaction to the list of pending transactions.
        """
        self.unconfirmed_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount
        })
        return True

    def mine(self):
        """
        This function serves as an interface to add the pending
        transactions to the blockchain by adding them to the block
        and figuring out Proof Of Work.
        """
        if not self.unconfirmed_transactions:
            return False

        last_block = self.last_block

        new_block = Block(index=last_block.index + 1,
                          transactions=self.unconfirmed_transactions,
                          timestamp=time.time(),
                          previous_hash=last_block.hash)

        proof = self.proof_of_work(new_block)

        new_block.hash = proof

        self.unconfirmed_transactions = []

        print(self.add_block(new_block, proof))

        return new_block.index


app = Flask(__name__)
blockchain = Blockchain()


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()
    print("wartosci ", values)
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Brakujące dane', 400

    index = blockchain.add_new_transaction(values['sender'], values['recipient'], values['amount'])

    blockchain.mine()

    response = {'message': f'Transakcja zostanie dodana do Bloku {index}'}
    return jsonify(response), 201

@app.route('/chain', methods=['GET'])
def full_chain():
    chain_data = []
    for block in blockchain.chain:
        block_data = {
            'index': block.index,
            'transactions': block.transactions,
            'timestamp': block.timestamp,
            'previous_hash': block.previous_hash,
            'nonce': block.nonce,
            'hash': block.hash
        }
        chain_data.append(block_data)

    response = {
        'chain': chain_data,
        'length': len(chain_data),
    }
    return jsonify(response), 200

@app.route('/transactions/pending', methods=['GET'])
def get_pending_transactions():
    """
    Returns the list of pending transactions.
    """
    pending_txs = blockchain.unconfirmed_transactions
    return jsonify({'transactions': pending_txs}), 200

@app.route('/wallet/<address>', methods=['GET'])
def get_wallet_balance(address):
    """
    Returns the balance of the wallet for a given address.
    """
    balance = 0
    for block in blockchain.chain:
        for tx in block.transactions:
            if tx['sender'] == address:
                balance -= tx['amount']
            if tx['recipient'] == address:
                balance += tx['amount']
    return jsonify({'address': address, 'balance': balance}), 200

@app.route('/chain/length', methods=['GET'])
def get_chain_length():
    """
    Returns the length of the blockchain.
    """
    chain_length = len(blockchain.chain)
    return jsonify({'chain_length': chain_length}), 200


app.run(debug=True, port=5000)
