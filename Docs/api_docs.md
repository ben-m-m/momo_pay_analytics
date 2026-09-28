# MoMo SMS REST API Documentation

## Base URL

```
http://localhost:8000
```

## Authentication

All endpoints require HTTP Basic Authentication. See `auth_docs.md` for full details.

```
Authorization: Basic <base64(username:password)>
```

## Data Model

Each transaction object contains the following fields:

| Field             | Type    | Description                                      |
|-------------------|---------|--------------------------------------------------|
| id                | integer | Auto generated unique identifier                 |
| transaction_type  | string  | Type of transaction (e.g. "INCOMING", "OUTGOING")|
| amount            | float   | Transaction amount (must be greater than zero)    |
| sender            | string  | Phone number or name of the sender               |
| receiver          | string  | Phone number or name of the receiver             |
| timestamp         | string  | Date and time of the transaction                 |
| status            | string  | Transaction status (e.g. "ok", "failed")         |
| txid              | string  | External transaction reference ID                |
| body              | string  | Original SMS message body                        |

---

## Endpoints

### 1. List All Transactions

**GET** `/transactions`

Returns all transactions in the database. Supports optional query parameter filtering.

#### Query Parameters

| Parameter        | Type   | Description                              |
|------------------|--------|------------------------------------------|
| transaction_type | string | Filter by transaction type (case insensitive) |
| status           | string | Filter by status (case insensitive)      |

#### Request

```bash
curl -u admin:password123 http://localhost:8000/transactions
```

#### Response (200 OK)

```json
{
  "count": 2,
  "transactions": [
    {
      "id": 1,
      "transaction_type": "INCOMING",
      "amount": 5000.0,
      "sender": "0781234567",
      "receiver": "0789876543",
      "timestamp": "2024-01-15 10:30:00",
      "status": "ok",
      "txid": "TXN001",
      "body": "You have received 5000 RWF from 0781234567"
    },
    {
      "id": 2,
      "transaction_type": "OUTGOING",
      "amount": 2000.0,
      "sender": "0789876543",
      "receiver": "0781234567",
      "timestamp": "2024-01-15 11:00:00",
      "status": "ok",
      "txid": "TXN002",
      "body": "You have sent 2000 RWF to 0781234567"
    }
  ]
}
```

#### Filtered Request

```bash
# Filter by transaction type
curl -u admin:password123 "http://localhost:8000/transactions?transaction_type=INCOMING"

# Filter by status
curl -u admin:password123 "http://localhost:8000/transactions?status=ok"

# Both filters combined
curl -u admin:password123 "http://localhost:8000/transactions?transaction_type=INCOMING&status=ok"
```

---

### 2. Get a Single Transaction

**GET** `/transactions/<id>`

Returns one transaction by its ID.

#### Request

```bash
curl -u admin:password123 http://localhost:8000/transactions/1
```

#### Response (200 OK)

```json
{
  "id": 1,
  "transaction_type": "INCOMING",
  "amount": 5000.0,
  "sender": "0781234567",
  "receiver": "0789876543",
  "timestamp": "2024-01-15 10:30:00",
  "status": "ok",
  "txid": "TXN001",
  "body": "You have received 5000 RWF from 0781234567"
}
```

#### Error Response (404 Not Found)

```json
{
  "error": "Transaction with id 999 not found."
}
```

---

### 3. Create a Transaction

**POST** `/transactions`

Creates a new transaction and adds it to the database.

#### Required Fields

| Field            | Type   | Description                     |
|------------------|--------|---------------------------------|
| amount           | number | Must be greater than zero       |
| transaction_type | string | Type of the transaction         |

#### Optional Fields

| Field     | Type   | Default |
|-----------|--------|---------|
| sender    | string | null    |
| receiver  | string | null    |
| timestamp | string | ""      |
| status    | string | "ok"    |
| txid      | string | null    |
| body      | string | ""      |

#### Request

```bash
curl -u admin:password123 -X POST http://localhost:8000/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_type": "INCOMING",
    "amount": 15000,
    "sender": "0781112222",
    "receiver": "0783334444",
    "status": "ok"
  }'
```

#### Response (201 Created)

```json
{
  "message": "Transaction created.",
  "transaction": {
    "id": 3,
    "transaction_type": "INCOMING",
    "amount": 15000.0,
    "sender": "0781112222",
    "receiver": "0783334444",
    "timestamp": "",
    "status": "ok",
    "txid": null,
    "body": ""
  }
}
```

#### Error Responses

**Missing required fields (400):**
```json
{
  "error": "Missing required fields: amount, transaction_type"
}
```

**Invalid amount (400):**
```json
{
  "error": "Amount must be greater than zero."
}
```

**Non numeric amount (400):**
```json
{
  "error": "Amount must be a number."
}
```

**Invalid JSON body (400):**
```json
{
  "error": "Request body must be valid JSON."
}
```

---

### 4. Update a Transaction

**PUT** `/transactions/<id>`

Updates an existing transaction. Only the fields included in the request body are changed. Fields not included remain unchanged.

#### Request

```bash
curl -u admin:password123 -X PUT http://localhost:8000/transactions/1 \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 7500,
    "status": "updated"
  }'
```

#### Response (200 OK)

```json
{
  "message": "Transaction updated.",
  "transaction": {
    "id": 1,
    "transaction_type": "INCOMING",
    "amount": 7500.0,
    "sender": "0781234567",
    "receiver": "0789876543",
    "timestamp": "2024-01-15 10:30:00",
    "status": "updated",
    "txid": "TXN001",
    "body": "You have received 5000 RWF from 0781234567"
  }
}
```

#### Updatable Fields

`transaction_type`, `amount`, `sender`, `receiver`, `timestamp`, `status`, `txid`, `body`

The `id` field cannot be changed.

#### Error Responses

**Transaction not found (404):**
```json
{
  "error": "Transaction with id 999 not found."
}
```

**Invalid amount (400):**
```json
{
  "error": "Amount must be greater than zero."
}
```

---

### 5. Delete a Transaction

**DELETE** `/transactions/<id>`

Permanently removes a transaction from the database.

#### Request

```bash
curl -u admin:password123 -X DELETE http://localhost:8000/transactions/1
```

#### Response (200 OK)

```json
{
  "message": "Transaction 1 deleted successfully."
}
```

#### Error Response (404 Not Found)

```json
{
  "error": "Transaction with id 1 not found."
}
```

---

## Error Handling Summary

| Status Code | Meaning               | When It Occurs                                   |
|-------------|-----------------------|--------------------------------------------------|
| 200         | OK                    | Successful GET, PUT, or DELETE                   |
| 201         | Created               | Successful POST (new transaction created)        |
| 400         | Bad Request           | Invalid JSON, missing fields, or invalid amount  |
| 401         | Unauthorized          | Missing, malformed, or incorrect credentials     |
| 404         | Not Found             | Transaction ID does not exist or invalid endpoint|

## Running the Server

```bash
python api.py
```

The server starts on `http://0.0.0.0:8000` and loads existing transactions from `data/transactions.json` if available. If the JSON file does not exist, the server attempts to generate it by running the XML parser. If that also fails, the server starts with an empty database.

All data is stored in memory. Changes made through POST, PUT, and DELETE are lost when the server is restarted.