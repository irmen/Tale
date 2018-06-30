"""
Banks.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

import datetime
from collections import defaultdict, deque
import json
from typing import Dict, MutableSequence, Optional

from .. import mud_context
from ..base import Item, Living, ParseResult
from ..errors import ActionRefused


__all__ = ["Bank"]


class Bank(Item):
    max_num_transactions = 1000
    """An item (such as ATM or cash card) that you can deposit and withdraw money from. The money is then safe when you log out."""
    def init(self) -> None:
        super().init()
        self.takeable = False   # can be set to true for instance when it's a credit card
        self.storage_file = ""
        self.verbs = {
            "balance": "See what the balance on your bank account is.",
            "deposit": "Deposit some money into your bank account.",
            "withdraw": "Withdraw some moeny from your bank account."
        }
        self.accounts = defaultdict(float)    # type: Dict[str, float]
        self.transaction_log = deque(maxlen=self.max_num_transactions)   # type: MutableSequence[str]   # py 3.5's don't have typing.Deque

    def allow_item_move(self, actor: Optional[Living], verb: str="move") -> None:
        if not self.takeable:
            raise ActionRefused("The %s won't budge." % self.name)

    def handle_verb(self, parsed: ParseResult, actor: Living) -> bool:
        if parsed.verb == "balance":
            self.do_balance(actor)
            return True
        elif parsed.verb == "deposit" or parsed.verb == "withdraw":
            self.do_transaction(actor, parsed)
            return True
        else:
            return False

    def do_balance(self, actor: Living) -> None:
        balance = self.accounts[actor.name]
        balance_str = mud_context.driver.moneyfmt.display(balance, zero_msg="Your account is empty.")
        actor.tell("The {} reports: 'CURRENT BALANCE: {}'".format(self.name, balance_str))
        return

    def do_transaction(self, actor: Living, parsed: ParseResult) -> None:
        if not parsed.args:
            raise ActionRefused("You forgot to specify the amount of money.")
        amount = mud_context.driver.moneyfmt.parse(parsed.unrecognized)
        if parsed.verb == "deposit":
            if amount <= 0.0:
                raise ActionRefused("That's not a valid amount of money.")
            if amount > actor.money:
                raise ActionRefused("You don't have that much money.")
            old_balance = self.accounts[actor.name]
            self.accounts[actor.name] = round(self.accounts[actor.name] + amount, 7)
            self.log_transaction(actor, parsed.verb, amount, self.accounts[actor.name])
            try:
                assert actor.money >= 0.0 and self.accounts[actor.name] >= 0.0
                self.save()
            except Exception:
                self.accounts[actor.name] = old_balance
                raise
            actor.money -= amount
            amount_str = mud_context.driver.moneyfmt.display(amount)
            actor.tell("You deposited {} into your account.".format(amount_str))
            actor.tell_others("{Actor} makes a bank transaction.")
        elif parsed.verb == "withdraw":
            if amount <= 0.0:
                raise ActionRefused("That's not a valid amount of money.")
            if amount > self.accounts[actor.name]:
                raise ActionRefused("You don't have that much money in your account.")
            old_balance = self.accounts[actor.name]
            self.accounts[actor.name] = round(self.accounts[actor.name] - amount, 7)
            self.log_transaction(actor, parsed.verb, amount, self.accounts[actor.name])
            try:
                assert actor.money >= 0.0 and self.accounts[actor.name] >= 0.0
                self.save()
            except Exception:
                self.accounts[actor.name] = old_balance
                raise
            actor.money += amount
            amount_str = mud_context.driver.moneyfmt.display(amount)
            actor.tell("You withdrew {} from your account.".format(amount_str))
            actor.tell_others("{Actor} makes a bank transaction.")

    def log_transaction(self, actor: Living, what: str, amount: float, balance: float) -> None:
        timestamp = str(datetime.datetime.now())
        amount_str = mud_context.driver.moneyfmt.display(amount, short=True)
        self.transaction_log.append("{timestamp}: {who} {what} {amount} ({amount_str}) -> {balance}"
                                    .format(timestamp=timestamp, who=actor.name, what=what, amount=amount,
                                            amount_str=amount_str, balance=balance))

    def load(self) -> None:
        """Load persisted bank account data from the datafile."""
        if not self.storage_file:
            return
        try:
            data = json.loads(mud_context.driver.user_resources[self.storage_file].text)
            self.accounts = data["accounts"]
            self.transaction_log = deque(data["transactions"], maxlen=self.max_num_transactions)
        except FileNotFoundError:
            pass
        except (ValueError, IOError) as x:
            print("Bank '%s' load error: %s" % (self.name, x))

    def save(self) -> None:
        """Save the bank account data to the data file."""
        if not self.storage_file:
            return
        data = {
            "accounts": self.accounts,
            "transactions": list(self.transaction_log)
        }
        try:
            mud_context.driver.user_resources[self.storage_file] = json.dumps(data, indent=4, sort_keys=True)
        except IOError as x:
            print("Bank '%s' save error: %s" % (self.name, x))
