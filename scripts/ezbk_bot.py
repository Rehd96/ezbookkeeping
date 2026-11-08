#!/usr/bin/env python3
"""
ezBookkeeping Telegram Budget Coach Bot
=======================================
Long-polling Telegram Bot connected to MySQL and replicating 100% of the
Foglio Spese Medion 2026 financial model:
- Daily Pacing: Ideale (Row 67), Pivot (Row 68), DIFFerenza (Row 69)
- Dynamic Daily Runway (Row 85)
- Direct Debit Shortfall Alerts (Intesa Account)
- Live Balances & Upcoming Bills Timeline
- Quick Expense insertion directly from chat into Budget Settimana
"""

import sys
import os
import time
import re
import csv
import json
import logging
import subprocess
import urllib.request
import urllib.parse
from datetime import datetime, date, timedelta
from threading import Thread

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger("ezbk_bot")

BOT_TOKEN = "8557003430:AAECSYrGry95gF4Lpo65y2bb9GbSWyDSq0g"
ALLOWED_CHAT_ID = "356683559"
USER_UID = "3810852904097546240"
DEFAULT_ACCOUNT_ID = "3811181793499938816" # Budget Settimana

# Excel Financial Model Constants
MONTHLY_VARIABLE_BUDGET = 724.88
STATIC_DAILY_BUDGET = 23.38
PAYCHECK_START_DAY = 11

RECURRING_BILLS = [
    {"day": 1,  "name": "Canone Conto Intesa",   "amount": 7.00,   "account": "Intesa"},
    {"day": 2,  "name": "Affitto (Rent)",         "amount": 500.00, "account": "Budget Settimana"},
    {"day": 5,  "name": "Finanziamento PC",       "amount": 36.73,  "account": "Intesa"},
    {"day": 5,  "name": "IONOS Spazio Web",       "amount": 10.98,  "account": "Budget Settimana"},
    {"day": 8,  "name": "Fibra Casa (Internet)",  "amount": 29.79,  "account": "Intesa"},
    {"day": 8,  "name": "Amazon Prime Ad-Free",   "amount": 1.99,   "account": "Budget Settimana"},
    {"day": 15, "name": "Tariffa Mobile (TIM)",   "amount": 7.99,   "account": "Intesa"},
    {"day": 16, "name": "Amazon Prime",           "amount": 4.99,   "account": "Budget Settimana"},
    {"day": 16, "name": "PAC Trade Investiti",    "amount": 50.00,  "account": "Trade Republic"},
    {"day": 20, "name": "Rata Auto",              "amount": 304.50, "account": "Intesa"},
    {"day": 21, "name": "Utenze (Luce & Gas)",    "amount": 117.34, "account": "Intesa"},
    {"day": 30, "name": "IONOS VPS",              "amount": 9.76,   "account": "Budget Settimana"},
]

FIXED_AND_TRAVEL_CATEGORIES = {
    'Affitto e Mutuo',
    'Elettronica',
    'Spese auto personale',
    'Spese per utenze',
    'Tariffa Internet',
    'Tariffa telefonica',
    'Costi di servizio',
    'Bollette e Tasse',
    'Viaggi',
    'Biglietti aerei'
}

CATEGORY_MAP = {
    "conad": ("3812838656859701248", "Conad"),
    "esselunga": ("3826245197558185984", "Esselunga"),
    "interspar": ("3810957991612514304", "Interspar"),
    "spar": ("3810957991612514304", "Interspar"),
    "ipercoop": ("3812838633237381120", "Ipercoop"),
    "coop": ("3812838633237381120", "Ipercoop"),
    "md": ("3812838613910028288", "MD"),
    "lidl": ("3826245178230833152", "Lild"),
    "carrefour": ("3814319572320780288", "Carrefour"),
    "spesa": ("3810957948662841344", "Spesa"),
    "colazione": ("3810957660900032512", "colazione"),
    "bar": ("3810957428971798528", "Bar"),
    "caffè": ("3810957660900032512", "colazione"),
    "caffe": ("3810957660900032512", "colazione"),
    "aperitivo": ("3810957701702221824", "aperitivo"),
    "pranzo": ("3810958169853657088", "Pranzo Ufficio"),
    "ufficio": ("3810958169853657088", "Pranzo Ufficio"),
    "benzina": ("3839734998345187328", "Benzina"),
    "gasolio": ("3839734998345187328", "Benzina"),
    "carburante": ("3839734998345187328", "Benzina"),
    "farmaci": ("3810852906647683134", "Farmaci"),
    "farmacia": ("3810852906647683134", "Farmaci"),
    "veterinario": ("3842485613513146368", "veterinario"),
    "cane": ("3842485613513146368", "veterinario"),
    "gatto": ("3842485613513146368", "veterinario"),
    "dentista": ("3814342531068461056", "dentista"),
    "ikea": ("3814319260935651328", "Ikea"),
    "casa": ("3839758560535773184", "Articoli per la casa"),
    "piante": ("3818073111744479232", "Piante"),
    "cibo": ("3810852906647683100", "Cibo"),
    "cena": ("3810852906647683100", "Cibo"),
    "pizza": ("3810852906647683100", "Cibo"),
    "ristorante": ("3810852906647683100", "Cibo")
}
DEFAULT_CATEGORY = ("3810852906647683141", "Altre spese")

def run_query(sql):
    res = subprocess.check_output(["mysql", "ezbookkeeping", "-B", "-e", sql]).decode("utf-8")
    lines = res.splitlines()
    if not lines:
        return []
    reader = csv.DictReader(lines, delimiter="\t")
    return list(reader)

def exec_sql(sql):
    subprocess.check_call(["mysql", "ezbookkeeping", "-e", sql])

def send_telegram(text, reply_markup=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": ALLOWED_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    data = urllib.parse.urlencode(payload).encode("utf-8")
    try:
        req = urllib.request.Request(url, data=data)
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        log.error("Failed to send telegram msg: %s", e)

def get_payday(year, month):
    """
    Calculates the salary date as the first weekday after the 27th of the month.
    """
    if month == 2:
        d = date(year, 2, 28)
    else:
        d = date(year, month, 28)
    while d.weekday() >= 5: # 5 = Saturday, 6 = Sunday
        d += timedelta(days=1)
    return d

def compute_cycle(today):
    """
    Computes start, end and next payday based on the rule:
    first weekday after the 27th of the month.
    """
    this_month_payday = get_payday(today.year, today.month)
    if today >= this_month_payday:
        start = this_month_payday
        if today.month == 12:
            next_payday = get_payday(today.year + 1, 1)
        else:
            next_payday = get_payday(today.year, today.month + 1)
        end = next_payday - timedelta(days=1)
    else:
        next_payday = this_month_payday
        end = next_payday - timedelta(days=1)
        if today.month == 1:
            start = get_payday(today.year - 1, 12)
        else:
            start = get_payday(today.year, today.month - 1)
    
    total_days = (end - start).days + 1
    days_elapsed = (today - start).days + 1
    days_remaining = max(1, (next_payday - today).days)
    return {
        "start": start,
        "end": end,
        "next_payday": next_payday,
        "total_days": total_days,
        "days_elapsed": days_elapsed,
        "days_remaining": days_remaining
    }

def get_financial_status():
    today = date.today()
    cycle = compute_cycle(today)
    start_ts_ms = int(datetime.combine(cycle["start"], datetime.min.time()).timestamp() * 1000)

    # 1. Accounts
    accs = run_query(f"SELECT name, balance FROM account WHERE uid = {USER_UID};")
    balances = {r["name"]: float(r["balance"]) / 100.0 for r in accs}

    liquid_keys = ["Intesa", "ISY", "Trade Republic", "Budget Settimana"]
    liquid_cash = sum(balances.get(k, 0.0) for k in liquid_keys)

    # 2. Fetch real salary of this cycle
    sal_query = f"""
        SELECT amount/100 as amt 
        FROM transaction 
        WHERE uid = {USER_UID} 
          AND type = 2 
          AND amount >= 100000 
          AND transaction_time >= {start_ts_ms - (4 * 24 * 60 * 60 * 1000)}
        ORDER BY transaction_time DESC 
        LIMIT 1;
    """
    sal_res = run_query(sal_query)
    current_salary = float(sal_res[0]["amt"]) if sal_res else 1736.00

    # Total recurring fixed expenses for a month
    total_monthly_fixed = sum(b["amount"] for b in RECURRING_BILLS)

    # Discretionary variable budget from salary
    monthly_var_budget = max(0.0, current_salary - total_monthly_fixed)

    # Daily ideal rate based strictly on paycheck
    daily_budget = monthly_var_budget / cycle["total_days"]
    ideale_to_date = cycle["days_elapsed"] * daily_budget
    weekly_budget = monthly_var_budget / (cycle["total_days"] / 7.0)

    # 3. Variable spend in cycle
    txs = run_query(f"""
        SELECT c.name as category, t.amount 
        FROM transaction t 
        LEFT JOIN transaction_category c ON t.category_id = c.category_id 
        WHERE t.uid = {USER_UID} 
          AND t.type = 3 
          AND t.deleted = 0 
          AND t.transaction_time >= {start_ts_ms};
    """)
    variable_spend = 0.0
    category_totals = {}
    for r in txs:
        cat = r["category"] or "Altro"
        amt = float(r["amount"]) / 100.0
        category_totals[cat] = category_totals.get(cat, 0.0) + amt
        if cat not in FIXED_AND_TRAVEL_CATEGORIES:
            variable_spend += amt

    # 4. Pending bills before next paycheck
    pending_bills = []
    total_pending_bills = 0.0
    intesa_pending = 0.0
    next_payday = cycle["next_payday"]

    for b in RECURRING_BILLS:
        b_day = b["day"]
        try:
            d1 = date(today.year, today.month, b_day)
            if today <= d1 < next_payday:
                days_until = (d1 - today).days
                pending_bills.append({**b, "due_date": d1, "days_until": days_until})
                total_pending_bills += b["amount"]
                if b["account"] == "Intesa":
                    intesa_pending += b["amount"]
                continue
        except ValueError:
            pass

        try:
            m2 = 1 if today.month == 12 else today.month + 1
            y2 = today.year + 1 if today.month == 12 else today.year
            d2 = date(y2, m2, b_day)
            if today <= d2 < next_payday:
                days_until = (d2 - today).days
                pending_bills.append({**b, "due_date": d2, "days_until": days_until})
                total_pending_bills += b["amount"]
                if b["account"] == "Intesa":
                    intesa_pending += b["amount"]
        except ValueError:
            pass

    pending_bills.sort(key=lambda x: x["days_until"])

    # 5. Math Pacing & Runway from Paycheck
    differenza = ideale_to_date - variable_spend
    media_reale = variable_spend / max(1, cycle["days_elapsed"])
    remaining_paycheck_budget = monthly_var_budget - variable_spend
    if cycle["days_remaining"] > 0 and remaining_paycheck_budget > 0:
        dynamic_runway = remaining_paycheck_budget / cycle["days_remaining"]
    else:
        dynamic_runway = 0.0

    intesa_shortfall = max(0.0, intesa_pending - balances.get("Intesa", 0.0))

    return {
        "today": today,
        "cycle": cycle,
        "current_salary": current_salary,
        "total_monthly_fixed": total_monthly_fixed,
        "monthly_var_budget": monthly_var_budget,
        "daily_budget": daily_budget,
        "weekly_budget": weekly_budget,
        "balances": balances,
        "liquid_cash": liquid_cash,
        "variable_spend": variable_spend,
        "ideale_to_date": ideale_to_date,
        "differenza": differenza,
        "remaining_paycheck_budget": remaining_paycheck_budget,
        "total_pending_bills": total_pending_bills,
        "pending_bills": pending_bills,
        "dynamic_runway": dynamic_runway,
        "media_reale": media_reale,
        "intesa_pending": intesa_pending,
        "intesa_shortfall": intesa_shortfall,
        "category_totals": category_totals
    }

def format_oggi_report(s):
    c = s["cycle"]
    diff_sign = "+" if s["differenza"] >= 0 else ""
    diff_status = "✅ SOTTO BUDGET (Stai risparmiando)" if s["differenza"] >= 0 else "🚨 SOPRA BUDGET (Ritmo elevato)"

    msg = [
        f"⚡ <b>BUDGET COACH EZBOOKKEEPING — {s['today'].strftime('%d %b %Y')}</b>",
        f"📅 Ciclo: <b>{c['start'].strftime('%d %b')} → {c['end'].strftime('%d %b')}</b> (Giorno {c['days_elapsed']} di {c['total_days']} · Payday: <b>{c['next_payday'].strftime('%d %b')}</b>, tra {c['days_remaining']} gg)",
        "──────────────────────────────",
        "💵 <b>ANALISI CASH FLOW STIPENDIO</b>",
        f"• Stipendio Netto Ricevuto: <b>€{s['current_salary']:.2f}</b>",
        f"• Spese Fisse Obbligatorie: <b>-€{s['total_monthly_fixed']:.2f}</b> (Affitto, Auto, Utenze, ecc.)",
        f"👉 <b>Budget Variabile Mese: €{s['monthly_var_budget']:.2f}</b> (€{s['daily_budget']:.2f}/gg · €{s['weekly_budget']:.2f}/sett)",
        "",
        "🎯 <b>PACING SPESE VARIABILI (A OGGI)</b>",
        f"• <b>Ideale (Row 67):</b> €{s['ideale_to_date']:.2f} (spesa teorica al giorno {c['days_elapsed']})",
        f"• <b>Pivot (Row 68):</b> €{s['variable_spend']:.2f} (spesa effettiva a oggi · media €{s['media_reale']:.2f}/gg)",
        f"• <b>DIFFerenza (Row 69): {diff_sign}€{s['differenza']:.2f}</b> [{diff_status}]",
        "",
        "🛡️ <b>DISPONIBILITÀ RESIDUA DELLO STIPENDIO</b>",
    ]

    if s["remaining_paycheck_budget"] > 0:
        msg.extend([
            f"• Budget Stipendio Rimanente: <b>€{s['remaining_paycheck_budget']:.2f}</b>",
            f"👉 <b>RUNWAY: €{s['dynamic_runway']:.2f} / giorno</b> per i restanti {c['days_remaining']} gg",
            f"<i>(Rispettando €{s['dynamic_runway']:.2f}/gg arrivi al {c['next_payday'].strftime('%d %b')} senza toccare 1€ di risparmi!)</i>"
        ])
    else:
        over = abs(s["remaining_paycheck_budget"])
        msg.extend([
            f"🚨 <b>BUDGET STIPENDIO ESAURITO: -€{over:.2f} fuori soglia!</b>",
            "👉 <b>RUNWAY CONSIGLIATO: €0.00 / giorno</b>",
            f"⚠️ <i>Attenzione: ogni spesa ulteriore da oggi al {c['next_payday'].strftime('%d %b')} intaccherà i risparmi accumulati!</i>"
        ])

    msg.extend([
        "",
        f"🏦 <b>Patrimonio & Risparmi Protetti:</b> €{s['liquid_cash']:.2f} (TR, ISY, Contanti)"
    ])

    if s["intesa_shortfall"] > 0:
        msg.extend([
            "",
            "🚨 <b>ALERT ADDEBITO DIRETTO INTESA!</b>",
            f"• Saldo Intesa: €{s['balances'].get('Intesa', 0.0):.2f}",
            f"• Bollette in arrivo su Intesa: €{s['intesa_pending']:.2f}",
            f"• <b>Scoperto previsto: €{s['intesa_shortfall']:.2f}</b>",
            f"👉 <i>Azione: Trasferisci almeno <b>€{s['intesa_shortfall'] + 20:.2f}</b> da Trade Republic a Intesa prima del 20 Nov!</i>"
        ])

    return "\n".join(msg)

def format_saldi_report(s):
    b = s["balances"]
    lines = [
        "💰 <b>SALDI DEI CONTI IN TEMPO REALE</b>",
        "──────────────────────────────",
        f"🏦 <b>Intesa Sanpaolo:</b> €{b.get('Intesa', 0.0):.2f}",
        f"💳 <b>ISY:</b> €{b.get('ISY', 0.0):.2f}",
        f"📈 <b>Trade Republic (Cash):</b> €{b.get('Trade Republic', 0.0):.2f}",
        f"🛒 <b>Budget Settimana:</b> €{b.get('Budget Settimana', 0.0):.2f}",
        f"📊 <b>Trade Investiti (Titoli):</b> €{b.get('Trade Investiti', 0.0):.2f}",
        f"💵 <b>Contante:</b> €{b.get('Contante', 0.0):.2f}",
        f"🎫 <b>Buoni Pasto:</b> €{b.get('Buoni Pasto', 0.0):.2f}",
        "──────────────────────────────",
        f"💎 <b>Liquidità Pronta:</b> €{s['liquid_cash']:.2f}",
        f"💼 <b>Patrimonio Totale Tracciato:</b> €{sum(b.values()):.2f}"
    ]
    return "\n".join(lines)

def format_bollette_report(s):
    lines = [
        "📅 <b>SCADENZIARIO BOLLETTE & SPESE FISSE</b>",
        "──────────────────────────────"
    ]
    if not s["pending_bills"]:
        lines.append("🎉 Nessuna spesa fissa in scadenza prima del prossimo stipendio!")
    else:
        for b in s["pending_bills"]:
            due_str = f"tra {b['days_until']} gg" if b['days_until'] > 1 else ("domani" if b['days_until'] == 1 else "OGGI")
            lines.append(f"• <b>{b['day']:02d} {b['due_date'].strftime('%b')}</b> ({due_str}): <b>€{b['amount']:.2f}</b> · {b['name']} (da <i>{b['account']}</i>)")
    
    lines.append("──────────────────────────────")
    lines.append(f"Totale in uscita prima del Payday: <b>€{s['total_pending_bills']:.2f}</b>")
    return "\n".join(lines)

def format_spese_report(s):
    cats = s["category_totals"]
    lines = [
        "🛒 <b>RIEPILOGO SPESE CICLO ATTUALE</b>",
        f"Periodo: {s['cycle']['start'].strftime('%d %b')} → {s['today'].strftime('%d %b')}",
        "──────────────────────────────"
    ]
    sorted_cats = sorted(cats.items(), key=lambda x: x[1], reverse=True)
    for cat, val in sorted_cats[:12]:
        is_fixed = " (fissa)" if cat in FIXED_AND_TRAVEL_CATEGORIES else ""
        lines.append(f"• {cat}: <b>€{val:.2f}</b>{is_fixed}")
    lines.append("──────────────────────────────")
    lines.append(f"Spese Variabili Pivot: <b>€{s['variable_spend']:.2f}</b>")
    return "\n".join(lines)

def format_investiti_report():
    lines = [
        "📈 <b>PORTAFOGLIO TRADE REPUBLIC</b>",
        "──────────────────────────────",
        "💰 <b>Guadagni Chiusi Incassati:</b> <b>+€126.86</b>",
        "  (Trading Netto: +€87.80 · Dividendi: +€39.06)",
        "",
        "📊 <b>Posizioni Aperte (Ongoing):</b>",
        "• Energiekontor (EKT.DE): 2 azioni · P&L: -€77.50",
        "• Eutelsat (ETL.PA): 14 azioni · P&L: -€51.24",
        "• Amundi FTSE Italia PIR (ITAMID.MI): 1.13 az · P&L: -€0.10",
        "• MSCI World Energy ETF (2B79.DE): 6.40 az · P&L: +€6.38",
        "──────────────────────────────",
        "Valore Contabile ezBookkeeping: <b>€435.51</b>",
        "<i>Le posizioni aperte sono mantenute a lungo termine come da piano.</i>"
    ]
    return "\n".join(lines)

def generate_tx_uuid():
    now = int(time.time())
    return ((now & 0xFFFFFFFF) << 31) | ((3 & 0xF) << 27) | (1 & 0x7FFFF)

def quick_add_expense(amount, text):
    cat_id, cat_name = DEFAULT_CATEGORY
    words = text.lower().split()
    for w in words:
        if w in CATEGORY_MAP:
            cat_id, cat_name = CATEGORY_MAP[w]
            break

    cents = int(round(amount * 100))
    tx_id = generate_tx_uuid()
    now_ms = int(time.time() * 1000)
    now_unix = int(time.time())

    sql_tx = f"""
        INSERT INTO transaction (
            transaction_id, uid, deleted, type, category_id, account_id,
            transaction_time, timezone_utc_offset, amount, related_id,
            related_account_id, related_account_amount, hide_amount, comment,
            created_unix_time, updated_unix_time
        ) VALUES (
            {tx_id}, {USER_UID}, 0, 3, {cat_id}, {DEFAULT_ACCOUNT_ID},
            {now_ms}, 60, {cents}, 0,
            0, 0, 0, '{text.replace("'", "''")}',
            {now_unix}, {now_unix}
        );
    """
    exec_sql(sql_tx)
    exec_sql(f"UPDATE account SET balance = balance - {cents} WHERE account_id = {DEFAULT_ACCOUNT_ID} AND uid = {USER_UID};")

    res = run_query(f"SELECT balance FROM account WHERE account_id = {DEFAULT_ACCOUNT_ID} AND uid = {USER_UID};")
    new_bal = float(res[0]["balance"]) / 100.0 if res else 0.0

    return cat_name, new_bal

def morning_scheduler():
    log.info("Starting morning scheduler thread (target: 08:30 CET)")
    last_sent_date = None
    while True:
        try:
            now = datetime.now()
            if now.hour == 8 and now.minute == 30 and last_sent_date != now.date():
                log.info("Sending scheduled morning report...")
                status = get_financial_status()
                msg = format_oggi_report(status)
                send_telegram(msg)
                last_sent_date = now.date()
        except Exception as e:
            log.error("Scheduler error: %s", e)
        time.sleep(30)

def main():
    log.info("ezBookkeeping Coach Bot starting up...")
    Thread(target=morning_scheduler, daemon=True).start()

    offset = 0
    menu_keyboard = {
        "keyboard": [
            [{"text": "/oggi"}, {"text": "/saldi"}],
            [{"text": "/bollette"}, {"text": "/spese"}, {"text": "/investiti"}]
        ],
        "resize_keyboard": True
    }

    while True:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={offset}&timeout=40"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=50) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            
            if not data.get("ok"):
                time.sleep(5)
                continue

            for update in data.get("result", []):
                offset = update["update_id"] + 1
                msg = update.get("message")
                if not msg:
                    continue

                chat_id = str(msg.get("chat", {}).get("id", ""))
                if chat_id != ALLOWED_CHAT_ID:
                    log.warning("Ignoring message from unauthorized chat_id: %s", chat_id)
                    continue

                text = msg.get("text", "").strip()
                if not text:
                    continue

                log.info("Received command: %s", text)
                cmd = text.lower()

                if cmd in ("/start", "/help", "/aiuto"):
                    reply = (
                        "👋 <b>Ciao Ion! Sono il tuo Coach Finanziario per ezBookkeeping.</b>\n\n"
                        "📊 <b>Comandi Rapidi:</b>\n"
                        "• /oggi — Budget giornaliero, pacing 3-lines e alert bonifici\n"
                        "• /saldi — Saldo istantaneo di tutti i tuoi conti\n"
                        "• /bollette — Prossimi addebiti fissi (rata auto, affitto, ecc.)\n"
                        "• /spese — Spese del ciclo attuale per categoria\n"
                        "• /investiti — Rendimenti e posizioni Trade Republic\n\n"
                        "✏️ <b>Registrazione Rapida Spese:</b>\n"
                        "Scrivimi direttamente l'importo e la causale per registrarla istantaneamente su <b>Budget Settimana</b>!\n"
                        "<i>Esempi:</i>\n"
                        "• <code>14.50 Pranzo lavoro</code>\n"
                        "• <code>35.20 Spesa Conad</code>\n"
                        "• <code>1.50 Caffe bar</code>"
                    )
                    send_telegram(reply, reply_markup=menu_keyboard)

                elif cmd in ("/oggi", "/runway", "/budget"):
                    status = get_financial_status()
                    reply = format_oggi_report(status)
                    send_telegram(reply, reply_markup=menu_keyboard)

                elif cmd in ("/saldi", "/conti", "/saldo"):
                    status = get_financial_status()
                    reply = format_saldi_report(status)
                    send_telegram(reply, reply_markup=menu_keyboard)

                elif cmd in ("/bollette", "/scadenze"):
                    status = get_financial_status()
                    reply = format_bollette_report(status)
                    send_telegram(reply, reply_markup=menu_keyboard)

                elif cmd in ("/spese", "/breakdown"):
                    status = get_financial_status()
                    reply = format_spese_report(status)
                    send_telegram(reply, reply_markup=menu_keyboard)

                elif cmd in ("/investiti", "/tr", "/stocks"):
                    reply = format_investiti_report()
                    send_telegram(reply, reply_markup=menu_keyboard)

                else:
                    m = re.match(r"^(\d+(?:[.,]\d{1,2})?)\s+(.+)$", text)
                    if m:
                        amt_str = m.group(1).replace(",", ".")
                        desc = m.group(2).strip()
                        amount = float(amt_str)
                        cat_name, new_bal = quick_add_expense(amount, desc)
                        reply = (
                            f"✅ <b>Spesa registrata con successo!</b>\n"
                            f"• Importo: <b>€{amount:.2f}</b>\n"
                            f"• Categoria: <b>{cat_name}</b>\n"
                            f"• Conto: <b>Budget Settimana</b>\n"
                            f"• Nuovo Saldo: <b>€{new_bal:.2f}</b>\n"
                            f"• Nota: <i>{desc}</i>"
                        )
                        send_telegram(reply, reply_markup=menu_keyboard)
                    else:
                        reply = "❓ Comando non riconosciuto. Usa /oggi, /saldi, /bollette oppure inserisci una spesa es. <code>12.50 Pranzo</code>."
                        send_telegram(reply, reply_markup=menu_keyboard)

        except Exception as e:
            log.error("Error in bot loop: %s", e)
            time.sleep(5)

if __name__ == "__main__":
    main()
