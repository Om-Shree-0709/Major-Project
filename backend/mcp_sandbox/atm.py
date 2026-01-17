class ATM:
    def __init__(self):
        self.balance = 0
        self.transactions = []

    def deposit(self, amount):
        if amount > 0:
            self.balance += amount
            self.transactions.append(f"Deposited: ${amount}")
            print(f"${amount} deposited successfully. New balance: ${self.balance}")
        else:
            print("Deposit amount must be positive.")

    def withdraw(self, amount):
        if amount > 0:
            if self.balance >= amount:
                self.balance -= amount
                self.transactions.append(f"Withdrew: ${amount}")
                print(f"${amount} withdrawn successfully. New balance: ${self.balance}")
            else:
                print("Insufficient funds.")
        else:
            print("Withdrawal amount must be positive.")

    def check_balance(self):
        print(f"Current balance: ${self.balance}")

    def view_transactions(self):
        if not self.transactions:
            print("No transactions yet.")
        else:
            print("Transaction History:")
            for transaction in self.transactions:
                print(f"- {transaction}")

def main():
    atm = ATM()
    while True:
        print("\nATM Menu:")
        print("1. Deposit")
        print("2. Withdraw")
        print("3. Check Balance")
        print("4. View Transactions")
        print("5. Exit")

        choice = input("Enter your choice: ")

        if choice == '1':
            try:
                amount = float(input("Enter amount to deposit: "))
                atm.deposit(amount)
            except ValueError:
                print("Invalid amount. Please enter a number.")
        elif choice == '2':
            try:
                amount = float(input("Enter amount to withdraw: "))
                atm.withdraw(amount)
            except ValueError:
                print("Invalid amount. Please enter a number.")
        elif choice == '3':
            atm.check_balance()
        elif choice == '4':
            atm.view_transactions()
        elif choice == '5':
            print("Thank you for using the ATM. Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
