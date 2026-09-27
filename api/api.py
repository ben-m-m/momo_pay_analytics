import json 
import re 
import pathlib
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import base64
 
ROOT = pathlib.Path(__file__).resolve().parent
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