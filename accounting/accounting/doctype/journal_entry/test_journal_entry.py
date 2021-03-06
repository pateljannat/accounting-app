# -*- coding: utf-8 -*-
# Copyright (c) 2020, Frappe and Contributors
# See license.txt
from __future__ import unicode_literals

import frappe
import unittest
from accounting.accounting.doctype.accounts.test_accounts import create_account, delete_account
from frappe.utils import nowdate

class TestJournalEntry(unittest.TestCase):

    def setUp(self):
        create_account("ACC-100","_Test Debtors", "Asset", "Assets")
        create_account("ACC-100","_Test Creditors", "Liability", "Liabilities")

    def tearDown(self):
        delete_account("_Test Debtors")
        delete_account("_Test Creditors")
    
    def test_journal_entry_creation(self):

        jv = make_journal_entry("_Test Debtors", "_Test Creditors", "Jannat Patel", 100, True, True)

        gl_entries = get_gl_entries(jv.name, "Journal Entry")
        self.assertTrue(gl_entries)

        self.assertTrue(get_account("_Test Debtors"))

        expected_values = {
            "_Test Debtors": {
                "debit_amount": 100,
                "credit_amount": 0
            },
            "_Test Creditors": {
                "debit_amount": 0,
                "credit_amount": 100
            }
        }

        for field in ("debit_amount", "credit_amount"):
            for i, gle in enumerate(gl_entries):
                self.assertEqual(expected_values[gle.account][field], gle[field])
        
        delete_gl_entries(gl_entries)

        self.assertFalse(get_gl_entries(jv.name, "Journal Entry"))

        jv.cancel()
        jv.delete()

    def test_jv_validations(self):
        jv = make_journal_entry("_Test Debtors", "_Test Creditors", "Jannat Patel", 100, False, False)
        jv.accounting_entries[0].update({
            "debit": 200
        })
        self.assertRaises(frappe.exceptions.ValidationError, jv.insert)

        jv.accounting_entries[0].update({
            "debit": 100
        })
        jv.insert()
        jv_entry = frappe.db.sql(""" select * from `tabJournal Entry` where name=%s """, jv.name, as_dict=1)
        self.assertTrue(jv_entry)
        jv.delete()

    def test_reverse_ledger_entry(self):
        jv = make_journal_entry("_Test Debtors", "_Test Creditors", "Jannat Patel", 100, True, True)

        gl_entries = get_gl_entries(jv.name, "Journal Entry")
        original_gl_entries_count = len(gl_entries)

        jv.cancel();
        gl_entries = get_gl_entries(jv.name, "Journal Entry")

        self.assertTrue(len(gl_entries)/2 == original_gl_entries_count)

        for gl in gl_entries:
            self.assertTrue(gl.is_cancelled)
        
        delete_gl_entries(gl_entries)
        jv.delete()

def make_journal_entry(account1, account2, party, amount, save=True, submit=False ):
    jv = frappe.new_doc("Journal Entry")
    jv.party = party
    jv.posting_date = nowdate()
    jv.payment_due_date = nowdate()
    jv.set("accounting_entries",[
        {
            "account": account1,
            "debit": amount if amount > 0 else 0,
            "credit": abs(amount) if amount < 0 else 0
        },
        {
            "account": account2,
            "debit": abs(amount) if amount < 0 else 0,
            "credit": amount if amount > 0 else 0
        }
    ])

    if save or submit:
        jv.insert()
        if submit:
            jv.submit()

    return jv

def get_account(name):
    return frappe.db.sql(""" select * from `tabAccounts` where name=%s """, name)

def get_gl_entries(voucher_no, voucher_type):
    return frappe.db.sql(""" select * from `tabGL Entry` where voucher_no=%s and voucher_type=%s """, (voucher_no, voucher_type), as_dict=1)

def delete_gl_entries(gl_entries):
    for gl in gl_entries:
        gle = frappe.get_doc("GL Entry", gl.name)
        gle.cancel()
        gle.delete()

    
    
