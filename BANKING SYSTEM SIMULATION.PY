import datetime
import json
import random
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from pathlib import Path  # <<< ADDED THIS IMPORT

# --- Helper Functions for Robustness ---


def get_float_input(prompt: str) -> Optional[float]:
    """Safely prompts the user for a positive floating-point number."""
    while True:
        try:
            value_str = input(prompt).strip()
            if not value_str:
                return None
            value = float(value_str)
            if value <= 0:
                print("Amount must be positive.")
                continue
            return value
        except ValueError:
            print("Invalid input. Please enter a numerical amount.")


# --- Account Classes ---


class Account(ABC):
    """Abstract base class for all account types"""

    def __init__(
        self,
        account_number: str,
        account_holder: str,
        customer_id: str,
        balance: float = 0.0,
    ):
        self.account_number = account_number
        self.account_holder = account_holder
        self.customer_id = customer_id  # Added customer_id for explicit linkage
        self.balance = balance
        self.transactions: List[Dict] = []
        self.account_type = "Generic"

    @abstractmethod
    def calculate_interest(self):
        pass

    def deposit(self, amount: float) -> bool:
        if amount > 0:
            self.balance += amount
            self._record_transaction("DEPOSIT", amount, "Deposit")
            return True
        return False

    def withdraw(self, amount: float) -> bool:
        # Generic withdrawal logic (can be overridden by subclasses)
        if amount > 0 and self.balance >= amount:
            self.balance -= amount
            self._record_transaction("WITHDRAWAL", amount, "Withdrawal")
            return True
        return False

    def _record_transaction(
        self, transaction_type: str, amount: float, description: str
    ):
        transaction = {
            "date": datetime.datetime.now().isoformat(),
            "type": transaction_type,
            "amount": amount,
            "description": description,
            "balance_after": self.balance,
        }
        self.transactions.append(transaction)

    def get_transaction_history(self) -> List[Dict]:
        return self.transactions

    def __str__(self):
        return (
            f"| {self.account_type} Account: {self.account_number}\n"
            f"| Holder: {self.account_holder} (Customer ID: {self.customer_id})\n"
            f"| Balance: ${self.balance:,.2f}"
        )


class SavingsAccount(Account):
    """Savings account with interest calculation"""

    def __init__(
        self,
        account_number: str,
        account_holder: str,
        customer_id: str,
        balance: float = 0.0,
        interest_rate: float = 0.02,
    ):
        super().__init__(account_number, account_holder, customer_id, balance)
        self.interest_rate = interest_rate
        self.account_type = "Savings"

    def calculate_interest(self) -> float:
        return self.balance * self.interest_rate

    def apply_interest(self):
        interest = self.calculate_interest()
        if interest > 0:
            self.balance += interest
            self._record_transaction(
                "INTEREST",
                interest,
                f"Interest applied @ {self.interest_rate*100:.2f}%",
            )
            print(f"Applied ${interest:,.2f} interest to account {self.account_number}")


class CheckingAccount(Account):
    """Checking account with overdraft protection"""

    def __init__(
        self,
        account_number: str,
        account_holder: str,
        customer_id: str,
        balance: float = 0.0,
        overdraft_limit: float = 100.0,
    ):
        super().__init__(account_number, account_holder, customer_id, balance)
        self.overdraft_limit = overdraft_limit
        self.account_type = "Checking"

    def calculate_interest(self) -> float:
        return 0  # Checking accounts typically don't earn interest

    def withdraw(self, amount: float) -> bool:
        new_balance = self.balance - amount

        # Check if withdrawal is valid considering the overdraft limit
        if amount > 0 and new_balance >= -self.overdraft_limit:
            self.balance = new_balance

            description = "Withdrawal"
            if new_balance < 0:
                description += " (Overdraft Used)"

            self._record_transaction("WITHDRAWAL", amount, description)
            return True

        # Check specific failure reasons for better feedback
        if amount <= 0:
            return False
        if new_balance < -self.overdraft_limit:
            print(
                f"Withdrawal failed: Exceeds overdraft limit of ${self.overdraft_limit:,.2f}."
            )
        return False


# --- Customer and Bank Classes ---


class Customer:
    """Customer class to manage customer information and accounts"""

    def __init__(self, customer_id: str, name: str, email: str, phone: str):
        self.customer_id = customer_id
        self.name = name
        self.email = email
        self.phone = phone
        self.accounts: Dict[str, Account] = {}

    def add_account(self, account: Account):
        self.accounts[account.account_number] = account

    def remove_account(self, account_number: str) -> Optional[Account]:
        return self.accounts.pop(account_number, None)

    def get_account(self, account_number: str) -> Optional[Account]:
        return self.accounts.get(account_number)

    def get_all_accounts(self) -> List[Account]:
        return list(self.accounts.values())

    def __str__(self):
        return (
            f"Customer: {self.name} (ID: {self.customer_id})\n"
            f"Contact: {self.email} | {self.phone}\n"
            f"Total Accounts: {len(self.accounts)}"
        )


class Bank:
    """Main banking system class"""

    def __init__(self, name: str):
        self.name = name
        self.customers: Dict[str, Customer] = {}
        self.accounts: Dict[str, Account] = {}

    def generate_account_number(self) -> str:
        """Generate a unique 10-digit account number"""
        # Using a fixed starting point for slightly better determinism than pure random
        prefix = str(int(datetime.datetime.now().timestamp()))[-4:]
        while True:
            account_number = f"1{prefix}{random.randint(100000, 999999)}"
            if account_number not in self.accounts:
                return account_number

    def generate_customer_id(self) -> str:
        """Generate a unique customer ID"""
        # Improved customer ID generation
        while True:
            customer_id = f"C{random.randint(10000, 99999)}"
            if customer_id not in self.customers:
                return customer_id

    def create_customer(self, name: str, email: str, phone: str) -> Customer:
        """Create a new customer"""
        customer_id = self.generate_customer_id()
        customer = Customer(customer_id, name, email, phone)
        self.customers[customer_id] = customer
        return customer

    def create_account(
        self,
        customer_id: str,
        account_type: str,
        initial_deposit: float = 0.0,
        **kwargs,
    ) -> Optional[Account]:
        """Create a new account for a customer"""
        customer = self.customers.get(customer_id)
        if not customer:
            return None

        account_number = self.generate_account_number()

        account: Optional[Account] = None

        if account_type.upper() == "SAVINGS":
            interest_rate = kwargs.get("interest_rate", 0.02)
            account = SavingsAccount(
                account_number,
                customer.name,
                customer_id,
                initial_deposit,
                interest_rate,
            )
        elif account_type.upper() == "CHECKING":
            overdraft_limit = kwargs.get("overdraft_limit", 100.0)
            account = CheckingAccount(
                account_number,
                customer.name,
                customer_id,
                initial_deposit,
                overdraft_limit,
            )
        else:
            return None

        customer.add_account(account)
        self.accounts[account_number] = account
        return account

    def remove_account(self, account_number: str) -> bool:
        """Remove an account and unlink it from the customer."""
        account = self.accounts.pop(account_number, None)
        if account:
            customer = self.customers.get(account.customer_id)
            if customer:
                customer.remove_account(account_number)
            return True
        return False

    def get_customer(self, customer_id: str) -> Optional[Customer]:
        return self.customers.get(customer_id)

    def get_account(self, account_number: str) -> Optional[Account]:
        return self.accounts.get(account_number)

    def transfer_funds(self, from_account: str, to_account: str, amount: float) -> bool:
        """Transfer funds between accounts with rollback integrity."""
        source = self.get_account(from_account)
        destination = self.get_account(to_account)

        if (
            not source
            or not destination
            or source.account_number == destination.account_number
        ):
            return False

        # Attempt withdrawal (handles insufficient funds/overdraft checks)
        if source.withdraw(amount):
            # Attempt deposit
            if destination.deposit(amount):
                # Record specific transfer transaction types
                source._record_transaction(
                    "TRANSFER_OUT", amount, f"Transfer to {to_account}"
                )
                destination._record_transaction(
                    "TRANSFER_IN", amount, f"Transfer from {from_account}"
                )
                return True
            else:
                # ROLLBACK: If deposit fails (shouldn't happen with valid amount > 0), refund the withdrawal
                source.deposit(amount)
                return False
        return False

    def apply_interest_to_all_savings(self):
        """Apply interest to all savings accounts"""
        count = 0
        for account in self.accounts.values():
            if isinstance(account, SavingsAccount):
                account.apply_interest()
                count += 1
        return count

    def get_total_deposits(self) -> float:
        """Get total deposits across all accounts"""
        return sum(account.balance for account in self.accounts.values())

    # --- MODIFIED FILE OPERATIONS START ---
    def save_to_file(self, filename: str):
        """Save bank data to JSON file using absolute path relative to the script."""

        # 1. Determine the path of the JSON file relative to the current script
        # This resolves the CWD issue by ensuring the path is always the script's directory
        data_path = Path(__file__).resolve().parent / filename  # <<< PATHLIB CHANGE

        data: Dict[str, Any] = {"name": self.name, "customers": {}, "accounts": {}}

        # Save Customers
        for customer_id, customer in self.customers.items():
            data["customers"][customer_id] = {
                "name": customer.name,
                "email": customer.email,
                "phone": customer.phone,
                "account_numbers": list(
                    customer.accounts.keys()
                ),  # Customer knows their accounts
            }

        # Save Accounts (includes custom attributes like interest_rate/overdraft_limit)
        for account_number, account in self.accounts.items():
            account_data: Dict[str, Any] = {
                "account_holder": account.account_holder,
                "customer_id": account.customer_id,  # Crucial for re-linking
                "balance": account.balance,
                "account_type": account.account_type,
                "transactions": account.transactions,
            }
            if isinstance(account, SavingsAccount):
                account_data["interest_rate"] = account.interest_rate
            elif isinstance(account, CheckingAccount):
                account_data["overdraft_limit"] = account.overdraft_limit

            data["accounts"][account_number] = account_data

        with open(data_path, "w") as f:  # <<< Using data_path
            json.dump(data, f, indent=2)

    def load_from_file(self, filename: str):
        """Load bank data from JSON file with proper object recreation and linking."""

        # 1. Determine the path of the JSON file relative to the current script
        data_path = Path(__file__).resolve().parent / filename  # <<< PATHLIB CHANGE

        try:
            # Open the file using the absolute path
            with open(data_path, "r") as f:  # <<< Using data_path
                data = json.load(f)

            self.name = data.get("name", "Unknown Bank")
            self.customers = {}
            self.accounts = {}

            # 1. Recreate customers (must happen first)
            for customer_id, customer_data in data.get("customers", {}).items():
                customer = Customer(
                    customer_id,
                    customer_data.get("name", "N/A"),
                    customer_data.get("email", "N/A"),
                    customer_data.get("phone", "N/A"),
                )
                self.customers[customer_id] = customer

            # 2. Recreate accounts and link to customers
            for account_number, account_data in data.get("accounts", {}).items():
                customer_id = account_data.get("customer_id")
                customer = self.customers.get(customer_id)

                if not customer:
                    print(
                        f"Warning: Account {account_number} has an unknown customer ID ({customer_id}). Skipping."
                    )
                    continue

                account: Optional[Account] = None
                acc_type = account_data.get("account_type")

                if acc_type == "Savings":
                    account = SavingsAccount(
                        account_number,
                        account_data["account_holder"],
                        customer_id,
                        account_data["balance"],
                        account_data.get("interest_rate", 0.02),
                    )
                elif acc_type == "Checking":
                    account = CheckingAccount(
                        account_number,
                        account_data["account_holder"],
                        customer_id,
                        account_data["balance"],
                        account_data.get("overdraft_limit", 100.0),
                    )

                if account:
                    account.transactions = account_data.get("transactions", [])
                    self.accounts[account_number] = account
                    customer.add_account(account)  # Link account back to customer

            print(f"\nData loaded successfully! Bank: {self.name}")
            print(
                f"Loaded {len(self.customers)} customers and {len(self.accounts)} accounts."
            )

        except FileNotFoundError:
            print("\nNo saved data found. Starting fresh.")
        except json.JSONDecodeError:
            print("\nError: The data file is corrupted or not a valid JSON format.")
        except Exception as e:
            print(f"\nAn unexpected error occurred while loading data: {e}")

    # --- MODIFIED FILE OPERATIONS END ---


# --- Banking System Interface ---


class BankingSystem:
    """User interface for the banking system"""

    def __init__(self):
        self.bank = Bank("Python Banking System")

    def display_menu(self):
        """Display main menu"""
        print("\n" + "=" * 50)
        print(f"🏦 {self.bank.name} 🏦")
        print("=" * 50)
        print("1. Create Customer")
        print("2. Create Account")
        print("3. Deposit")
        print("4. Withdraw")
        print("5. Transfer Funds")
        print("6. View Account Details")
        print("7. View Transaction History")
        print("8. **Bank Operations** (Interest/Stats)")
        print("9. Close Account")
        print("10. Save Data")
        print("11. Load Data")
        print("12. Exit")
        print("=" * 50)

    def run(self):
        """Main application loop"""
        print("Welcome to the Python Banking System!")

        while True:
            self.display_menu()
            choice = input("Enter your choice (1-12): ").strip()

            try:
                if choice == "1":
                    self.create_customer()
                elif choice == "2":
                    self.create_account()
                elif choice == "3":
                    self.deposit()
                elif choice == "4":
                    self.withdraw()
                elif choice == "5":
                    self.transfer_funds()
                elif choice == "6":
                    self.view_account_details()
                elif choice == "7":
                    self.view_transaction_history()
                elif choice == "8":
                    self.bank_operations_menu()
                elif choice == "9":
                    self.close_account()
                elif choice == "10":
                    self.save_data()
                elif choice == "11":
                    self.load_data()
                elif choice == "12":
                    print("Thank you for using Python Banking System! Goodbye! 👋")
                    break
                else:
                    print("\n❌ Invalid choice. Please try again.")

            except Exception as e:
                print(f"\n⚠️ An unexpected error occurred: {e}")

    # --- UI Methods ---

    def create_customer(self):
        """Create a new customer"""
        print("\n--- Create New Customer ---")
        name = input("Enter full name: ").strip()
        email = input("Enter email: ").strip()
        phone = input("Enter phone number: ").strip()

        if not name or not email:
            print("Customer creation failed: Name and email cannot be empty.")
            return

        customer = self.bank.create_customer(name, email, phone)
        print(
            f"✅ Customer created successfully! Name: {customer.name}, ID: **{customer.customer_id}**"
        )

    def create_account(self):
        """Create a new account"""
        print("\n--- Create New Account ---")
        customer_id = input("Enter customer ID: ").strip()

        customer = self.bank.get_customer(customer_id)
        if not customer:
            print(f"❌ Customer with ID '{customer_id}' not found!")
            return

        print(f"Customer: {customer.name}")
        print("Available account types: 1. Savings (2%) | 2. Checking ($100 OD)")

        acc_type_choice = input("Choose account type (1/2): ").strip()

        initial_deposit = get_float_input("Enter initial deposit amount: $")
        if initial_deposit is None:
            initial_deposit = 0.0  # Allow 0 initial deposit

        account = None

        if acc_type_choice == "1":
            account = self.bank.create_account(customer_id, "SAVINGS", initial_deposit)
        elif acc_type_choice == "2":
            account = self.bank.create_account(customer_id, "CHECKING", initial_deposit)
        else:
            print("❌ Invalid account type choice!")
            return

        if account:
            print(
                f"✅ Account created successfully! Type: {account.account_type}, Number: **{account.account_number}**"
            )
        else:
            print("❌ Failed to create account!")

    def deposit(self):
        """Deposit money into account"""
        print("\n--- Deposit Money ---")
        account_number = input("Enter account number: ").strip()
        amount = get_float_input("Enter amount to deposit: $")

        if amount is None:
            print("Deposit cancelled.")
            return

        account = self.bank.get_account(account_number)
        if account:
            if account.deposit(amount):
                print(
                    f"✅ Deposit of ${amount:,.2f} successful! New balance: ${account.balance:,.2f}"
                )
            else:
                print("❌ Deposit failed! Amount must be positive.")
        else:
            print("❌ Deposit failed! Account not found.")

    def withdraw(self):
        """Withdraw money from account"""
        print("\n--- Withdraw Money ---")
        account_number = input("Enter account number: ").strip()
        amount = get_float_input("Enter amount to withdraw: $")

        if amount is None:
            print("Withdrawal cancelled.")
            return

        account = self.bank.get_account(account_number)
        if account:
            if account.withdraw(amount):
                print(
                    f"✅ Withdrawal of ${amount:,.2f} successful! New balance: ${account.balance:,.2f}"
                )
            else:
                print(
                    "❌ Withdrawal failed! Insufficient funds or amount exceeds overdraft limit."
                )
        else:
            print("❌ Withdrawal failed! Account not found.")

    def transfer_funds(self):
        """Transfer funds between accounts"""
        print("\n--- Transfer Funds ---")
        from_account = input("Enter source account number: ").strip()
        to_account = input("Enter destination account number: ").strip()
        amount = get_float_input("Enter amount to transfer: $")

        if amount is None:
            print("Transfer cancelled.")
            return

        if self.bank.transfer_funds(from_account, to_account, amount):
            print(
                f"✅ Transfer of ${amount:,.2f} from {from_account} to {to_account} successful!"
            )
        else:
            print("❌ Transfer failed! Check account numbers and sufficient balance.")

    def view_account_details(self):
        """View account details"""
        print("\n--- Account Details ---")
        account_number = input("Enter account number: ").strip()

        account = self.bank.get_account(account_number)
        if account:
            print(f"\n{account}")
            if isinstance(account, SavingsAccount):
                print(f"| Interest Rate: {account.interest_rate*100:.2f}%")
            elif isinstance(account, CheckingAccount):
                print(f"| Overdraft Limit: ${account.overdraft_limit:,.2f}")
        else:
            print("❌ Account not found!")

    def view_transaction_history(self):
        """View transaction history"""
        print("\n--- Transaction History ---")
        account_number = input("Enter account number: ").strip()

        account = self.bank.get_account(account_number)
        if account:
            transactions = account.get_transaction_history()
            if not transactions:
                print("No transactions found.")
            else:
                print("-" * 50)
                print(f"History for Account: {account_number}")
                print("-" * 50)
                for i, transaction in enumerate(transactions, 1):
                    # Robust datetime parsing
                    try:
                        dt = datetime.datetime.fromisoformat(transaction["date"])
                        date_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        date_str = transaction["date"]  # Fallback to raw string

                    amount_str = f"${transaction['amount']:,.2f}"
                    balance_str = f"Balance: ${transaction['balance_after']:,.2f}"

                    print(
                        f"[{i:02}] {date_str} | {transaction['type']:<12} | {amount_str:<12} | {transaction['description']:<30} | {balance_str}"
                    )
                print("-" * 50)
        else:
            print("❌ Account not found!")

    def close_account(self):
        """Close an existing account."""
        print("\n--- Close Account ---")
        account_number = input("Enter account number to close: ").strip()
        account = self.bank.get_account(account_number)

        if not account:
            print("❌ Account not found.")
            return

        if account.balance != 0:
            print(
                f"❌ Account **{account_number}** has a remaining balance of ${account.balance:,.2f}."
            )
            print("Please withdraw or transfer the balance before closing.")
            return

        confirm = (
            input(
                f"Are you sure you want to CLOSE account {account_number}? (yes/no): "
            )
            .lower()
            .strip()
        )
        if confirm == "yes":
            if self.bank.remove_account(account_number):
                print(
                    f"✅ Account **{account_number}** for {account.account_holder} has been successfully closed."
                )
            else:
                print("❌ Failed to close account.")
        else:
            print("Account closing cancelled.")

    def bank_operations_menu(self):
        """Menu for interest and statistics"""
        print("\n--- Bank Operations ---")
        print("1. Apply Interest (Savings Accounts)")
        print("2. Bank Statistics")
        op_choice = input("Enter your choice (1/2): ").strip()

        if op_choice == "1":
            self.apply_interest()
        elif op_choice == "2":
            self.show_bank_statistics()
        else:
            print("❌ Invalid choice.")

    def apply_interest(self):
        """Apply interest to savings accounts"""
        print("\n--- Apply Interest ---")
        count = self.bank.apply_interest_to_all_savings()
        print(
            f"✅ Interest application complete. Applied interest to **{count}** savings account(s)."
        )

    def show_bank_statistics(self):
        """Show bank statistics"""
        print("\n--- Bank Statistics ---")
        savings_count = sum(
            1 for acc in self.bank.accounts.values() if isinstance(acc, SavingsAccount)
        )
        checking_count = sum(
            1 for acc in self.bank.accounts.values() if isinstance(acc, CheckingAccount)
        )

        print(f"Total Customers: **{len(self.bank.customers)}**")
        print(f"Total Accounts: **{len(self.bank.accounts)}**")
        print(
            f"Total Deposits (Bank Assets): **${self.bank.get_total_deposits():,.2f}**"
        )
        print(f"  - Savings Accounts: {savings_count}")
        print(f"  - Checking Accounts: {checking_count}")

    def save_data(self):
        """Save data to file"""
        filename = (
            input("Enter filename to save data (default: bank_data.json): ").strip()
            or "bank_data.json"
        )

        try:
            self.bank.save_to_file(filename)
            print(f"✅ Data saved successfully to **{filename}**")
        except Exception as e:
            print(f"❌ Failed to save data: {e}")

    def load_data(self):
        """Load data from file"""
        filename = (
            input("Enter filename to load data (default: bank_data.json): ").strip()
            or "bank_data.json"
        )

        self.bank.load_from_file(filename)


# Sample data for testing
def create_sample_data(bank_system):
    """Create sample data for testing"""
    customer1 = bank_system.bank.create_customer(
        "John Doe", "john@email.com", "555-1234"
    )
    customer2 = bank_system.bank.create_customer(
        "Jane Smith", "jane@email.com", "555-5678"
    )

    s_acc = bank_system.bank.create_account(customer1.customer_id, "SAVINGS", 1000.0)
    c_acc = bank_system.bank.create_account(customer1.customer_id, "CHECKING", 500.0)
    bank_system.bank.create_account(customer2.customer_id, "SAVINGS", 2000.0)

    if s_acc and c_acc:
        s_acc.deposit(500)
        c_acc.withdraw(150)
        bank_system.bank.transfer_funds(s_acc.account_number, c_acc.account_number, 200)

    print("\n✅ Sample data created successfully!")


if __name__ == "__main__":
    banking_system = BankingSystem()

    # Uncomment the next line to create sample data for your initial run
    create_sample_data(banking_system)

    banking_system.run()
