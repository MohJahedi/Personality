"""Accounting rules with no dependency on students, HTTP, or persistence."""
from dataclasses import dataclass

class InvalidJournal(ValueError):
    pass

@dataclass(frozen=True)
class Posting:
    account: str
    debit: int = 0
    credit: int = 0

    def __post_init__(self):
        if not isinstance(self.account, str) or not self.account.strip():
            raise InvalidJournal('An account is required.')
        if type(self.debit) is not int or type(self.credit) is not int:
            raise InvalidJournal('Amounts must be integer rial.')
        if self.debit < 0 or self.credit < 0 or bool(self.debit) == bool(self.credit):
            raise InvalidJournal('A line must contain one positive side.')

@dataclass(frozen=True)
class JournalEntry:
    postings: tuple[Posting, ...]

    def __post_init__(self):
        if not isinstance(self.postings, tuple) or len(self.postings) < 2:
            raise InvalidJournal('An entry needs at least two immutable lines.')
        if any(not isinstance(line, Posting) for line in self.postings):
            raise InvalidJournal('Every line must be a Posting.')
        if sum(line.debit for line in self.postings) != sum(line.credit for line in self.postings):
            raise InvalidJournal('Debits must equal credits.')

    @classmethod
    def pair(cls, debit_account: str, credit_account: str, amount: int):
        if debit_account == credit_account:
            raise InvalidJournal('Pair accounts must differ.')
        return cls((Posting(debit_account, debit=amount), Posting(credit_account, credit=amount)))
