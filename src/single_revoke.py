from web3 import Web3
import httpx
from Abi.data_abi import abi


class TokenAuthorizedListFetcher:
    def __init__(self, address, network):
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

        if network not in self.chain_rpc or network not in self.chain_dict:
            raise ValueError(f"Network '{network}' is not supported.")

        self.rpc_url = self.chain_rpc[network]
        self.chain_id = self.chain_dict[network]

        self.address = Web3.to_checksum_address(address)
        self.network = network
        self.web3 = Web3(Web3.HTTPProvider(self.rpc_url))

        self.url = "https://api.rabby.io/v2/user/token_authorized_list"
        self.gas_market_url = f"https://api.rabby.io/v1/wallet/gas_market?chain_id={network}"
        self.pre_exec_tx_url = "https://api.rabby.io/v1/wallet/pre_exec_tx"
        self.parse_tx_url = "https://api.rabby.io/v1/engine/action/parse_tx"
        self.eth_rpc_url = "https://api.rabby.io/v1/wallet/eth_rpc?origin=chrome-extension%3A%2F%2Facmacodkjbdgmoleebolmdjonilkdbch&method=eth_getBlockByNumber"
        self.tx_is_gasless_url = "https://api.rabby.io/v1/wallet/tx_is_gasless"
        self.submit_tx_url = "https://api.rabby.io/v1/wallet/submit_tx"
        self.contract_info_url = f"https://api.rabby.io/v1/contract?chain_id={network}&id={{spender_address}}"
        self.token_info_url = f"https://api.rabby.io/v1/user/token?id={{address}}&chain_id={network}&token_id={{token_id}}"
        self.contract_interaction_url = f"https://api.rabby.io/v1/engine/contract/has_interaction?chain_id={network}&user_addr={{my_address}}&contract_id={{spender_id}}"
        self.festats_pre_exec_url = f"https://festats.debank.com/rabby/preExecTransaction?type=Simple%20Key%20Pair&category=PrivateKey&chainId={network}&success=true&createdBy=rabby&source=tokenApproval&trigger=&networkType=Integrated%20Network"
        self.festats_sign_url = f"https://festats.debank.com/rabby/signTransaction?type=Simple%20Key%20Pair&chainId={network}&category=PrivateKey&preExecSuccess=true&createdBy=rabby&source=tokenApproval&trigger=&networkType=Integrated%20Network"
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

    async def fetch_data(self):
        params = {
            "id": self.address,
            "chain_id": self.chain_id
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(self.url, params=params, headers=self.eth_rpc_headers)
            if response.status_code == 200:
                data = response.json()
                return data
            else:
                print(f"Failed to fetch data: {response.status_code}")
                return None

    def extract_spender_ids(self, data):
        spender_ids = []
        for token in data:
            token_id = token['id']
            spenders = token.get('spenders', [])
            for spender in spenders:
                spender_id = Web3.to_checksum_address(spender['id'])
                spender_ids.append({
                    'token_id': token_id,
                    'spender_id': spender_id
                })
        return spender_ids

    async def encode_approve_data(self, contract_address: str, spender_address: str) -> str:
        contract_address = Web3.to_checksum_address(contract_address)
        spender_address = Web3.to_checksum_address(spender_address)

        contract = self.web3.eth.contract(address=contract_address, abi=abi)

        encoded_data = contract.encodeABI(fn_name="approve", args=[spender_address, 0])

        return encoded_data

    async def fetch_gas_market_data(self):
        async with httpx.AsyncClient() as client:
            response = await client.get(self.gas_market_url, headers=self.eth_rpc_headers)

            if response.status_code == 200:
                data = response.json()
                return data
            else:
                print(f"Failed to fetch gas market data: {response.status_code}")
                return None

    async def extract_price_and_convert_to_hex(self):
        data = await self.fetch_gas_market_data()

        if data and len(data) > 1:
            second_item = data[1]
            price = second_item.get('price')
            if price is not None:
                int_price = int(price)
                hex_price = hex(int_price)
            else:
                print("Price not found in the second dictionary")
                return None, None

            priority_price = second_item.get('priority_price')
            if priority_price is not None:
                int_priority_price = int(priority_price)
                hex_priority_price = hex(int_priority_price)
            else:
                print("Priority price not found in the second dictionary")
                return None, None

            return hex_price, hex_priority_price
        else:
            print("Second dictionary not found in the response")
            return None, None

    async def post_eth_rpc_request(self, payload):
        async with httpx.AsyncClient() as client:
            response = await client.post(self.eth_rpc_url, headers=self.eth_rpc_headers, json=payload)

            if response.status_code == 200:
                data = response.json()
                result = data.get('result')
                if result:
                    print(f"Result: {result}")
                    return result
                else:
                    print("Result not found in the response")
                    return None
            else:
                print(f"Failed to post eth_rpc_request: {response.status_code}")
                return None

    async def post_pre_exec_tx(self, token_id, encoded_data, gas_hex, nonce):
        payload = {
            "tx": {
                "chainId": self.chain_id,
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

    async def post_parse_tx(self, token_id, encoded_data, gas_hex, nonce):
        payload = {
            "chain_id": self.network,
            "tx": {
                "chainId": self.chain_id,
                "from": self.address,
                "to": token_id,
                "value": "0x0",
                "data": encoded_data,
                "gas": "0x0",
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

    async def post_eth_get_block_by_number(self):
        payload = {
            "chain_id": self.network,
            "method": "eth_getBlockByNumber",
            "params": [
                "latest",
                False
            ]
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(self.eth_rpc_url, headers=self.eth_rpc_headers, json=payload)

            if response.status_code == 200:
                data = response.json()
                print("Block Data:", data)
                return data
            else:
                print(f"Failed to get block by number: {response.status_code}")
                return None

    async def get_contract_info(self, spender_address: str):
        url = self.contract_info_url.format(spender_address=spender_address)

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.eth_rpc_headers)

            if response.status_code == 200:
                data = response.json()
                print(f"Contract Info for {spender_address}:", data)
                return data
            else:
                print(f"Failed to get contract info: {response.status_code}")
                return None

    async def get_token_info(self, token_id: str):
        url = self.token_info_url.format(address=self.address, token_id=token_id)

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.eth_rpc_headers)

            if response.status_code == 200:
                data = response.json()
                print(f"Token Info for {token_id}:", data)
                return data
            else:
                print(f"Failed to get token info: {response.status_code}")
                return None

    async def get_contract_interaction(self, spender_id: str):
        url = self.contract_interaction_url.format(my_address=self.address, spender_id=spender_id)

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.eth_rpc_headers)

            if response.status_code == 200:
                data = response.json()
                print(f"Contract Interaction for {spender_id}:", data)
                return data
            else:
                print(f"Failed to get contract interaction: {response.status_code}")
                return None

    async def post_tx_is_gasless(self, private_key, gas_used: int, pre_exec_success: bool, token_id: str,
                                 encoded_data: str, gas_hex: str, nonce: str):

        w3 = Web3(Web3.HTTPProvider(self.rpc_url))  # Use dynamic RPC URL
        wallet = w3.eth.account.from_key(private_key)

        gas_estimate = w3.eth.estimate_gas({
            "from": wallet.address,
            "to": Web3.to_checksum_address(f"{token_id}"),
            "data": encoded_data,
            "value": "0x0"
        })

        print(gas_estimate)
        payload = {
            "gas_used": gas_used,
            "pre_exec_success": pre_exec_success,
            "tx": {
                "chainId": self.chain_id,  # Use dynamic chainId
                "from": self.address,
                "to": token_id,
                "data": encoded_data,
                "gas": gas_estimate,
                "maxFeePerGas": gas_hex,
                "maxPriorityFeePerGas": gas_hex,
                "nonce": nonce,
                "gasPrice": gas_hex
            },
            "usd_value": 0
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(self.tx_is_gasless_url, headers=self.eth_rpc_headers, json=payload)

            if response.status_code == 200:
                data = response.json()
                print(f"Gasless TX Result: {data}")
                return data
            else:
                print(f"Failed to check if TX is gasless: {response.status_code}")
                return None

    async def post_submit_tx(self, private_key, token_id: str, encoded_data: str, nonce: str,
                             log_id: int, maxFeePerGas: int, maxPriorityFeePerGas: int):

        w3 = Web3(Web3.HTTPProvider(self.rpc_url))
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
            "chainId": self.chain_id,
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
                "chainId": self.chain_id,
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

    async def run(self):
        pk = input("Enter your private key: ")
        data = await self.fetch_data()
        if data:
            spender_ids = self.extract_spender_ids(data)

            for item in spender_ids:
                spender_address = item['spender_id']
                token_id = item['token_id']
                encoded_data = await self.encode_approve_data(token_id, spender_address)
                print(f"Token ID: {token_id}, Spender ID: {spender_address}, Encoded Data: {encoded_data}")

                hex_price, hex_priority_price = await self.extract_price_and_convert_to_hex()

                nonce = await self.post_eth_rpc_request(
                    {"chain_id": self.chain_id, "method": "eth_getTransactionCount", "params": [self.address, "latest"]})

                await self.post_pre_exec_tx(token_id, encoded_data, hex_price, nonce)

                log_id = await self.post_parse_tx(token_id, encoded_data, hex_price, nonce)

                await self.post_eth_get_block_by_number()

                await self.get_contract_info(spender_address)

                await self.get_token_info(token_id)

                await self.get_contract_interaction(spender_address)

                await self.post_tx_is_gasless(pk, 24059, True, token_id, encoded_data, hex_price, nonce)

                await self.post_submit_tx(pk, token_id, encoded_data, nonce, log_id, hex_price, hex_priority_price)
