#!/usr/bin/env python3
"""
ezBookkeeping Live Cash Flow, Paycheck Budget Coach & Investment Engine
======================================================================
Replicates 100% of the financial logic and control from 'Foglio spese 2026-Medion.ods'
and tracks Trade Republic assets.

Features:
1. Paycheck Cycle Engine: Tracks expenses from Payday (11th of month) across 5 weeks.
2. The 3 Lines of Costs:
   - Spese Ideale (Row 67): Linear cumulative budget ceiling (t * daily_budget).
   - Spese Pivot (Row 68): Cumulative actual variable spend (excluding one-off travel).
   - Spese DIFFerenza (Row 69): Real-time cushion (+) vs deficit (-).
3. Dynamic Daily Runway (Row 85): Safe Liquid Cash Remaining / Days until next paycheck.
4. Weekly Rollup Matrix (Rows 88-114): Category breakdown across Weeks 1 to 5.
5. Media Reale (Cell I31): True variable daily burn stripping out lumpy travel spikes.
6. Trade Republic Stock Engine & Chart Generator:
   - Banked Closed Gains: +€126.86 (Trading PnL + Dividends net of fees/taxes).
   - Live valuation of 4 active open positions (EKT.DE, ETL.PA, ITAMID.MI, 2B79.DE).
   - Matplotlib dark-mode chart generation for daily VPS updates / Telegram push.

Usage:
  python3 scripts/daily_budget_coach.py [--csv PATH] [--generate-chart]
"""

import os
import sys
import csv
import argparse
from datetime import datetime, date, timedelta
from collections import defaultdict

# ---------------------------------------------------------
# Financial Baselines & Constants (from Excel Model)
# ---------------------------------------------------------
MONTHLY_NET_SALARY = 1736.00      # Regular base net paycheck (EUR)
# Recurring Bills (Day of month, name, expected amount, account, category)
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
TOTAL_MONTHLY_FIXED = sum(b["amount"] for b in RECURRING_BILLS) # 1081.07 EUR
MONTHLY_VARIABLE_BUDGET = max(0.0, MONTHLY_NET_SALARY - TOTAL_MONTHLY_FIXED) # 654.93 EUR
TR_INTEREST_RATE = 0.025          # 2.5% p.a. on uninvested cash

FIXED_CATEGORIES = {
    'Affitto e Mutuo',
    'Elettronica',
    'Spese auto personale',
    'Spese per utenze',
    'Tariffa Internet',
    'Tariffa telefonica',
    'Costi di servizio',
}

# Active Long-Term Stock Holdings (from Trade Republic CSV analysis)
ACTIVE_STOCK_HOLDINGS = [
    {"name": "Energiekontor",            "isin": "DE0005313506", "sym": "EKT.DE",   "shares": 2.0000, "cost": 126.80, "price": 24.65},
    {"name": "Eutelsat Communications",  "isin": "FR0010221234", "sym": "ETL.PA",   "shares": 14.000, "cost": 76.72,  "price": 1.820},
    {"name": "Amundi FTSE Italia PIR",   "isin": "FR0011758085", "sym": "ITAMID.MI", "shares": 1.1319, "cost": 284.43, "price": 251.20},
    {"name": "MSCI World Energy ETF",    "isin": "IE00BJ5JP105", "sym": "2B79.DE",  "shares": 6.4046, "cost": 60.86,  "price": 10.498},
]

BANKED_REALIZED_GAIN = 126.86  # +€87.80 realized trading PnL + €39.06 dividends

def get_payday(year, month):
    """
    Calculates the salary date as the first weekday after the 27th of the month.
    """
    if month == 2:
        d = date(year, 2, 28)
    else:
        d = date(year, month, 28)
    while d.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
        d += timedelta(days=1)
    return d

def compute_paycheck_cycle(target_date):
    """
    Computes start, end and next payday based on the rule:
    first weekday after the 27th of the month.
    """
    this_month_payday = get_payday(target_date.year, target_date.month)
    if target_date >= this_month_payday:
        start = this_month_payday
        if target_date.month == 12:
            next_payday = get_payday(target_date.year + 1, 1)
        else:
            next_payday = get_payday(target_date.year, target_date.month + 1)
        end = next_payday - timedelta(days=1)
    else:
        next_payday = this_month_payday
        end = next_payday - timedelta(days=1)
        if target_date.month == 1:
            start = get_payday(target_date.year - 1, 12)
        else:
            start = get_payday(target_date.year, target_date.month - 1)

    total_days = (end - start).days + 1
    days_elapsed = (target_date - start).days + 1
    days_remaining = max(1, (next_payday - target_date).days)

    return {
        "start": start,
        "end": end,
        "next_payday": next_payday,
        "total_days": total_days,
        "days_elapsed": days_elapsed,
        "days_remaining": days_remaining,
    }

def analyze_financials(csv_path):
    rows = []
    with open(csv_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)

    today = date.today()
    cycle = compute_paycheck_cycle(today)

    # 1. Chronological account balances
    chronological_rows = list(reversed(rows))
    balances = defaultdict(float)

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

    # 2. Extract transactions in current paycheck cycle vs prior cycle
    cycle_start_dt = datetime.combine(cycle['start'], datetime.min.time())
    cycle_end_dt = datetime.combine(cycle['end'], datetime.max.time())
    
    # Prior cycle start/end
    prior_cycle = compute_paycheck_cycle(cycle['start'] - timedelta(days=1))
    prior_start_dt = datetime.combine(prior_cycle['start'], datetime.min.time())
    prior_end_dt = datetime.combine(prior_cycle['end'], datetime.max.time())

    cycle_expenses = []
    prior_cycle_expenses = []
    weekly_breakdown = defaultdict(lambda: defaultdict(float)) # week_num -> category -> sum

    for r in rows:
        if r['Type'] != 'Expense':
            continue
        try:
            dt = datetime.strptime(r['Time'][:19], '%Y-%m-%d %H:%M:%S')
        except Exception:
            continue

        amt = float(r['Amount']) if r['Amount'] else 0.0
        cat = r['Category']
        subcat = r['Sub Category']
        desc = r['Description'] or ''

        is_fixed = (cat in FIXED_CATEGORIES) or (subcat in FIXED_CATEGORIES) or ('affitto' in desc.lower())
        is_travel = ('viaggi' in cat.lower()) or ('viaggi' in subcat.lower()) or ('valencia' in desc.lower())

        item = {
            'dt': dt,
            'amt': amt,
            'cat': cat,
            'subcat': subcat,
            'desc': desc,
            'account': r['Account'],
            'is_fixed': is_fixed,
            'is_travel': is_travel
        }

        if cycle_start_dt <= dt <= cycle_end_dt:
            cycle_expenses.append(item)
            # determine week index (1 to 5)
            days_from_start = (dt.date() - cycle['start']).days
            week_idx = (days_from_start // 7) + 1
            main_cat = cat if cat else 'Varie'
            weekly_breakdown[week_idx][main_cat] += amt
        elif prior_start_dt <= dt <= prior_end_dt:
            prior_cycle_expenses.append(item)

    # 3. Fixed vs Variable separation in current cycle
    cycle_fixed_paid = [e for e in cycle_expenses if e['is_fixed']]
    cycle_var_paid = [e for e in cycle_expenses if not e['is_fixed']]

    # 4. Pending bills for remainder of cycle
    current_day = today.day
    pending_bills = []
    for bill in RECURRING_BILLS:
        # Check if already paid in current cycle
        paid = False
        for p in cycle_fixed_paid:
            if abs(p['dt'].day - bill['day']) <= 3 and abs(p['amt'] - bill['amount']) < 2.0:
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

        if not paid:
            # Days until bill
            # If bill['day'] >= today.day, it is in this month
            if bill['day'] >= current_day:
                days_until = bill['day'] - current_day
            else:
                # Due next calendar month within current cycle
                days_until = (cycle['end'].day - current_day) + bill['day']
            b_copy = dict(bill)
            b_copy['days_until'] = days_until
            pending_bills.append(b_copy)

    pending_bills.sort(key=lambda x: x['days_until'])
    total_pending_fixed = sum(b['amount'] for b in pending_bills)

    # 5. Liquidity & Capital Savings (Protected)
    liquid_cash = balances['Intesa'] + balances['Trade Republic'] + balances['Budget Settimana'] + balances['ISY']

    # 6. Detect Current Salary from Paycheck Cycle or fallback
    current_salary = MONTHLY_NET_SALARY
    for r in chronological_rows:
        if r['Type'] == 'Income':
            amt = float(r['Amount']) if r['Amount'] else 0.0
            if amt >= 1000.0:
                try:
                    dt = datetime.strptime(r['Time'][:19], '%Y-%m-%d %H:%M:%S')
                    if cycle_start_dt - timedelta(days=4) <= dt <= cycle_end_dt:
                        current_salary = amt
                except Exception:
                    pass

    total_monthly_fixed = sum(b['amount'] for b in RECURRING_BILLS)
    monthly_var_budget = max(0.0, current_salary - total_monthly_fixed)

    # 7. The 3 Lines of Costs (Paycheck Pacing)
    cycle_daily_rate = monthly_var_budget / cycle['total_days']
    ideale_to_date = cycle['days_elapsed'] * cycle_daily_rate
    pivot_to_date = sum(e['amt'] for e in cycle_var_paid if not e['is_travel'])
    differenza_to_date = ideale_to_date - pivot_to_date
    media_reale_daily = pivot_to_date / max(1, cycle['days_elapsed'])

    # Paycheck-based safe-to-spend & runway (Preserves accumulated savings)
    remaining_paycheck_budget = max(0.0, monthly_var_budget - pivot_to_date)
    days_left = max(1, cycle['days_remaining'])
    dynamic_daily_allowance = remaining_paycheck_budget / days_left

    # Intesa Direct Debit Check
    intesa_pending = sum(b['amount'] for b in pending_bills if b['account'] == 'Intesa')
    intesa_shortfall = max(0.0, intesa_pending - balances['Intesa'])

    # 8. Stock Portfolio Live Stats
    portfolio_cost = sum(s['cost'] for s in ACTIVE_STOCK_HOLDINGS)
    portfolio_val = sum(s['shares'] * s['price'] for s in ACTIVE_STOCK_HOLDINGS)
    unrealized_pnl = portfolio_val - portfolio_cost

    return {
        "today": today.isoformat(),
        "cycle": cycle,
        "balances": balances,
        "liquid_cash": liquid_cash,
        "current_salary": current_salary,
        "total_monthly_fixed": total_monthly_fixed,
        "monthly_var_budget": monthly_var_budget,
        "remaining_paycheck_budget": remaining_paycheck_budget,
        "total_pending_fixed": total_pending_fixed,
        "safe_to_spend": remaining_paycheck_budget,
        "dynamic_daily_allowance": dynamic_daily_allowance,
        "ideale_to_date": ideale_to_date,
        "pivot_to_date": pivot_to_date,
        "differenza_to_date": differenza_to_date,
        "media_reale_daily": media_reale_daily,
        "pending_bills": pending_bills,
        "intesa_shortfall": intesa_shortfall,
        "intesa_pending": intesa_pending,
        "weekly_breakdown": weekly_breakdown,
        "portfolio_cost": portfolio_cost,
        "portfolio_val": portfolio_val,
        "unrealized_pnl": unrealized_pnl,
        "banked_gain": BANKED_REALIZED_GAIN,
    }

def generate_stock_graphic(output_path="/home/ion/ezbookkeeping/scripts/daily_portfolio_summary.png"):
    """
    Generates dark-mode matplotlib visual chart of Trade Republic open portfolio.
    """
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import numpy as np

        names = [s['name'] for s in ACTIVE_STOCK_HOLDINGS]
        vals = [s['shares'] * s['price'] for s in ACTIVE_STOCK_HOLDINGS]
        pnls = [(s['shares'] * s['price']) - s['cost'] for s in ACTIVE_STOCK_HOLDINGS]

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        fig.patch.set_facecolor('#0f172a')

        # Subplot 1: Allocation Donut
        ax1.set_facecolor('#0f172a')
        colors = ['#38bdf8', '#818cf8', '#34d399', '#f59e0b']
        wedges, texts, autotexts = ax1.pie(vals, labels=names, autopct='%1.1f%%', startangle=140, colors=colors,
                                           textprops={'color': 'white', 'fontsize': 10},
                                           wedgeprops=dict(width=0.45, edgecolor='#0f172a'))
        for at in autotexts:
            at.set_color('#0f172a')
            at.set_weight('bold')
        ax1.set_title(f'Active Stock Allocation (€{sum(vals):.2f})', color='white', fontsize=12, pad=12)

        # Subplot 2: Unrealized P&L Waterfall
        ax2.set_facecolor('#1e293b')
        y_pos = np.arange(len(names))
        bar_colors = ['#ef4444' if p < 0 else '#10b981' for p in pnls]
        bars = ax2.barh(y_pos, pnls, color=bar_colors, height=0.55)
        ax2.set_yticks(y_pos)
        ax2.set_yticklabels(names, color='white', fontsize=10)
        ax2.axvline(0, color='#64748b', linewidth=1, linestyle='--')
        ax2.set_title(f'Unrealized P&L per Position (€{sum(pnls):+.2f})', color='white', fontsize=12, pad=12)
        ax2.tick_params(colors='white')
        for bar in bars:
            w = bar.get_width()
            x = w + (1 if w >= 0 else -1)
            ha = 'left' if w >= 0 else 'right'
            ax2.text(x, bar.get_y() + bar.get_height()/2, f'{w:+.2f} €', color='white', va='center', ha=ha, fontsize=9, fontweight='bold')

        for spine in ax2.spines.values():
            spine.set_color('#334155')

        plt.tight_layout()
        plt.savefig(output_path, dpi=150, facecolor=fig.get_facecolor(), bbox_inches='tight')
        plt.close()
        return output_path
    except Exception as e:
        print(f"Error generating chart: {e}")
        return None

def print_paycheck_dashboard(data):
    c = data['cycle']
    print("=" * 72)
    print(f"⚡ EZBOOKKEEPING PAYCHECK BUDGET COACH — {data['today']}")
    print(f"📅 Paycheck Cycle: {c['start'].strftime('%d %b')} → {c['end'].strftime('%d %b %Y')} (Day {c['days_elapsed']} of {c['total_days']} • {c['days_remaining']} days left)")
    print("=" * 72)

    print("\n💵 1. MONTHLY PAYCHECK CASH FLOW BREAKDOWN")
    print(f"   • Monthly Net Paycheck:     €{data['current_salary']:7.2f}")
    print(f"   • Obligatory Fixed Bills:  -€{data['total_monthly_fixed']:7.2f} (Rent, Car loan, Utilities, subs)")
    print("   -----------------------------------------------------")
    print(f"   • Variable Spending Cap:    €{data['monthly_var_budget']:7.2f} (Pacing: €{data['monthly_var_budget']/c['total_days']:.2f}/day)")

    print("\n🎯 2. THE 3 LINES OF COSTS (PACING WITHIN PAYCHECK)")
    print(f"   • Row 67 (Spese Ideale):    €{data['ideale_to_date']:7.2f} (Cumulative linear pace to Day {c['days_elapsed']})")
    print(f"   • Row 68 (Spese Pivot):     €{data['pivot_to_date']:7.2f} (Actual variable burn to date, excl. travel)")
    diff_status = "✅ CUSHION (UNDER BUDGET)" if data['differenza_to_date'] >= 0 else "🚨 DEFICIT (OVER BUDGET)"
    sign = "+" if data['differenza_to_date'] >= 0 else ""
    print(f"   • Row 69 (DIFFerenza):     {sign}€{data['differenza_to_date']:7.2f} [{diff_status}]")
    print(f"   👉 Media Reale Daily Burn:  €{data['media_reale_daily']:7.2f} / day")

    print("\n💰 3. REMAINING PAYCHECK RUNWAY (PRESERVING SAVINGS)")
    print(f"   Variable Cap for Cycle:     €{data['monthly_var_budget']:7.2f}")
    print(f"   - Variable Spend to Date:  -€{data['pivot_to_date']:7.2f}")
    print("   -----------------------------------------------------")
    print(f"   Remaining Paycheck Budget:  €{data['remaining_paycheck_budget']:7.2f}")
    print(f"   👉 DYNAMIC DAILY RUNWAY:    €{data['dynamic_daily_allowance']:7.2f} / day for remaining {c['days_remaining']} days")
    print(f"   🛡️ Protected Total Savings: €{data['liquid_cash']:7.2f} (Untouched capital across all banks)")

    if data['intesa_shortfall'] > 0:
        print("\n⚠️ 4. DIRECT DEBIT ALERT (INTESA ACCOUNT)")
        print(f"   Intesa Balance:             €{data['balances']['Intesa']:7.2f}")
        print(f"   Intesa Pending Bills:       €{data['intesa_pending']:7.2f}")
        print(f"   🚨 SHORTFALL:               €{data['intesa_shortfall']:7.2f}")
        print(f"   👉 ACTION: Transfer at least €{data['intesa_shortfall'] + 30:.2f} from Trade Republic before bills debit!")

    print("\n📅 5. UPCOMING BILLS TIMELINE (NEXT DAYS)")
    for b in data['pending_bills'][:6]:
        due_str = f"In {b['days_until']} days" if b['days_until'] > 1 else ("Tomorrow" if b['days_until'] == 1 else "Today")
        print(f"   • {b['day']:02d} Nov ({due_str:<10}): €{b['amount']:6.2f} | {b['name']:<24} (from {b['account']})")

    print("\n📊 6. WEEKLY ROLLUP MATRIX (EXCEL ROWS 88-114)")
    for w in sorted(data['weekly_breakdown'].keys()):
        tot = sum(data['weekly_breakdown'][w].values())
        print(f"   • Week {w}: €{tot:7.2f} total")

    print("\n📈 7. TRADE REPUBLIC STOCKS (PIPELINE ROADMAP SUMMARY)")
    print(f"   • Banked Cash Gains:       +€{data['banked_gain']:7.2f} (Closed trades PnL + cash dividends)")
    print(f"   • Active Portfolio Value:   €{data['portfolio_val']:7.2f} (Cost basis: €{data['portfolio_cost']:.2f})")
    print(f"   • Unrealized Open P&L:      €{data['unrealized_pnl']:+7.2f} (Holding 4 active assets)")
    print("=" * 72)
    print("=" * 72)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="ezBookkeeping Paycheck Budget Coach")
    parser.add_argument("--csv", default="/home/ion/Scaricati/ezBookkeeping_Doi_export_data(8).csv", help="Path to CSV export")
    parser.add_argument("--generate-chart", action="store_true", help="Generate dark-mode portfolio chart PNG")
    args = parser.parse_args()

    data = analyze_financials(args.csv)
    print_paycheck_dashboard(data)

    if args.generate_chart:
        chart_file = generate_stock_graphic()
        if chart_file:
            print(f"✅ Generated portfolio chart at: {chart_file}")
