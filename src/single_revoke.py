from web3 import Web3
import httpx
from Abi.data_abi import abi


class TokenAuthorizedListFetcher:
    def __init__(self, address, chain):
        self.address = Web3.to_checksum_address(address)  # Convert the address to checksum format
        self.chain = chain
        self.url = "https://api.rabby.io/v2/user/token_authorized_list"
        self.gas_market_url = "https://api.rabby.io/v1/wallet/gas_market?chain_id=base"
        self.pre_exec_tx_url = "https://api.rabby.io/v1/wallet/pre_exec_tx"
        self.parse_tx_url = "https://api.rabby.io/v1/engine/action/parse_tx"
        self.eth_rpc_url = "https://api.rabby.io/v1/wallet/eth_rpc?origin=chrome-extension%3A%2F%2Facmacodkjbdgmoleebolmdjonilkdbch&method=eth_getBlockByNumber"
        self.tx_is_gasless_url = "https://api.rabby.io/v1/wallet/tx_is_gasless"
        self.submit_tx_url = "https://api.rabby.io/v1/wallet/submit_tx"
        self.contract_info_url = "https://api.rabby.io/v1/contract?chain_id=base&id={spender_address}"
        self.token_info_url = "https://api.rabby.io/v1/user/token?id={address}&chain_id=base&token_id={token_id}"
        self.contract_interaction_url = "https://api.rabby.io/v1/engine/contract/has_interaction?chain_id=base&user_addr={my_address}&contract_id={spender_id}"
        self.festats_pre_exec_url = "https://festats.debank.com/rabby/preExecTransaction?type=Simple%20Key%20Pair&category=PrivateKey&chainId=base&success=true&createdBy=rabby&source=tokenApproval&trigger=&networkType=Integrated%20Network"
        self.festats_sign_url = "https://festats.debank.com/rabby/signTransaction?type=Simple%20Key%20Pair&chainId=base&category=PrivateKey&preExecSuccess=true&createdBy=rabby&source=tokenApproval&trigger=&networkType=Integrated%20Network"
        self.eth_rpc_headers = {
            "accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "Connection": "keep-alive",
            "content-type": "application/json",
            "Cookie": "_ga=GA1.2.1701441413.1723813477; _gid=GA1.2.1121394741.1723813478; _ga_H8G6S9KCTX=GS1.1.1723813477.1.1.1723813502.0.0.0",
            "Host": "api.rabby.io",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "none",
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
            "chain_id": self.chain
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
                spender_id = Web3.to_checksum_address(spender['id'])  # Convert spender address to checksum format
                spender_ids.append({
                    'token_id': token_id,
                    'spender_id': spender_id
                })
        return spender_ids

    async def encode_approve_data(self, contract_address: str, spender_address: str) -> str:
        w3 = Web3()

        contract_address = Web3.to_checksum_address(contract_address)
        spender_address = Web3.to_checksum_address(spender_address)

        contract = w3.eth.contract(address=contract_address, abi=abi)

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
        if data and len(data) > 1:  # Check if there is at least a second element
            second_item = data[1]  # Get the second dictionary (index 1)
            price = second_item.get('price')  # Extract the price value
            int_price = int(price)
            if int_price is not None:
                hex_number = hex(int_price)  # Convert the decimal price to hex
                print(f"Price in Decimal: {int_price}, Price in Hex: {hex_number}")
                return hex_number
            else:
                print("Price not found in the second dictionary")
                return None
        else:
            print("Second dictionary not found in the response")
            return None

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
                "chainId": 8453,
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
            "chain_id": "base",
            "tx": {
                "chainId": 8453,
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
            "chain_id": "base",
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

    async def post_tx_is_gasless(self, gas_used: int, pre_exec_success: bool, token_id: str, encoded_data: str,
                                 gas_hex: str, nonce: str):
        payload = {
            "gas_used": gas_used,
            "pre_exec_success": pre_exec_success,
            "tx": {
                "chainId": 8453,
                "from": self.address,
                "to": token_id,
                "data": encoded_data,
                "gas": gas_hex,
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

    async def get_festats_info(self):
        async with httpx.AsyncClient() as client:
            response = await client.get(self.festats_pre_exec_url, headers=self.eth_rpc_headers)

            if response.status_code == 200:
                data = response.json()
                print("Festats Info:", data)
                return data
            else:
                print(f"Failed to get festats info: {response.status_code}")
                return None

    async def get_festats_sign_info(self):
        async with httpx.AsyncClient() as client:
            response = await client.get(self.festats_sign_url, headers=self.eth_rpc_headers)

            if response.status_code == 200:
                data = response.json()
                print("Festats Sign Info:", data)
                return data
            else:
                print(f"Failed to get festats sign info: {response.status_code}")
                return None

    async def post_submit_tx(self, token_id: str, encoded_data: str, gas_hex: str, nonce: str, r: str, s: str, v: str,
                             log_id: int):

        w3 = Web3(Web3.HTTPProvider("rpc_which_user_request or from my dictionary"))
        wallet = w3.eth.account.from_key("input from user")

        tx = {
            "from": "0x4deb87910f51804741514406cae71c23f2f9f05d",
            "to": Web3.to_checksum_address("0x176211869ca2b568f2a7d4ee941e073a821ee1ff"),
            "data": "0x095ea7b30000000000000000000000002ad69a0cf272b9941c7ddcada7b0273e9046c4b00000000000000000000000000000000000000000000000000000000000000000",
            "nonce": "0x39",
            "chainId": 59144,
            "gas": "0xfd94",
            "gasPrice": "0x3b20b80",
            "value": "0x0"
        }

        signed_tx = wallet.sign_transaction(tx)
        v = signed_tx.v
        r = signed_tx.r
        s = signed_tx.s
        payload = {
            "tx": {
                "from": self.address,
                "to": token_id,
                "data": encoded_data,
                "nonce": nonce,
                "chainId": 8453,
                "gas": gas_hex,
                "maxFeePerGas": gas_hex,
                "maxPriorityFeePerGas": "0x10c8e0",
                "r": r,
                "s": s,
                "v": v,
                "value": "0x0"
            },
            "push_type": "default",
            "req_id": "",
            "origin": "chrome-extension://acmacodkjbdgmoleebolmdjonilkdbch",
            "is_gasless": False,
            "log_id": log_id
        }

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
        data = await self.fetch_data()
        if data:
            spender_ids = self.extract_spender_ids(data)

            for item in spender_ids:
                spender_address = item['spender_id']
                token_id = item['token_id']
                encoded_data = await self.encode_approve_data(token_id, spender_address)
                print(f"Token ID: {token_id}, Spender ID: {spender_address}, Encoded Data: {encoded_data}")

                gas_hex = await self.extract_price_and_convert_to_hex()

                nonce = await self.post_eth_rpc_request(
                    {"chain_id": "base", "method": "eth_getTransactionCount", "params": [self.address, "latest"]})

                await self.post_pre_exec_tx(token_id, encoded_data, gas_hex, nonce)

                log_id = await self.post_parse_tx(token_id, encoded_data, gas_hex, nonce)

                await self.post_eth_get_block_by_number()

                await self.get_contract_info(spender_address)

                await self.get_token_info(token_id)

                await self.get_contract_interaction(spender_address)

                await self.post_tx_is_gasless(24059, True, token_id, encoded_data, gas_hex, nonce)

                await self.get_festats_info()

                await self.get_festats_sign_info()

                # TODO get from getting_vrs.py (v,r,s)
                await self.post_submit_tx(token_id, encoded_data, gas_hex, nonce,
                                          "0xd5fe45ae35c312bb849f7380bb4ed5dfba0fb89618509ba0835c2726f0016868",
                                          "0x31a7f83b4cc491bdbc277aa2cfa2d8943c861db0b9304dd3987ab37932278e2b", "0x01",
                                          log_id)
