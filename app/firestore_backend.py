# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
from typing import Any, Dict, List, Optional
from google.cloud import firestore

# IMPORTANT: Hardcoded project ID as string.
# On Agent Platform, google.auth.default() or GOOGLE_CLOUD_PROJECT can return
# the project number which breaks Firestore client.
PROJECT_ID = "qwiklabs-gcp-03-6fca0bafb4e6"
COLLECTION_NAME = "watchlist"

_db: Optional[firestore.Client] = None


def get_firestore_client() -> firestore.Client:
    """Returns a singleton Firestore client explicitly pinned to the project string."""
    global _db
    if _db is None:
        _db = firestore.Client(project=PROJECT_ID)
    return _db


def add_to_watchlist(
    symbol: str,
    company_name: str,
    action: str,
    target_price: float,
    stop_loss: float,
    notes: str = ""
) -> Dict[str, Any]:
    """Adds or updates a stock symbol in the swing trading watchlist.

    Args:
        symbol: The stock ticker symbol (e.g. 'AAPL', 'MSFT', 'TSLA').
        company_name: The human-readable name of the company.
        action: Recommended swing trading action ('BUY', 'SELL', 'WATCH').
        target_price: Target take-profit price.
        stop_loss: Invalidation stop-loss price.
        notes: Strategic notes or rationales for the trade setup.

    Returns:
        A dictionary confirming the saved watchlist item.
    """
    clean_sym = symbol.strip().upper()
    db = get_firestore_client()
    doc_ref = db.collection(COLLECTION_NAME).document(clean_sym)
    
    data = {
        "symbol": clean_sym,
        "company_name": company_name,
        "action": action.upper(),
        "target_price": float(target_price),
        "stop_loss": float(stop_loss),
        "notes": notes,
        "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    
    doc_ref.set(data, merge=True)
    return {
        "status": "success",
        "message": f"Saved {clean_sym} to watchlist in Firestore.",
        "data": data
    }


def get_watchlist() -> Dict[str, Any]:
    """Retrieves all tracked stocks and trade plans from the Firestore watchlist.

    Returns:
        A dictionary containing the list of watchlist items.
    """
    db = get_firestore_client()
    docs = db.collection(COLLECTION_NAME).stream()
    items: List[Dict[str, Any]] = []
    for doc in docs:
        d = doc.to_dict()
        items.append(d)
        
    return {
        "count": len(items),
        "watchlist": items
    }


def remove_from_watchlist(symbol: str) -> Dict[str, Any]:
    """Removes a stock from the swing trading watchlist.

    Args:
        symbol: The stock ticker symbol to remove.

    Returns:
        A dictionary confirming removal status.
    """
    clean_sym = symbol.strip().upper()
    db = get_firestore_client()
    db.collection(COLLECTION_NAME).document(clean_sym).delete()
    return {
        "status": "success",
        "message": f"Removed {clean_sym} from watchlist."
    }
