import json
import hashlib
from time import time
from textwrap import dedent
from uuid import uuid4
from flask import Flask, jsonify, request

class Blockchain(object):
	"""docstring for Blockchain"""
	def __init__(self):
		self.chain=[]		#list of blocks
		self.current_transactions=[] 	#joined transactions
		# create genesis block
		self.new_block(previous_hash= 1, proof= 100) 
	def new_block(self, proof, previous_hash=None):
		'''
		generate new block
		param - proof: <int> the proof given by proof of work algorithm
		param - previous_hash: (option)<str> hash of previous block
		return - <dict> new_block
		'''
		block={
			'index': len(self.chain)+1,
			'timestamp': time(),
			'transaction': self.current_transactions,
			'proof': proof,
			'previous_hash': previous_hash or self.hash(self.chain[-1])
		}

		self.current_transactions= []
		self.chain.append(block)

		return block

	def new_transaction(self, sender, recipient, amount):
		'''
		生成新的交易，信息加入下一个待挖矿的区块中
		'''
		self.current_transactions.append({
			'sender': sender,
			'recipient': recipient,
			'amount': amount
			})
		return self.last_block()['index']+1


	def hash(self, block):
		'''
		Generate SHA-256 hash

		param: block
		return: str
		'''
		block_string= json.dumps(block, sort_keys= True).encode()
		return hashlib.sha256(block_string).hexdigest()


	def last_block(self):
		return self.chain[-1]


	def Proof_of_Work(self, last_proof):
		'''
		hash value begin with 0000
		'''
		proof= 0
		while True:
			proof_str= str(last_proof)+ str(proof)
			if hashlib.sha256(proof_str.encode()).hexdigest()[0:4] == '0000':
				break
			if proof%100 ==0:
				print('Now we try on %s, the str is %s'%(proof, proof_str))
			proof= proof+1

		return proof






"""
block structure

block= {
	
	'index': 1,
	'timestamp': time.time(),
	'transaction': {
		'sender': "your public key(SHA256)",
		'recipient' "reviver's public key",
		'amount': 'amount of BTC' 
	}

	'proof': "proof of work(your compute result)",
	'previous_block': "previous block's hash(key part, prevent tampering)"
}
"""

app= Flask(__name__)	#initial Node
node_identifier= str(uuid4()).replace('-', '')	#Generate a globally unique address for this node
blockchain= Blockchain()	#initial Blockchain

@app.route('/mine', methods= ['GET'])
def mine():
	last_block= blockchain.last_block()
	last_proof= last_block['proof']
	proof= blockchain.Proof_of_Work(last_proof)
	#给工作量证明的节点给予奖励
	#发送者为0表明是新挖出的币
	
	blockchain.new_transaction(sender= 0, recipient= node_identifier, amount= 1)
	#Forge the new Block by adding it to the chain
	
	block= blockchain.new_block(proof)
	response= {
		'message': 'New block forge',
		'index': block['index'],
		'transaction': block['transaction'],
		'proof': block['proof'],
		'previous_hash':block['previous_hash']
	}
	return jsonify(response), 200

@app.route('/transaction/new', methods= ['POST'])
def new_transaction():
	values= request.get_json()
	required= ['sender', 'recipient', 'amount']
	for k in required:
		if k not in values:
			return 'Missing values', 400

	index= blockchain.new_transaction(values['sender', 'recipient', 'amount'])
	reponse= {'message': 'Transaction will be add to Block %s'%(ckchain.chain[-1]['index'])}
	return jsonify(response), 201



@app.route('/chain', methods= ['GET'])
def full_chain():
	response={
		'chain': blockchain.chain,
		'length': len(blockchain.chain)
	}
	return jsonify(response), 200

if __name__== '__main__':
	app.run(host = '127.0.0.1', port= 5000)
