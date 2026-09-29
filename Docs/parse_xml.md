# `dsa/parse_xml.py` — SMS Parser Module

**Author:** `<Benson Maina>`
**Date:** 2026-09-25
**Purpose:** Parse `modified_sms_v2.xml` (MTN MoMo SMS backup) into a
structured list of transaction dictionaries for downstream use by
the API and DSA modules.

---

## Overview

The MTN MoMo SMS backup contains 1,691 records. Each `<sms>` element
has a `body` attribute containing free-form text with **13 distinct
message templates** (English + Kinyarwanda). The parser:

1. Reads every `<sms>` element from the XML
2. Filters out OTP / verification messages
3. Classifies each remaining body into one of 13 transaction templates
4. Extracts five fields: `transaction_type`, `amount`, `sender`,
   `receiver`, `timestamp`
5. Adds `status`, `txid`, and the raw `body` for audit
6. Returns a list of dicts (and can save/load as JSON)

**Result:** 1,683 transactions extracted, 8 OTP messages filtered out,
0 unrecognized. Full accounting: `1683 + 8 + 0 = 1691`.

---

## Public API

| Function | Signature | Returns | Used by |
|---|---|---|---|
| `parse_sms_xml` | `(path=XML_PATH, include_otp=False, include_unknown=False)` | `(transactions, skipped_otp, skipped_unknown)` | Tests, debugging |
| `parse_and_save` | `(xml_path=XML_PATH, json_path=JSON_PATH)` | `list[dict]` | CLI entry point |
| `load_transactions` | `(path=JSON_PATH)` | `list[dict]` | **API + DSA modules** |
| `save_json` | `(transactions, path=JSON_PATH)` | `Path` | Internal |
| `is_otp` | `(body: str)` | `bool` | Public utility |
| `_extract_from_body` | `(body, date_ms)` | `tuple` or `None` | Internal (prefix `_`) |

### The dict schema

Every record returned by `load_transactions()` / `parse_sms_xml()` has
exactly these 9 keys:

```python
{
    "id": 1,                                 # int, contiguous from 1
    "transaction_type": "received",          # str, one of 13 types
    "amount": 2000.0,                        # float (never None for parsed records)
    "sender": "Jane Smith",                  # str
    "receiver": "self",                      # str
    "timestamp": "2024-05-10 16:30:51",      # str, Kigali local time
    "status": "ok",                          # str, one of 5 statuses
    "txid": "76662021700",                   # str or None
    "body": "You have received 2000 RWF..."  # str, raw SMS (for audit)
}
```

---

## Transaction Types (13 total)

| Type | Count | Direction | Description |
|---|---|---|---|
| `payment` | 698 | outgoing | Payment to a person or business |
| `transfer` | 585 | outgoing | `*165*` mobile-money transfer |
| `deposit` | 248 | incoming | Bank deposit notification |
| `received` | 63 | incoming | Money received from a person |
| `direct_payment` | 36 | incoming | Business-initiated payment |
| `bundle_purchase` | 21 | outgoing | Data bundle purchase (Kinyarwanda) |
| `airtime` | 15 | outgoing | Airtime top-up |
| `bank_transfer` | 6 | outgoing | Transfer to a bank account |
| `failed_transaction` | 5 | (attempt) | Payment attempted but failed |
| `agent_withdrawal` | 3 | outgoing | Cash withdrawal at an agent |
| `reversal_initiated` | 1 | (state) | Reversal started (pending) |
| `reversal_confirmed` | 1 | (state) | Reversal completed |
| `statement_line` | 1 | (metadata) | Statement excerpt, not a real SMS |

---

## Status Mapping

`status` is derived from `transaction_type` via `_status_for()`:

| `transaction_type` | `status` |
|---|---|
| `failed_transaction` | `"failed"` |
| `reversal_initiated` | `"pending_reversal"` |
| `reversal_confirmed` | `"reversed"` |
| `statement_line` | `"statement"` |
| everything else | `"ok"` |

Final distribution: `ok=1675`, `failed=5`, `pending_reversal=1`,
`reversed=1`, `statement=1`.

---

## Design Decisions

### 1. Sender/Receiver semantics use `"self"` as sentinel

For outgoing transactions, `sender="self"`. For incoming transactions,
`receiver="self"`. This makes direction filterable with one comparison:

```python
incoming = [t for t in txs if t["receiver"] == "self"]
outgoing = [t for t in txs if t["sender"] == "self"]
```

Other semantic labels: `"bank"` (bank deposit source),
`"MTN"` (data bundle provider), `"Airtime"` (airtime purchase).

### 2. Template classification requires two markers

Each template block checks **two distinctive markers** before running
any regex. Example:

```python
if "Your payment of" in body and "to Airtime" in body:
```

`"to Airtime"` is the discriminating marker — the generic payment block
would otherwise swallow airtime messages because they both start with
"Your payment of". **Order matters:** more specific templates must come
before generic ones.

### 3. Timestamp priority: body text > epoch

Human-readable timestamps in the SMS body (`"at 2024-05-10 16:30:51"`)
are preferred because they match what the user sees. The XML's `date`
attribute (Unix milliseconds) is the fallback for templates that don't
include a body timestamp (`bundle_purchase`, `reversal_initiated`).

**Timezone:** All timestamps are converted to **Kigali local time
(Africa/Kigali, UTC+2)** — the timezone the SMS body uses. Using UTC
would produce a 2-hour mismatch between fallback and body timestamps.

### 4. Failed and reversed transactions are included (Option C)

Failed transactions, reversals, and one statement-line record are
**kept in the output** with distinctive `status` values rather than
excluded. Rationale:

- The assignment says "SMS records" — not "successful transactions"
- Excluding silently would hide ~2% of the data
- The API consumer can filter by `status` if they want successful only

### 5. OTP messages are filtered before extraction

`is_otp()` runs **before** `_extract_from_body()`. OTP bodies have no
amount/sender/receiver, so extracting fields would waste time and
produce garbage. The 8 OTP messages are counted separately
(`skipped_otp=8`) and can be included with `include_otp=True`.

### 6. Malformed records are skipped, not fatal

Every iteration is wrapped in `try/except`. A single bad record
increments the skip counter, prints a `[warn]` line, and continues.
The parser never crashes on one bad input.

### 7. `id` values are contiguous starting from 1

Skipped records do not consume an ID. This means `/transactions/{id}`
can be used as a direct index into the list by the API.

---

## Files Produced

| Path | Size | Purpose |
|---|---|---|
| `dsa/parse_xml.py` | ~330 lines | The parser module |
| `dsa/test_parse_xml.py` | ~280 lines | Unit tests (35 tests) |
| `data/transactions.json` | 727 KB | Parsed output (1,683 records) |

---

## Usage Examples

### Basic — load all transactions

```python
from dsa.parse_xml import load_transactions

txs = load_transactions()
print(f"{len(txs)} transactions loaded")
print(txs[0])
```

### Filter by status

```python
successful = [t for t in txs if t["status"] == "ok"]
failed = [t for t in txs if t["status"] == "failed"]
```

### Filter by direction

```python
incoming = [t for t in txs if t["receiver"] == "self"]
outgoing = [t for t in txs if t["sender"] == "self"]
```

### Regenerate the JSON from XML

```bash
cd dsa
python parse_xml.py
```

### Run the test suite

```bash
cd dsa
python -m unittest test_parse_xml -v
```

---

## Known Limitations

1. **Timezone is hardcoded to Kigali** (`Africa/Kigali`). If the data
   ever comes from another timezone, this needs to be parameterized.
2. **`sender="self"` / `receiver="self"` are sentinels**, not real
   account IDs. If the API needs to distinguish multiple accounts,
   the schema would need extension.
3. **Reversals are standalone records** — not linked back to the
   original transaction they reversed (no shared ID available in the
   SMS bodies).
4. **1 failed transaction type is not surfaced separately** — the
   `failed_transaction` type covers both failed bundles and failed
   company payments. If the API needs to distinguish them, add a
   `failure_reason` field.