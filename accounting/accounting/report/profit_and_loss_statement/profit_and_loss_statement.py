# Copyright (c) 2013, Frappe and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from accounting.accounting.report.balance_sheet.balance_sheet import get_fiscal_year_data, get_columns, get_data

def execute(filters=None):
    columns, data = [], []
    fiscal_year = get_fiscal_year_data(filters.fiscal_year)
    income = get_data("Income", fiscal_year)
    expense = get_data("Expense", fiscal_year)

    data = []
    data.extend(income or [])
    if income:
        data.extend([{
            "account": "Total Income",
            "opening_balance": income[0].opening_balance
        }])
    data.extend(expense or [])
    if expense:
            data.extend([{
                "account": "Total Expense",
                "opening_balance": expense[0].opening_balance
            }])
    columns = get_columns(filters.fiscal_year)
    return columns, data
