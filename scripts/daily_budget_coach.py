#!/usr/bin/env python3
"""
ezBookkeeping Live Cash Flow, Upcoming Bills & Investment Monitor
================================================================
Gives instant visibility on:
1. Upcoming fixed expenses for the rest of the month (day-by-day timeline).
2. True "Safe-to-Spend" liquid cash (Liquid balances minus pending bills).
3. Account-specific liquidity checks (e.g. Intesa shortfall warning before car/utility debits).
4. Trade Republic 2.5% daily accrued interest counter & monthly projection.
5. Conto Investimenti cost basis vs real portfolio tracking.

Usage:
  python3 scripts/daily_budget_coach.py
"""

import os
import sys
import csv
import argparse
from datetime import datetime, date
from collections import defaultdict

# Target Baselines (from roadmap)
MONTHLY_VARIABLE_BUDGET = 724.88  # All-in variable cap (EUR)
WEEKLY_VARIABLE_BUDGET = 167.41   # Weekly variable cap (EUR)
TR_INTEREST_RATE = 0.025          # 2.5% p.a. on uninvested cash

# Standard Recurring Bills (Day of month, name, expected amount, account, category)
RECURRING_BILLS = [
    {"day": 1,  "name": "Canone Conto Intesa",   "amount": 7.00,   "account": "Intesa",           "category": "Finanza -> Costi di servizio"},
    {"day": 2,  "name": "Affitto (Rent)",         "amount": 500.00, "account": "Budget Settimana", "category": "Alloggio -> Affitto e Mutuo"},
    {"day": 5,  "name": "Finanziamento PC",       "amount": 36.73,  "account": "Intesa",           "category": "Alloggio -> Elettronica"},
    {"day": 5,  "name": "IONOS Spazio Web",       "amount": 10.98,  "account": "Budget Settimana", "category": "Comunicazione -> Internet"},
    {"day": 8,  "name": "Fibra Casa (Internet)",  "amount": 29.79,  "account": "Intesa",           "category": "Comunicazione -> Internet"},
    {"day": 8,  "name": "Amazon Prime Ad-Free",   "amount": 1.99,   "account": "Budget Settimana", "category": "Intrattenimento -> Sub"},
    {"day": 15, "name": "Tariffa Mobile (TIM)",   "amount": 7.99,   "account": "Intesa",           "category": "Comunicazione -> Telefono"},
    {"day": 16, "name": "Amazon Prime",           "amount": 4.99,   "account": "Budget Settimana", "category": "Intrattenimento -> Sub"},
    {"day": 16, "name": "PAC Trade Investiti",    "amount": 50.00,  "account": "Trade Republic",   "category": "Trasferimento -> PAC"},
    {"day": 20, "name": "Rata Auto",              "amount": 304.50, "account": "Intesa",           "category": "Trasporti -> Spese auto"},
    {"day": 21, "name": "Utenze (Luce & Gas)",    "amount": 117.34, "account": "Intesa",           "category": "Utenze -> Luce e Gas"},
    {"day": 30, "name": "IONOS VPS",              "amount": 9.76,   "account": "Budget Settimana", "category": "Comunicazione -> VPS"},
]

FIXED_CATEGORIES = {
    'Affitto e Mutuo',
    'Elettronica',
    'Spese auto personale',
    'Spese per utenze',
    'Tariffa Internet',
    'Tariffa telefonica',
    'Costi di servizio',
}

def analyze_full_cashflow(csv_path):
    rows = []
    with open(csv_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)

    today = date.today()
    current_year = today.year
    current_month = today.month
    day_of_month = today.day

    # Days in month
    if current_month in [1, 3, 5, 7, 8, 10, 12]:
        days_in_month = 31
    elif current_month in [4, 6, 9, 11]:
        days_in_month = 30
    else:
        days_in_month = 29 if (current_year % 4 == 0 and current_year % 100 != 0) or (current_year % 400 == 0) else 28

    days_left_in_month = days_in_month - day_of_month + 1

    # 1. Compute Chronological Account Balances
    chronological_rows = list(reversed(rows))
    balances = defaultdict(float)
    pac_total_invested = 0.0

    for r in chronological_rows:
        amt = float(r['Amount']) if r['Amount'] else 0.0
        acc = r['Account']
        t_type = r['Type']

        if t_type == 'Balance Modification':
            balances[acc] = amt
        elif t_type == 'Income':
            balances[acc] += amt
        elif t_type == 'Expense':
            balances[acc] -= amt
        elif t_type == 'Transfer':
            balances[acc] -= amt
            acc2 = r['Account2']
            amt2 = float(r['Account2 Amount']) if r['Account2 Amount'] else amt
            balances[acc2] += amt2
            if acc2 == 'Trade Investiti':
                pac_total_invested += amt2

    # 2. Check Paid Bills vs Pending Bills for Current Month
    month_paid_fixed = []
    month_paid_variable = []
    subcat_spend = defaultdict(float)

    for r in rows:
        if r['Type'] != 'Expense':
            continue
        try:
            dt = datetime.strptime(r['Time'][:19], '%Y-%m-%d %H:%M:%S')
        except Exception:
            continue

        if dt.year != current_year or dt.month != current_month:
            continue

        amt = float(r['Amount']) if r['Amount'] else 0.0
        cat = r['Category']
        subcat = r['Sub Category']
        desc = r['Description'] or ''

        is_fixed = (cat in FIXED_CATEGORIES) or (subcat in FIXED_CATEGORIES) or ('affitto' in desc.lower())

        item = {
            'time': dt,
            'amt': amt,
            'cat': cat,
            'subcat': subcat,
            'desc': desc,
            'account': r['Account']
        }

        if is_fixed:
            month_paid_fixed.append(item)
        else:
            month_paid_variable.append(item)
            full_cat = f"{cat} -> {subcat}" if subcat else cat
            subcat_spend[full_cat] += amt

    # Determine which recurring bills are already paid vs pending
    pending_bills = []
    already_paid_bills = []

    for bill in RECURRING_BILLS:
        paid = False
        for p in month_paid_fixed:
            if abs(p['time'].day - bill['day']) <= 3 and abs(p['amt'] - bill['amount']) < 2.0:
                paid = True
                break
            if bill['name'] == 'Canone Conto Intesa' and 'Costi di servizio' in p['cat']:
                paid = True
                break
            if bill['name'] == 'Affitto (Rent)' and ('Affitto' in p['subcat'] or 'affitto' in p['desc'].lower()):
                paid = True
                break
            if bill['name'] == 'Finanziamento PC' and abs(p['amt'] - 36.73) < 0.01:
                paid = True
                break
            if bill['name'] == 'IONOS Spazio Web' and abs(p['amt'] - 10.98) < 0.01:
                paid = True
                break

        if paid:
            already_paid_bills.append(bill)
        else:
            days_until = bill['day'] - day_of_month
            bill_copy = dict(bill)
            bill_copy['days_until'] = days_until
            pending_bills.append(bill_copy)

    pending_bills.sort(key=lambda x: x['day'])
    total_pending_fixed = sum(b['amount'] for b in pending_bills)

    # 3. Calculate Liquidity & Safe-to-Spend
    liquid_bank_cash = balances['Intesa'] + balances['Trade Republic'] + balances['Budget Settimana'] + balances['ISY']
    safe_to_spend_cash = liquid_bank_cash - total_pending_fixed

    # Intesa direct debit check
    intesa_pending_bills = [b for b in pending_bills if b['account'] == 'Intesa']
    intesa_pending_total = sum(b['amount'] for b in intesa_pending_bills)
    intesa_current_bal = balances['Intesa']
    intesa_shortfall = max(0.0, intesa_pending_total - intesa_current_bal)

    # Trade Republic 2.5% daily interest calculation
    tr_cash = balances['Trade Republic']
    tr_daily_interest = (tr_cash * TR_INTEREST_RATE) / 365.0
    tr_monthly_interest = (tr_cash * TR_INTEREST_RATE) / 12.0

    # Variable Pace
    var_spent_mtd = sum(v['amt'] for v in month_paid_variable)
    ideal_var_mtd = (MONTHLY_VARIABLE_BUDGET / days_in_month) * day_of_month
    var_variance = var_spent_mtd - ideal_var_mtd
    remaining_var_budget = max(0.0, MONTHLY_VARIABLE_BUDGET - var_spent_mtd)
    daily_var_allowance = remaining_var_budget / days_left_in_month if days_left_in_month > 0 else 0.0

    return {
        'today': today.isoformat(),
        'day_of_month': day_of_month,
        'days_in_month': days_in_month,
        'days_left_in_month': days_left_in_month,
        'balances': balances,
        'liquid_bank_cash': liquid_bank_cash,
        'safe_to_spend_cash': safe_to_spend_cash,
        'total_pending_fixed': total_pending_fixed,
        'pending_bills': pending_bills,
        'intesa_current_bal': intesa_current_bal,
        'intesa_pending_total': intesa_pending_total,
        'intesa_shortfall': intesa_shortfall,
        'intesa_pending_bills': intesa_pending_bills,
        'tr_cash': tr_cash,
        'tr_daily_interest': tr_daily_interest,
        'tr_monthly_interest': tr_monthly_interest,
        'pac_total_invested': pac_total_invested,
        'trade_investiti_balance': balances['Trade Investiti'],
        'var_spent_mtd': var_spent_mtd,
        'ideal_var_mtd': ideal_var_mtd,
        'var_variance': var_variance,
        'remaining_var_budget': remaining_var_budget,
        'daily_var_allowance': daily_var_allowance,
        'top_subcategories': sorted(subcat_spend.items(), key=lambda x: x[1], reverse=True)[:5],
    }

def print_dashboard(data):
    print("=" * 70)
    print(f"⚡ LIVE MONEY FLOW & CASH REALITY DASHBOARD — {data['today']}")
    print("=" * 70)
    print(f"📅 Day {data['day_of_month']} of {data['days_in_month']} ({data['days_left_in_month']} days left in month)")
    print()

    print("💰 1. REAL LIQUIDITY & SAFE-TO-SPEND (NO MENTAL MATH)")
    print(f"   Liquid Bank Balance:        €{data['liquid_bank_cash']:8.2f} (TR + Intesa + Budget Sett. + ISY)")
    print(f"   - Pending Fixed Bills:      €{data['total_pending_fixed']:8.2f} (Due between today and Nov {data['days_in_month']})")
    print("   -----------------------------------------------------")
    print(f"   👉 TRUE SAFE-TO-SPEND CASH: €{data['safe_to_spend_cash']:8.2f}")
    print()

    print("⚠️ 2. DIRECT DEBIT ALERT (INTESA ACCOUNT)")
    print(f"   Intesa Current Balance:     €{data['intesa_current_bal']:8.2f}")
    print(f"   Intesa Upcoming Debits:     €{data['intesa_pending_total']:8.2f} (Car, Utilities, Fiber, Mobile)")
    if data['intesa_shortfall'] > 0:
        print(f"   🚨 SHORTFALL DETECTED:      €{data['intesa_shortfall']:8.2f}")
        print(f"   👉 ACTION: Transfer at least €{data['intesa_shortfall'] + 30:.2f} from Trade Republic to Intesa before Nov 20!")
    else:
        print("   ✅ Intesa has sufficient funds for upcoming bills.")
    print()

    print("📅 3. UPCOMING BILLS TIMELINE (NEXT DAYS)")
    for b in data['pending_bills']:
        due_str = f"In {b['days_until']} days" if b['days_until'] > 1 else ("Tomorrow" if b['days_until'] == 1 else "Today")
        print(f"   • {b['day']:02d} Nov ({due_str:<10}): €{b['amount']:6.2f} | {b['name']:<24} (from {b['account']})")
    print()

    print("📈 4. TRADE REPUBLIC 2.5% INTEREST & INVESTMENTS")
    print(f"   Trade Republic Cash:        €{data['tr_cash']:8.2f}")
    print(f"   👉 Daily Accrued Interest:  +€{data['tr_daily_interest']:.3f} / day (at 2.5% p.a.)")
    print(f"   👉 Projected Monthly Yield: +€{data['tr_monthly_interest']:.2f} / month")
    print(f"   Conto Investiti Ledger:     €{data['trade_investiti_balance']:8.2f} (Cash deposited via PAC)")
    print("   ℹ️  Note: ezBookkeeping only tracks deposits, not ETF market value or P&L.")
    print()

    print("🎯 5. VARIABLE BUDGET PACING")
    status = "🚨 OVER PACE" if data['var_variance'] > 0 else "✅ ON TRACK"
    print(f"   Spent MTD:                  €{data['var_spent_mtd']:6.2f} / €{MONTHLY_VARIABLE_BUDGET:.2f} (Ideal: €{data['ideal_var_mtd']:.2f} | {status}: €{abs(data['var_variance']):.2f})")
    print(f"   Remaining Variable Budget:  €{data['remaining_var_budget']:6.2f}")
    print(f"   👉 Daily Variable Allowance: €{data['daily_var_allowance']:.2f} / day for the remaining {data['days_left_in_month']} days")
    print("=" * 70)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Live Money Flow & Investment Monitor")
    parser.add_argument("--csv", default="/home/ion/Scaricati/ezBookkeeping_Doi_export_data(8).csv", help="Path to CSV export")
    args = parser.parse_args()

    data = analyze_full_cashflow(args.csv)
    print_dashboard(data)
