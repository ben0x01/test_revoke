import asyncio
from runner import run_contract_revoke, run_single_rabby_revoke, run_mass_rabby_revoke


def main_menu():
    print("Main Menu")
    print("1. Run revoke with contract")
    print("2. Run single revoke from rabby")
    print("3. Run mass revoke from rabby")
    print("4. Exit")


    choice = input("Choose an option: ").strip()

    if choice == '1':
        private_key = input("Enter your private key: ").strip()
        asyncio.run(run_contract_revoke(private_key))
    elif choice == '2':
        asyncio.run(run_single_rabby_revoke())
    elif choice == '3':
        asyncio.run(run_mass_rabby_revoke())
    elif choice == '4':
        print("Exiting...")
        return
    else:
        print("Invalid choice. Please try again.")
        main_menu()


if __name__ == "__main__":
    main_menu()
