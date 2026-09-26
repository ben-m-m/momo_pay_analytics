"""
Public API:
    load_transactions()  -> list[dict]
    parse_sms_xml()      -> (txs, skipped_otp, skipped_unknown)
    parse_and_save()     -> list[dict]
"""

import xml.etree.ElementTree as ET
import json
import pathlib
import re
from datetime import datetime
from zoneinfo import ZoneInfo


ROOT = pathlib.Path(__file__).resolve().parents[1]
XML_PATH = ROOT / "modified_sms_v2.xml"
JSON_PATH = ROOT / "data" / "transactions.json"
RW_TZ = ZoneInfo("Africa/Kigali")


OTP_MARKERS = (
    "otp",
    "one-time password",
    "one time password",
    "verification code",
    "your code is",
)

def is_otp(body: str) -> bool:
    if not body:
        return False
    lowered = body.lower()
    return any(marker in lowered for marker in OTP_MARKERS)

def _epoch_millisec_to_iso(ms):
    """convert a unix milliseconds timestamp 
    to YYYY-MM-DD HH:MM:SS in Kigali LOcal time
    """
    
    if ms is None:
        return None
    try:
        seconds = int(ms) / 1000
        dt = datetime.fromtimestamp(seconds, tz=RW_TZ)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (TypeError, ValueError, OverflowError, OSError):
        return None

def _to_float(s):

    if s is None:
        return None
    try:
        cleaned = str(s).replace(",", "").strip()
        return float(cleaned)
    except (TypeError, ValueError):
        return None

# status helper
def _status_for(transaction_type):
    # map a transaction to its status
    mapping = {
        "failed_transaction": "failed",
        "reversal_initiated": "pending_reversal",
        "reversal_confirmed": "reversed",
        "statement_line": "statement",
    }
    return mapping.get(transaction_type, "ok")


def _extract_from_body(body, date_ms):
    """
    Extracts transaction type, amount, sender, receiver, timestamp
    from sms boday
    ORDER: templates are checked most specific first
            because later blocks would overshadow earlier ones
            such as airtime before payment
    If no human readable timestamp in text message, falls back to
    date_ms (epoch ms).
    Returns None if no matches found
    """

    if not body:
        return None

    if "You have received" in body:
        amount = re.search(r"([\d,]+(?:\.\d+)?)\s*RWF", body)
        sender = re.search(r"from\s+(.+?)\s*\(", body)
        time_stamp = re.search(r"at\s+(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})", body)
        if amount and sender:
            return (
                "received",
                _to_float(amount.group(1)),
                sender.group(1).strip(),
                "self",
                time_stamp.group(1) if time_stamp else _epoch_millisec_to_iso(date_ms)
            )
    # failed transactions with difering context
    if "has failed" in body and "Your payment of" in body:
        # Failed transaction
        amount = re.search(r"Your payment of\s+([\d,]+(?:\.\d+)?)\s*RWF", body)
        receiver = re.search(r"to\s+(.+?)(?:\s+with token)?\s+has failed", body)
        time_stamp = re.search(r"at\s+(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})", body)
        if amount and receiver:
            return (
                "failed_transaction",
                _to_float(amount.group(1)),
                "self",
                receiver.group(1).strip(),
                time_stamp.group(1) if time_stamp else _epoch_millisec_to_iso(date_ms),
            )

    if "the transaction with amount" in body and "failed at" in body:
        amount = re.search(r"the transaction with amount\s+([\d,]+(?:\.\d+)?)\s*RWF", body)
        receiver = re.search(r"for\s+(.+?)\s+with message", body)
        time_stamp = re.search(r"failed at\s+(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})", body)

        if amount and receiver:
            return (
                "failed_transaction",
                _to_float(amount.group(1)),
                "self",
                receiver.group(1).strip(),
                time_stamp.group(1) if time_stamp else _epoch_millisec_to_iso(date_ms),
            )

    if "has been reversed" in body:
        #succesful reversal filter
        amount = re.search(r"with\s+([\d,]+(?:\.\d+)?)\s*RWF", body)
        receiver = re.search(r"to\s+(.+?)\s*\(", body)
        time_stamp = re.search(r"at\s+(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})", body)
        if amount and receiver:
            return (
                "reversal_confirmed",
                _to_float(amount.group(1)),
                "self",
                receiver.group(1).strip(),
                time_stamp.group(1) if time_stamp else _epoch_millisec_to_iso(date_ms),
            )

    if "A reversal has been initiated" in body:
        amount = re.search(r"with\s+([\d,]+(?:\.\d+)?)\s*RWF", body)
        receiver = re.search(r"to\s+(.+?)\s*\(", body)
        if amount and receiver:
            return (
                "reversal_initiated",
                _to_float(amount.group(1)),
                "self",
                receiver.group(1).strip(),
                _epoch_millisec_to_iso(date_ms),
            )


    if "Your payment of" in body and "to Airtime" in body:
        # airtime transaction
        amount = re.search(r"Your payment of\s+([\d,]+(?:\.\d+)?)\s*RWF", body)
        time_stamp = re.search(r"at\s+(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})", body)
        if amount:
            return (
                "airtime",
                _to_float(amount.group(1)),
                "self",
                "Airtime",
                time_stamp.group(1) if time_stamp else _epoch_millisec_to_iso(date_ms)
            )

    if "Umaze kugura" in body:
        amount = re.search(r"Umaze kugura\s+([\d,]+(?:\.\d+)?)", body)
        if amount:
            return (
                "bundle_purchase",
                _to_float(amount.group(1)),
                "self",
                "MTN",
                _epoch_millisec_to_iso(date_ms)
            )


    if "Your payment of" in body and "has been completed" in body:
        amount = re.search(r"Your payment of\s+([\d,]+(?:\.\d+)?)\s*RWF", body)
        receiver = re.search(r"to\s+(.+?)(?:\s+\d+)?\s+has been completed", body)
        time_stamp = re.search(r"at\s+(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})", body)

        if amount and receiver:
            return (
                "payment",
                _to_float(amount.group(1)),
                "self",
                receiver.group(1).strip(),
                time_stamp.group(1) if time_stamp else _epoch_millisec_to_iso(date_ms),
            )

    if "You have transferred" in body:
        # bank transfer
        amount = re.search(r"You have transferred\s+([\d,]+(?:\.\d+)?)\s*RWF", body)
        receiver = re.search(r"transferred\s+[\d,]+\s*RWF\s+to\s+(.+?)\s*\(", body)
        time_stamp = re.search(r"at\s+(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})", body)

        if amount and receiver:
            return (
                "bank_transfer",
                _to_float(amount.group(1)),
                "self",
                receiver.group(1).strip(),
                time_stamp.group(1) if time_stamp else _epoch_millisec_to_iso(date_ms)
            )

    if "A transaction of" in body and "by" in body and "on your MOMO" in body:
        amount = re.search(r"A transaction of\s+([\d,]+(?:\.\d+)?)\s*RWF", body)
        sender = re.search(r"RWF\s+by\s+(.+?)\s+on your MOMO", body)
        time_stamp = re.search(r"at\s+(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})", body)
        if amount and sender:
            return (
                "direct_payment",
                _to_float(amount.group(1)),
                sender.group(1).strip(),
                "self",
                time_stamp.group(1) if time_stamp else _epoch_millisec_to_iso(date_ms)
            )


    if "have via agent:" in body and "withdrawn" in body:
        # agent withdrawals
        amount = re.search(r"withdrawn\s+([\d,]+(?:\.\d+)?)\s*RWF", body)
        receiver = re.search(r"agent:\s+(.+?)\s*\(", body)
        time_stamp = re.search(r"at\s+(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})", body)
        if amount and receiver:
            return (
                "agent_withdrawal",
                _to_float(amount.group(1)),
                "self",
                receiver.group(1).strip(),
                time_stamp.group(1) if time_stamp else _epoch_millisec_to_iso(date_ms)
            )
        

    if "RWF transferred to" in body:
        amount = re.search(r"([\d,]+(?:\.\d+)?)\s*RWF\s+transferred", body)
        receiver = re.search(r"transferred to\s+(.+?)\s*\(", body)
        time_stamp = re.search(r"at\s+(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})", body)
        if amount and receiver:
            return (
                "transfer",
                _to_float(amount.group(1)),
                "self",
                receiver.group(1).strip(),
                time_stamp.group(1) if time_stamp else _epoch_millisec_to_iso(date_ms),
            )

    if "A bank deposit of" in body:
        amount = re.search(r"A bank deposit of\s+([\d,]+(?:\.\d+)?)\s*RWF", body)
        time_stamp = re.search(r"at\s+(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})", body)

        if amount:
            return (
                "deposit",
                _to_float(amount.group(1)),
                "bank",
                "self",
                time_stamp.group(1) if time_stamp else _epoch_millisec_to_iso(date_ms),
            )        


    if "DEPOSIT RWF" in body and "Receiver:" in body:
        amount = re.search(r"DEPOSIT\s+RWF\s+([\d,]+(?:\.\d+)?)", body)
        date = re.search(r"(\d{4}-\d{2}-\d{2})", body)
        if amount and date:
            return (
                "statement_line",
                _to_float(amount.group(1)),
                "bank",
                "self",
                date.group(1) + " 00:00:00",
            )

        
    return None

def parse_sms_xml(path=XML_PATH, include_otp=False, include_unknown=False):
    tree = ET.parse(path)
    root = tree.getroot()

    transactions = []
    next_id = 1
    skipped_otp = 0
    skipped_unknown = 0

    for sms in root.iter("sms"):
        try:
            body = sms.attrib.get("body", "")
            date = sms.attrib.get("date")

            # OTP before extraction
            if is_otp(body):
                skipped_otp += 1
                if not include_otp:
                    continue
                transactions.append({
                    "id": next_id,
                    "transaction_type": "otp",
                    "amount": None,
                    "sender": None,
                    "receiver": None,
                    "timestamp": _epoch_millisec_to_iso(date),
                    "status": "otp",
                    "txid": None,
                    "body": body,
                })
                next_id += 1
                continue
            # Extract
            parsed = _extract_from_body(body, date)

            if parsed is None:
                skipped_unknown += 1
                if not include_unknown:
                    continue
                transactions.append({
                    "id": next_id,
                    "transaction_type": "unknown",
                    "amount": None,
                    "sender": None,
                    "receiver": None,
                    "timestamp": _epoch_millisec_to_iso(date),
                    "status": "unknown",
                    "txid": None,
                    "body": body,
                })
                next_id += 1
                continue

            # Building the dictionary
            tx_type, amount, sender, receiver, timestamp = parsed

            txid_match = re.search(r"(?:TxId[:\s]*|Financial Transaction Id:\s*)(\d+)", body)
            txid = txid_match.group(1) if txid_match else None

            transactions.append({
                "id": next_id,
                "transaction_type": tx_type,
                "amount": amount,
                "sender": sender,
                "receiver": receiver,
                "timestamp": timestamp,
                "status": _status_for(tx_type),
                "txid": txid,
                "body": body,
            })
            next_id += 1

        except Exception as ex:
            skipped_unknown += 1
            print(f"[warn] skipping malformed record: {ex}")
            continue

    return transactions, skipped_otp, skipped_unknown


def save_json(transactions, path=JSON_PATH):
    #write the transactions list into a JSON file
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(transactions, indent=2))
    return path

def load_transactions(path=JSON_PATH):
    """
    Load transactions from JSON. if file doesnt exist, generate it.
    Th e function the API and DSA modules import
    """
    if not path.exists():
        parse_and_save()
    return json.loads(path.read_text())

def parse_and_save(xml_path=XML_PATH, json_path=JSON_PATH):
    #CLI entry point: parse XML, write JSON, print summary
    txs, otp, unknown = parse_sms_xml(xml_path)
    save_json(txs, json_path)
    print(f"Saved {len(txs)} transactions")
    print(f"---Skipped {otp} OTP")
    print(f"---Skipped {unknown} unrecognized")
    print(f" path -> {json_path}")
    return txs



