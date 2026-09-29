# Copyright 2026 Google LLC
# Seed script for Swing Trading Watchlist in Firestore

import datetime
from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-03-6fca0bafb4e6"
COLLECTION_NAME = "watchlist"

def seed():
    print(f"Connecting to Firestore with hardcoded project ID: {PROJECT_ID}")
    db = firestore.Client(project=PROJECT_ID)
    
    initial_items = [
        {
            "symbol": "AAPL",
            "company_name": "Apple Inc.",
            "action": "BUY",
            "target_price": 365.47,
            "stop_loss": 309.90,
            "notes": "20 SMA crossed above 50 SMA. Bullish continuation above 200 SMA macro trend.",
            "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        },
        {
            "symbol": "TSLA",
            "company_name": "Tesla, Inc.",
            "action": "BUY",
            "target_price": 386.05,
            "stop_loss": 339.58,
            "notes": "Tactical mean-reversion swing. 20 SMA > 50 SMA, targeting 200 SMA overhead resistance.",
            "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        },
        {
            "symbol": "NVDA",
            "company_name": "NVIDIA Corporation",
            "action": "BUY",
            "target_price": 247.17,
            "stop_loss": 208.93,
            "notes": "Solid bullish stack (Price > 20 SMA > 50 SMA > 200 SMA) with healthy RSI momentum.",
            "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        },
    ]
    
    for item in initial_items:
        doc_ref = db.collection(COLLECTION_NAME).document(item["symbol"])
        doc_ref.set(item)
        print(f"Seeded {item['symbol']} ({item['company_name']}) -> {item['action']}")
        
    print(f"Successfully seeded {len(initial_items)} watchlist items into Firestore!")

if __name__ == "__main__":
    seed()
