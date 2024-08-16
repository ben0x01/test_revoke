from src.contract_revoke import ApproverManager
from src.single_revoke import TokenAuthorizedListFetcher

async def run_contract_revoke(private_key):
    manager = ApproverManager(private_key)
    await manager.main()


async def run_single_rabby_revoke():
    address = input("Write wallet address: ")
    chain = input("Write chain: ")
    manager_2 = TokenAuthorizedListFetcher(address, chain)
    await manager_2.run()