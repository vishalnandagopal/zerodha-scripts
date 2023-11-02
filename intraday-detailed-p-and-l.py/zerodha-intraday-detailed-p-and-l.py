from csv import reader
from os import path
from os.path import dirname
from pathlib import Path

from colorama import Fore


def redify(string: str) -> str:
    return f"{Fore.RED}{string}{Fore.RESET}"


def greenify(string: str) -> str:
    return f"{Fore.GREEN}{string}{Fore.RESET}"


def yellowify(string: str) -> str:
    return f"{Fore.YELLOW}{string}{Fore.RESET}"


class Ticker:
    def __init__(self, ticker: str):
        self.ticker: str = ticker
        self.buy_price: float = 0
        self.sell_price: float = 0
        self.total_charges: float = 0
        # Quantity does not actually matter. If trading 10 stocks of 100, can consider it as 1 of 1000. Only net qt matters
        self.total_transactions: int = 0
        self.net_qt: float = 0
        self.net_profit: float = 0

    def buy(self, price: float, qt: float):
        self.buy_price += round((price * qt), 2)
        self.total_charges += Ticker.calculate_charges_on_buy(price * qt)
        self.net_qt += qt
        self.total_transactions += 1

    def sell(self, price: float, qt: float):
        self.sell_price += round((price * qt), 2)
        self.total_charges += Ticker.calculate_charges_on_sell(price * qt)
        self.net_qt -= qt
        self.total_transactions += 1

    def __str__(self) -> str:
        return f"{self.ticker} bought for {self.buy_price} and sold for {self.sell_price}. Net Qt = {self.net_qt}"

    def calculate_brokerage(price) -> float:
        # Includes 18% GST
        return round(
            (round((price * 0.0003), 2) if price * 0.0003 < 20 else 20) * 1.18, 2
        )

    def calculate_charges(price) -> float:
        # I do most of my trades on the NSE (because of the volume), so I am assuming all the trades in the CSV have been executed on the NSE.
        # This assumption is neccessary since there is no exchange field to indicate which exchange the transaction was carried out on, and due to the difference in exchange transaction charges (0.00325% on NSE vs 0.00375 on BSE)
        # There is also an 0.0001% investor protection fund charges by NSE

        exchange_transaction_charges = round((price * (0.0000325 + 0.000001)), 2)

        sebi_charges = round((price * 0.000001), 2)
        # Adding GST and returning
        return round((1.18 * (sebi_charges + exchange_transaction_charges)), 2)

    def calculate_charges_on_buy(price: float) -> float:
        buy_brokerage: float = Ticker.calculate_brokerage(price)
        stamp_charges = round((price * 0.00003), 2)
        common_charges = Ticker.calculate_charges(price)
        return buy_brokerage + stamp_charges + common_charges

    def calculate_charges_on_sell(price: float) -> float:
        sell_brokerage: float = Ticker.calculate_brokerage(price)

        securities_transaction_tax: float = round((price * 0.00025), 2)

        common_charges = Ticker.calculate_charges(price)

        return sell_brokerage + securities_transaction_tax + common_charges

    def calculate_net_profit(self) -> float:
        if self.net_qt == 0:
            self.net_profit = round(
                (self.sell_price - self.buy_price) - self.total_charges, 2
            )
        else:
            self.net_profit = 0
            raise RuntimeError(
                redify(
                    f"Net profit is being calculated when net qt for {self.ticker} is not 0. Check again!"
                )
            )
        return self.net_profit

    def get_colored_string(price) -> str:
        price = round(price, 2)
        return greenify(f"+{price}") if price > 0 else redify(price)

    def get_profit_or_loss_string(self) -> str:
        profit_or_loss_string = Ticker.get_colored_string(self.net_profit)
        turnover = self.buy_price + self.sell_price
        return f"\n{yellowify(ticker)}\n    Net P&L : {profit_or_loss_string}\n    Turnover: {turnover}\n    ~20%: {round((turnover/all_tickers[ticker].total_transactions)* 0.2)}"


all_tickers: dict[str, Ticker] = dict()


if "orders.csv" in dirname(__file__):
    orders_file = dirname(__file__) + "/" + "orders.csv"
else:
    # Assumes your downloads folder is in the normal place and not like C:\Users\V\OneDrive\Photos\Downloads
    orders_file = path_to_download_folder = (
        path.join(Path.home(), "Downloads") + "/" + "orders.csv"
    )

with open(orders_file, "r") as f:
    csv_reader = reader(f)

    # Ignore header
    next(csv_reader)

    for row in csv_reader:
        ticker = row[2]
        if row[3] == "MIS" and row[6] == "COMPLETE":
            price = float(row[5])
            qt = float(row[4].split("/")[0])
            if ticker not in all_tickers:
                all_tickers[row[2]] = Ticker(ticker)
            if row[1] == "SELL":
                all_tickers[ticker].sell(price, qt)
            elif row[1] == "BUY":
                all_tickers[row[2]].buy(price, qt)
    days_profit: float = 0
    days_charges_paid: float = 0
    for ticker in all_tickers:
        _ = all_tickers[ticker]
        _.calculate_net_profit()

        print(_.get_profit_or_loss_string())

        days_profit += _.net_profit
        days_charges_paid += _.total_charges
    print(
        f"\nCharges Paid (Included in above P&L calc): {Ticker.get_colored_string(-price)}\n\nDay's P&L: {Ticker.get_colored_string(days_profit)}"
    )
