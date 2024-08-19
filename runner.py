from src.contract_revoke import ApproverManager
from src.single_revoke import TokenAuthorizedListFetcher
from src.mass_revoke import MassTokenAuthorizedListFetcher


def load_private_keys(file_path='keys.txt'):
    with open(file_path, 'r') as file:
        keys = [line.strip() for line in file.readlines() if line.strip()]
    return keys


async def run_contract_revoke():
    private_keys = load_private_keys()
    if not private_keys:
        print("No private keys found in keys.txt")
        return
    for private_key in private_keys:
        manager = ApproverManager(private_key)
        await manager.main()


async def run_single_rabby_revoke():
    private_keys = load_private_keys()
    if not private_keys:
        print("No private keys found in keys.txt")
        return
    for private_key in private_keys:
        chain = input("Write chain: ")
        manager_2 = TokenAuthorizedListFetcher(chain, private_key)
        await manager_2.run()


async def run_mass_rabby_revoke():
    private_keys = load_private_keys()
    if not private_keys:
        print("No private keys found in keys.txt")
        return
    for private_key in private_keys:
        manager_3 = MassTokenAuthorizedListFetcher(private_key)
        await manager_3.run()
