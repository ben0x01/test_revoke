import httpx
from web3 import Web3
from Abi.data_abi import abi


class MassTokenAuthorizedListFetcher:
    def __init__(self, address):
        self.base_gas_market_url = "https://api.rabby.io/v1/wallet/gas_market?chain_id="
        self.parse_tx_url = "https://api.rabby.io/v1/engine/action/parse_tx"
        self.submit_tx_url = "https://api.rabby.io/v1/wallet/submit_tx"
        self.eth_call_url = "https://api.rabby.io/v1/wallet/eth_rpc?origin=chrome-extension%3A%2F%2Facmacodkjbdgmoleebolmdjonilkdbch&method=eth_call"
        self.url = "https://api.rabby.io/v2/user/token_authorized_list"
        self.pre_exec_tx_url = "https://api.rabby.io/v1/wallet/pre_exec_tx"
        self.eth_rpc_url = "https://api.rabby.io/v1/wallet/eth_rpc?origin=chrome-extension%3A%2F%2Facmacodkjbdgmoleebolmdjonilkdbch&method=eth_getBlockByNumber"
        self.eth_get_balance_url = "https://api.rabby.io/v1/wallet/eth_rpc?origin=chrome-extension%3A%2F%2Facmacodkjbdgmoleebolmdjonilkdbch&method=eth_getBalance"
        self.eth_get_block_by_number_url = "https://api.rabby.io/v1/wallet/eth_rpc?origin=chrome-extension%3A%2F%2Facmacodkjbdgmoleebolmdjonilkdbch&method=eth_getBlockByNumber"
        self.eth_rpc_headers = {
            "accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "Connection": "keep-alive",
            "content-type": "application/json",
            "Host": "api.rabby.io",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
            "x-api-nonce": "n_G1kQlpy6ihaTc0ErkeATqiyIATMlSotRDktguR0x",
            "x-api-sign": "331be08950feccd71752e509047727a111e0211778d4344bf126c7616b23a30f",
            "x-api-ts": "1723844498",
            "x-api-ver": "v2",
            "x-client": "Rabby",
            "x-version": "0.92.87",
        }
        self.address = address
        self.chains = ["op", "arb", "bsc", "eth", "avax", "base", "xdai", "blast", "linea", "matic"]

        self.chain_rpc = {
            "op": "https://optimism.llamarpc.com",
            "arb": "https://arbitrum.llamarpc.com",
            "bsc": "https://binance.llamarpc.com",
            "eth": "https://eth.llamarpc.com",
            "avax": "https://avalanche.drpc.org",
            "base": "https://base.llamarpc.com",
            "xdai": "https://gnosis-rpc.publicnode.com",
            "blast": "https://blast.din.dev/rpc",
            "linea": "https://linea.decubate.com",
            "matic": "https://polygon.llamarpc.com"
        }

        self.chain_dict = {
            "op": 10,
            "arb": 42161,
            "bsc": 56,
            "eth": 1,
            "avax": 43114,
            "base": 8453,
            "xdai": 100,
            "blast": 81457,
            "linea": 59144,
            "matic": 137
        }

    def get_rpc_and_chain_id(self, network: str):
        if network not in self.chain_rpc or network not in self.chain_dict:
            raise ValueError(f"Network '{network}' is not supported.")
        rpc_url = self.chain_rpc[network]
        chain_id = self.chain_dict[network]
        return rpc_url, chain_id

    async def fetch_data(self, chain):
        params = {
            "id": self.address,
            "chain_id": chain
        }

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(self.url, params=params, headers=self.eth_rpc_headers)
                response.raise_for_status()
                data = response.json()

                tokens_info = []
                if data:
                    for item in data:
                        token_id = item['id']
                        spenders = item.get('spenders', [])
                        for spender in spenders:
                            spender_id = Web3.to_checksum_address(spender['id'])
                            tokens_info.append({
                                'token_id': token_id,
                                'spender_id': spender_id
                            })
                return tokens_info, chain

        except httpx.HTTPStatusError as e:
            print(f"HTTP error occurred: {e}")
        except httpx.RequestError as e:
            print(f"Request error occurred: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")
        return None, None

    async def check_all_chains(self):
        results = {}
        for chain in self.chains:
            data, successful_chain = await self.fetch_data(chain)
            if data:
                results[successful_chain] = data
        return results

    async def encode_approve_data(self, contract_address: str, spender_address: str) -> str:
        w3 = Web3()

        contract_address = Web3.to_checksum_address(contract_address)
        spender_address = Web3.to_checksum_address(spender_address)

        contract = w3.eth.contract(address=contract_address, abi=abi)

        encoded_data = contract.encodeABI(fn_name="approve", args=[spender_address, 0])

        return encoded_data

    async def post_pre_exec_tx(self, token_id, encoded_data, gas_hex, nonce, network):
        rpc_url, chain_id = self.get_rpc_and_chain_id(network)

        payload = {
            "tx": {
                "chainId": chain_id,
                "from": self.address,
                "to": token_id,
                "value": "0x0",
                "data": encoded_data,
                "gas": "",
                "maxFeePerGas": gas_hex,
                "maxPriorityFeePerGas": gas_hex,
                "nonce": nonce
            },
            "user_addr": self.address,
            "origin": "chrome-extension://acmacodkjbdgmoleebolmdjonilkdbch",
            "update_nonce": True,
            "pending_tx_list": []
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(self.pre_exec_tx_url, headers=self.eth_rpc_headers, json=payload)

            if response.status_code == 200:
                data = response.json()
                print("Pre Exec TX Success:", data)
                return data
            else:
                print(f"Failed to post pre_exec_tx: {response.status_code}")
                return None

    async def post_eth_rpc_request(self, chain, wallet_address):
        rpc_url, chain_id = self.get_rpc_and_chain_id(chain)

        payload = {
            "chain_id": chain_id,
            "method": "eth_getTransactionCount",
            "params": [
                wallet_address,
                "latest"
            ]
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(self.eth_rpc_url, headers=self.eth_rpc_headers, json=payload)

            if response.status_code == 200:
                data = response.json()
                result = data.get('result')
                if result:
                    return result
                else:
                    print(f"Result not found in the response for chain {chain}")
                    return None
            else:
                print(f"Failed to post eth_rpc_request for chain {chain}: {response.status_code}")
                return None

    async def fetch_gas_market_data(self, successful_chains):
        results = {}
        for chain in successful_chains:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_gas_market_url}{chain}", headers=self.eth_rpc_headers)
                if response.status_code == 200:
                    data = response.json()
                    results[chain] = data
                else:
                    print(f"Failed to fetch gas market data for {chain}: {response.status_code}")
        return results

    async def extract_price_and_convert_to_hex(self, gas_market_data):
        hex_prices = {}

        for chain, market_data in gas_market_data.items():
            if market_data and len(market_data) > 1:
                second_item = market_data[1]
                price = second_item.get('price')
                if price is not None:
                    int_price = int(price)
                    hex_number = hex(int_price)
                    hex_prices[chain] = hex_number
                else:
                    print(f"Price not found in the second dictionary for chain {chain}")
            else:
                print(f"Second dictionary not found in the response for chain {chain}")

        return hex_prices

    async def post_eth_get_balance(self, chain, wallet_address):
        rpc_url, chain_id = self.get_rpc_and_chain_id(chain)

        payload = {
            "chain_id": chain_id,
            "method": "eth_getBalance",
            "params": [
                wallet_address,
                "latest"
            ]
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(self.eth_get_balance_url, headers=self.eth_rpc_headers, json=payload)

            if response.status_code == 200:
                data = response.json()
                balance = data.get('result')
                if balance:
                    return balance
                else:
                    print(f"Balance not found in the response for chain {chain}")
                    return None
            else:
                print(f"Failed to post eth_getBalance request for chain {chain}: {response.status_code}")
                return None

    async def post_eth_get_block_by_number(self, chain):
        rpc_url, chain_id = self.get_rpc_and_chain_id(chain)

        payload = {
            "chain_id": chain_id,
            "method": "eth_getBlockByNumber",
            "params": [
                "latest",
                False
            ]
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(self.eth_get_block_by_number_url, headers=self.eth_rpc_headers,
                                         json=payload)

            if response.status_code == 200:
                data = response.json()
                block_info = data.get('result')
                if block_info:
                    return block_info
                else:
                    print(f"Block info not found in the response for chain {chain}")
                    return None
            else:
                print(f"Failed to post eth_getBlockByNumber request for chain {chain}: {response.status_code}")
                return None

    async def post_parse_tx(self, token_id, encoded_data, gas_hex, nonce, network):
        rpc_url, chain_id = self.get_rpc_and_chain_id(network)

        payload = {
            "chain_id": chain_id,
            "tx": {
                "chainId": chain_id,
                "from": self.address,
                "to": token_id,
                "value": "0x0",
                "data": encoded_data,
                "gas": "",
                "maxFeePerGas": gas_hex,
                "maxPriorityFeePerGas": gas_hex,
                "nonce": nonce
            },
            "origin": "chrome-extension://acmacodkjbdgmoleebolmdjonilkdbch",
            "user_addr": self.address
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(self.parse_tx_url, headers=self.eth_rpc_headers, json=payload)

            if response.status_code == 200:
                data = response.json()
                log_id = data.get('log_id')
                if log_id:
                    print(f"Log ID: {log_id}")
                    return log_id
                else:
                    print("Log ID not found in the response")
                    return None
            else:
                print(f"Failed to parse transaction: {response.status_code}")
                return None

    async def post_submit_tx(self, private_key, token_id: str, encoded_data: str, nonce: str,
                             log_id: int, maxFeePerGas: int, maxPriorityFeePerGas: int, network):

        rpc_url, chain_id = self.get_rpc_and_chain_id(network)
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        wallet = w3.eth.account.from_key(private_key)

        gas_estimate = w3.eth.estimate_gas({
            "from": wallet.address,
            "to": Web3.to_checksum_address(f"{token_id}"),
            "data": encoded_data,
            "value": "0x0"
        })
        print(gas_estimate)
        print(type(gas_estimate))

        tx = {
            "from": self.address,
            "to": Web3.to_checksum_address(f"{token_id}"),
            "data": encoded_data,
            "nonce": nonce,
            "chainId": chain_id,
            "gas": gas_estimate,
            "maxFeePerGas": maxFeePerGas,
            "maxPriorityFeePerGas": maxPriorityFeePerGas
        }

        signed_tx = wallet.sign_transaction(tx)

        v = signed_tx.v
        r = signed_tx.r
        s = signed_tx.s

        v_hex = f"0x{v:02x}"
        r_hex = f"0x{r:x}"
        s_hex = f"0x{s:x}"

        payload = {
            "tx": {
                "from": self.address,
                "to": token_id,
                "data": encoded_data,
                "nonce": nonce,
                "chainId": chain_id,
                "gas": gas_estimate,
                "maxFeePerGas": maxFeePerGas,
                "maxPriorityFeePerGas": maxPriorityFeePerGas,
                "r": r_hex,
                "s": s_hex,
                "v": v_hex,
                "value": "0x0"
            },
            "push_type": "default",
            "req_id": "",
            "origin": "chrome-extension://acmacodkjbdgmoleebolmdjonilkdbch",
            "is_gasless": False,
            "log_id": log_id
        }

        print(payload)

        async with httpx.AsyncClient() as client:
            response = await client.post(self.submit_tx_url, headers=self.eth_rpc_headers, json=payload)

            if response.status_code == 200:
                data = response.json()
                print(f"Submit TX Result: {data}")
                return data
            else:
                print(f"Failed to submit transaction: {response.status_code}")
                return None

    # TODO rewrite run
    async def run(self):
        wallet_address = input("Enter your wallet address: ")

        successful_chains = await self.check_all_chains()

        gas_market_data = await self.fetch_gas_market_data(successful_chains.keys())
        hex_prices = await self.extract_price_and_convert_to_hex(gas_market_data)

        for network, data in successful_chains.items():
            token_id = data[0]['token_id']
            spender_id = data[0]['spender_id']
            encoded_data = await self.encode_approve_data(token_id, spender_id)
            gas_hex = hex_prices.get(network, "0x0")
            nonce = await self.post_eth_rpc_request(network, wallet_address)
            if nonce:
                pre_exec_tx_result = await self.post_pre_exec_tx(token_id, encoded_data, gas_hex, nonce, network)
                if pre_exec_tx_result:
                    log_id = await self.post_parse_tx(token_id, encoded_data, gas_hex, nonce, network)
                    if log_id:
                        print(f"Transaction parsed successfully with log ID: {log_id}")
                        await self.post_submit_tx(wallet_address, token_id, encoded_data, nonce, log_id, gas_hex,
                                                  gas_hex, network)
                    else:
                        print("Failed to parse transaction.")

        for network in successful_chains.keys():
            balance = await self.post_eth_get_balance(network, wallet_address)
            if balance:
                print(f"Balance for chain {network} ({self.get_rpc_and_chain_id(network)[1]}): {balance}")

            block_info = await self.post_eth_get_block_by_number(network)
            if block_info:
                print(f"Block info for chain {network} ({self.get_rpc_and_chain_id(network)[1]}): {block_info}")
