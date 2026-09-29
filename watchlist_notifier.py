#!/usr/bin/env python3
"""Watchlist monitor script: checks watchlist stocks and sends email update."""

import os
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import datetime

# Ensure simple-agent app is on sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.firestore_backend import get_watchlist
from app.trading_tools import get_crossover_signals

RECIPIENT_EMAIL = "gadagool.krishna@gmail.com"
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")

def run_watchlist_check():
    now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    watchlist_data = get_watchlist()
    items = watchlist_data.get("watchlist", [])
    
    lines = [
        f"=== Swing Trading Watchlist Alert ({now_str}) ===",
        f"Recipient: {RECIPIENT_EMAIL}",
        f"Total Tracked Assets: {len(items)}\n",
    ]
    
    for item in items:
        symbol = item.get("symbol", "")
        company = item.get("company_name", "")
        saved_action = item.get("action", "")
        target = item.get("target_price", 0)
        stop = item.get("stop_loss", 0)
        
        signals = get_crossover_signals(symbol)
        curr_price = signals.get("current_price", "N/A")
        verdict = signals.get("swing_strategy_verdict", {}).get("action", "N/A")
        conviction = signals.get("swing_strategy_verdict", {}).get("conviction_score", "N/A")
        crossover = signals.get("crossover_analysis", {}).get("current_alignment", "N/A")
        
        lines.append(f"• {symbol} ({company}):")
        lines.append(f"   Current Price: ${curr_price} | Live Signal: {verdict} (Conviction: {conviction})")
        lines.append(f"   Watchlist Target: ${target} | Stop-Loss: ${stop}")
        lines.append(f"   MA Alignment: {crossover}")
        lines.append("")

    report_text = "\n".join(lines)
    print(report_text)
    
    # Save latest execution report
    log_dir = os.path.join(BASE_DIR, "logs")
    os.makedirs(log_dir, exist_ok=True)
    with open(os.path.join(log_dir, "last_watchlist_alert.txt"), "w") as f:
        f.write(report_text)
        
    # Attempt email delivery if credentials configured
    if SMTP_USER and SMTP_PASS:
        try:
            msg = MIMEMultipart()
            msg["From"] = SMTP_USER
            msg["To"] = RECIPIENT_EMAIL
            msg["Subject"] = f"📈 Swing Trading Watchlist Update - {now_str}"
            msg.attach(MIMEText(report_text, "plain"))
            
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASS)
                server.send_message(msg)
            print(f"✅ Email successfully delivered to {RECIPIENT_EMAIL}")
        except Exception as e:
            print(f"⚠️ Email delivery failed: {e}")
    else:
        print(f"ℹ️ SMTP credentials (SMTP_USER & SMTP_PASS) not configured. Report saved to logs/last_watchlist_alert.txt.")

if __name__ == "__main__":
    run_watchlist_check()
