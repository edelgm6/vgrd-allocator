import csv
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict

import yaml


def get_config(path: str) -> Dict[str, Dict[str, Any]]:
    # Load the YAML configuration file
    with open(path, "r") as config_file:
        config = yaml.safe_load(config_file)

    return config


def get_balance_file_path() -> Path:
    # Define file paths
    local_balance_path = Path("balances_local.csv")
    fallback_balance_path = Path("balances.csv")

    # Determine which file to use
    balance_file_path = (
        local_balance_path if local_balance_path.exists() else fallback_balance_path
    )

    return balance_file_path


def get_balance_dictionary(balance_file_path: Path) -> Dict[str, Decimal]:
    # Dictionary to store results
    symbol_balance: Dict[str, Decimal] = {}

    # Open the CSV file
    cash_symbol = "VMFXX"
    with open(balance_file_path, mode="r", newline="") as file:
        reader = csv.reader(file)
        next(reader)

        # Iterate through rows
        for row in reader:
            if not row:
                break

            symbol = row[2]
            balance_str = row[5]

            if not symbol == cash_symbol:
                balance = Decimal(balance_str)
                symbol_balance[symbol] = balance

    return symbol_balance


def get_category_totals(
    symbol_balances: Dict[str, Decimal], categories: Dict[str, str]
) -> Dict[str, Decimal]:
    # Aggregate balances by category
    category_totals = {category: Decimal(0) for category in categories}
    for category, symbols in categories.items():
        for symbol in symbols:
            category_totals[category] += symbol_balances.get(symbol, Decimal(0))

    return category_totals


def prompt_for_investment_amount() -> Decimal:
    # Prompt for investment amount
    investment_amount_str = input("\nEnter the amount you want to invest: $")
    investment_amount_str = investment_amount_str.replace(",", "")
    # Remove commas and convert to an integer
    investment_amount = Decimal(investment_amount_str)
    return investment_amount


def get_desired_balances(
    investment_amount: Decimal,
    total_balance: Decimal,
    target_allocation: Dict[str, Decimal],
) -> Dict[str, Decimal]:
    # Calculate the desired total balance after the investment
    new_total_balance = total_balance + investment_amount

    # Calculate the desired balances for each category based on the target allocation
    desired_balances = {
        category: new_total_balance * allocation
        for category, allocation in target_allocation.items()
    }

    return desired_balances


def main():
    # File paths
    balance_file_path = get_balance_file_path()
    config_file_path = "config.yaml"
    config = get_config(path=config_file_path)

    categories = config["categories"]
    target_allocation = {
        key: Decimal(value) for key, value in config["target_allocation"].items()
    }

    symbol_balances = get_balance_dictionary(balance_file_path=balance_file_path)
    category_totals = get_category_totals(
        symbol_balances=symbol_balances, categories=categories
    )

    # Print results
    print("Balances by Security:")
    for symbol, balance in symbol_balances.items():
        print(f"{symbol}: ${balance:,.2f}")
    print(f"Total Balance from Securities: ${sum(symbol_balances.values()):,.2f}")

    print("\nBalances by Category:")
    for category, total in category_totals.items():
        print(f"{category}: ${total:,.2f}")

    print("\nTarget Allocation vs. Current Allocation:")
    total_balance = Decimal(sum(category_totals.values()))
    for category, target in target_allocation.items():
        current_allocation = category_totals.get(category, Decimal(0)) / total_balance
        print(f"{category}: Target = {target:.2%}, Current = {current_allocation:.2%}")
    print(f"Total Balance: ${total_balance:,.2f}")

    investment_amount = prompt_for_investment_amount()

    desired_balances = get_desired_balances(
        investment_amount=investment_amount,
        total_balance=total_balance,
        target_allocation=target_allocation,
    )

    # Calculate how much more needs to be invested in each category to meet the target allocation
    needed_investments = {
        category: max(
            desired_balances[category] - category_totals[category], Decimal(0)
        )
        for category in categories
    }

    # Additive logic: distribute the investment proportionally if the total exceeds the available amount
    total_needed = sum(needed_investments.values())
    if total_needed > investment_amount:
        for category in needed_investments:
            needed_investments[category] = investment_amount * (
                needed_investments[category] / total_needed
            )

    # Add investments to current totals to compute the resulting allocation
    resulting_totals = {
        category: category_totals[category] + needed_investments[category]
        for category in categories
    }
    resulting_total_balance = sum(resulting_totals.values())

    # Calculate resulting allocation percentages
    resulting_allocations = {
        category: resulting_totals[category] / resulting_total_balance
        for category in categories
    }

    # Print the investment allocation
    print("\nRecommended Investment Allocation:")
    for category, investment in needed_investments.items():
        print(f"{category}: ${investment:,.2f}")

    # Print the resulting allocation percentages
    print("\nResulting Allocation After Investment:")
    for category, allocation in resulting_allocations.items():
        print(f"{category}: {allocation:.2%}")


if __name__ == "__main__":
    main()
