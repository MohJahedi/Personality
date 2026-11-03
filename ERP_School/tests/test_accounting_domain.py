import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from erp_school.modules.accounting.domain import InvalidJournal, JournalEntry, Posting


class JournalTests(unittest.TestCase):
    def test_balanced_multiline_entry_is_independent_of_student_data(self):
        entry = JournalEntry((Posting('cash', debit=100), Posting('bank', debit=50), Posting('income', credit=150)))
        self.assertEqual(sum(line.debit for line in entry.postings), 150)

    def test_invalid_amounts_and_unbalanced_entries_are_rejected(self):
        for amount in (0, -1, 1.5, True, '100'):
            with self.subTest(amount=amount), self.assertRaises(InvalidJournal):
                JournalEntry.pair('cash', 'income', amount)
        with self.assertRaises(InvalidJournal):
            JournalEntry((Posting('cash', debit=100), Posting('income', credit=90)))
        with self.assertRaises(InvalidJournal):
            JournalEntry.pair('cash', 'cash', 100)
