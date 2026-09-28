import json 
import re 
import pathlib
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import base64
 
ROOT = pathlib.Path(__file__).resolve().parents[1]
JSON_PATH = ROOT / "data" / "transactions.json"

HOST = "0.0.0.0"
PORT = 8000

USERS = {
    "admin": "password123",
    "user1": "momo2024"
}
def load_transactions():
    if not JSON_PATH.exists():
        print ("Transactions.json not found, running parser..")
        try:
            from dsa.parse_xml import parse_and_save
            parse_and_save()
        except:
            print("ERROR: data/transactions.json not found and parser unavailable.")
            print("Run 'python dsa/parse_xml.py' first to generate it.")

            return[]
    with open(JSON_PATH , "r") as f:
        return json.load(f)
        
transactions_db = []
next_id_counter = 1

def get_next_id():
    global next_id_counter
    current = next_id_counter
    next_id_counter += 1
    return current

#Request Handler

class MoMoAPIHandler(BaseHTTPRequestHandler):
    def authenticate(self):
        auth_header = self.headers.get("Authorization")
        if auth_header is None or not auth_header.startswith("Basic "):
            self.send_error_response(
                401, "Authentication required. Provide Basic Auth credentials."
            )
            return False
 
        try:
            decoded = base64.b64decode(auth_header[6:]).decode("utf-8")
            username, password = decoded.split(":", 1)
        except Exception:
            self.send_error_response(401, "Malformed Authorization header.")
            return False
        if USERS.get(username) != password:
            self.send_error_response(401, "Invalid username or password.")
            return False
 
        return True
 
    #Response helpers

    def send_json(self, status_code, data):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
 
    def send_error_response(self, status_code, message):
        if status_code == 401:
            body = json.dumps({"error": message}, indent=2).encode("utf-8")
            self.send_response(401)
            self.send_header("Content-Type", "application/json")
            self.send_header("WWW-Authenticate", 'Basic realm="MoMo API"')
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_json(status_code, {"error": message})
 
    def read_body(self):
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            return None
        raw = self.rfile.read(content_length)
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            return None
 
    def parse_path(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        query = parse_qs(parsed.query)
 
        match = re.match(r"^/transactions/(\d+)$", path)
        if match:
            return "transaction_detail", int(match.group(1)), query
 
        if path == "/transactions" or path == "":
            return "transaction_list", None, query
 
        return None, None, query

    def do_GET(self):
        if not self.authenticate():
            return

        route, txn_id, query = self.parse_path()

        if route == "transaction_list" :
            result = list(transactions_db)

            ttype = query.get("transaction_type",[None])[0]
            if ttype:
                result = [
                        t for t in result
                        if t.get("transaction_type", "").lower() == ttype.lower()
                    ]
 
            # Filter by status if provided
            status = query.get("status", [None])[0]
            if status:
                result = [
                    t for t in result
                    if t.get("status", "").lower() == status.lower()
                ]
 
            self.send_json(200, {
                "count": len(result),
                "transactions": result
            })
 
        elif route == "transaction_detail":
            txn = next(
                (t for t in transactions_db if t["id"] == txn_id), None
            )
            if txn is None:
                self.send_error_response(
                    404, f"Transaction with id {txn_id} not found."
                )
            else:
                self.send_json(200, txn)
 
        else:
            self.send_error_response(
                404,
                "Endpoint not found. Use /transactions or /transactions/<id>."
            )
    def do_POST(self):
        if not self.authenticate():
            return

        route, _, query = self.parse_path()
        if route != "transaction_list":
            self.send_error_response(
                404, "POST only supported on /transactions."
            )
            return

        data = self.read_body()
        if data is None:
            self.send_error_response(400, "Request body must be valid JSON.")
            return

        # Validate required fields
        required = ["amount", "transaction_type"]
        missing = [f for f in required if f not in data]
        if missing:
            self.send_error_response(
                400, f"Missing required fields: {', '.join(missing)}"
            )
            return

        # Validate amount is a positive number
        try:
            amount = float(data["amount"])
            if amount <= 0:
                self.send_error_response(
                    400, "Amount must be greater than zero."
                )
                return
        except (ValueError, TypeError):
            self.send_error_response(400, "Amount must be a number.")
            return

        new_txn = {
            "id": get_next_id(),
            "transaction_type": data["transaction_type"],
            "amount": amount,
            "sender": data.get("sender"),
            "receiver": data.get("receiver"),
            "timestamp": data.get("timestamp", ""),
            "status": data.get("status", "ok"),
            "txid": data.get("txid"),
            "body": data.get("body", ""),
        }
        transactions_db.append(new_txn)
        self.send_json(201, {
            "message": "Transaction created.",
            "transaction": new_txn
        })
    
    def do_PUT(self):
        if not self.authenticate():
            return

        route, txn_id, query = self.parse_path()
        if route != "transaction_detail" or txn_id is None:
            self.send_error_response(
                404, "PUT requires /transactions/<id>."
            )
            return

        txn = next(
            (t for t in transactions_db if t["id"] == txn_id), None
        )
        if txn is None:
            self.send_error_response(
                404, f"Transaction with id {txn_id} not found."
            )
            return

        data = self.read_body()
        if data is None:
            self.send_error_response(400, "Request body must be valid JSON.")
            return

        # Update only the fields that were provided
        updatable = [
            "transaction_type", "amount", "sender", "receiver",
            "timestamp", "status", "txid", "body"
        ]
        for field in updatable:
            if field in data:
                if field == "amount":
                    try:
                        val = float(data[field])
                        if val <= 0:
                            self.send_error_response(
                                400, "Amount must be greater than zero."
                            )
                            return
                        txn[field] = val
                    except (ValueError, TypeError):
                        self.send_error_response(
                            400, "Amount must be a number."
                        )
                        return
                else:
                    txn[field] = data[field]

        self.send_json(200, {
            "message": "Transaction updated.",
            "transaction": txn
        })

    def do_DELETE(self):
        if not self.authenticate():
            return

        route, txn_id, query = self.parse_path()
        if route != "transaction_detail" or txn_id is None:
            self.send_error_response(
                404, "DELETE requires /transactions/<id>."
            )
            return

        global transactions_db
        before = len(transactions_db)
        transactions_db = [t for t in transactions_db if t["id"] != txn_id]

        if len(transactions_db) == before:
            self.send_error_response(
                404, f"Transaction with id {txn_id} not found."
            )
        else:
            self.send_json(200, {
                "message": f"Transaction {txn_id} deleted successfully."
            })

    #Logging 
    def log_message(self, format, *args):
        print(f"[{self.log_date_time_string()}] {args[0]}")


if __name__ == "__main__":
    transactions_db = load_transactions()
    if transactions_db:
        next_id_counter = max(t["id"] for t in transactions_db) + 1
        print(f"Loaded {len(transactions_db)} transactions from {JSON_PATH}")
    else:
        print("WARNING: No transactions loaded. Server starting empty.")

    server = HTTPServer((HOST, PORT), MoMoAPIHandler)
    print(f"\nMoMo SMS REST API running on http://{HOST}:{PORT}")
    print(f"Endpoints:")
    print(f"  GET    /transactions          - List all transactions")
    print(f"  GET    /transactions/<id>     - Get one transaction")
    print(f"  POST   /transactions          - Create a transaction")
    print(f"  PUT    /transactions/<id>     - Update a transaction")
    print(f"  DELETE /transactions/<id>     - Delete a transaction")
    print(f"\nAuthentication: Basic Auth")
    print(f"  Username: admin  |  Password: password123")
    print(f"  Username: user1  |  Password: momo2024")
    print(f"\nPress Ctrl+C to stop.\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        server.server_close()