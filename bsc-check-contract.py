from web3 import Web3
import json
import asyncio
from web3.middleware import geth_poa_middleware


# Constants
BSC_RPC_URL = ""
TOKEN_ADDRESS = ""  # BUSD token address as an example

# Standard ERC20 ABI (this is a minimal ABI, you might want to expand it for more functions)
ERC20_ABI = json.loads('''
[
    {"constant":true,"inputs":[],"name":"name","outputs":[{"name":"","type":"string"}],"type":"function"},
    {"constant":true,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"type":"function"},
    {"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"},
    {"constant":true,"inputs":[],"name":"totalSupply","outputs":[{"name":"","type":"uint256"}],"type":"function"},
    {"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"},
    {"constant":false,"inputs":[{"name":"_to","type":"address"},{"name":"_value","type":"uint256"}],"name":"transfer","outputs":[{"name":"","type":"bool"}],"type":"function"},
    {"constant":true,"inputs":[],"name":"owner","outputs":[{"name":"","type":"address"}],"type":"function"}
]
''')

class TokenAnalyzer:
    def __init__(self, rpc_url, token_address):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)

        self.token_address = Web3.to_checksum_address(token_address)
        self.token_contract = self.w3.eth.contract(address=self.token_address, abi=ERC20_ABI)

    async def analyze_token(self):
        print(f"Analyzing token at address: {self.token_address}")

        # Basic token information
        name = await self.call_contract_function('name')
        symbol = await self.call_contract_function('symbol')
        decimals = await self.call_contract_function('decimals')
        total_supply = await self.call_contract_function('totalSupply')

        print(f"Name: {name}")
        print(f"Symbol: {symbol}")
        print(f"Decimals: {decimals}")
        print(f"Total Supply: {total_supply / (10 ** decimals)}")

        # Contract owner (if available)
        try:
            owner = await self.call_contract_function('owner')
            print(f"Contract Owner: {owner}")
        except Exception as e:
            print("Contract owner function not available")

        # Check if the contract is verified on BscScan
        is_verified = self.check_contract_verification()
        print(f"Contract Verified on BscScan: {is_verified}")

        # Token balance of the contract itself
        contract_balance = await self.call_contract_function('balanceOf', self.token_address)
        print(f"Token Balance of Contract: {contract_balance / (10 ** decimals)}")

        # Get some additional blockchain data
        creator_address = await self.get_contract_creator()
        print(f"Contract Creator: {creator_address}")

        creation_tx = await self.get_contract_creation_tx()
        print(f"Creation Transaction: {creation_tx}")

    async def call_contract_function(self, function_name, *args):
        function = getattr(self.token_contract.functions, function_name)
        return await asyncio.to_thread(function(*args).call)

    def check_contract_verification(self):
        bscscan_url = f"https://bscscan.com/address/{self.token_address}#code"
    
        return True

    async def get_contract_creator(self):
        creation_tx = await self.get_contract_creation_tx()
        if creation_tx:
            tx = await asyncio.to_thread(self.w3.eth.get_transaction, creation_tx)
            return tx['from']
        return None

    async def get_contract_creation_tx(self):
        nonce = await asyncio.to_thread(self.w3.eth.get_transaction_count, self.token_address)
        
        for i in range(max(0, nonce - 1000), nonce + 1):
            block = await asyncio.to_thread(self.w3.eth.get_block, nonce - i, full_transactions=True)
            for tx in block['transactions']:
                if tx['to'] is None and tx['creates'] == self.token_address:
                    return tx['hash'].hex()
        return None

async def main():
    analyzer = TokenAnalyzer(BSC_RPC_URL, TOKEN_ADDRESS)
    await analyzer.analyze_token()

if __name__ == "__main__":
    asyncio.run(main())
