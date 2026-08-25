import json
import urllib.error
import urllib.request

url = "http://127.0.0.1:8000/triage"
payload = {"text": "My payment failed."}
data = json.dumps(payload).encode("utf-8")

req = urllib.request.Request(
    url, data=data, headers={"Content-Type": "application/json"}
)

try:
    response = urllib.request.urlopen(req)
    print("SUCCESS (HTTP 200):")
    print(response.read().decode("utf-8"))
except urllib.error.HTTPError as e:
    print(f"HTTP STATUS CODE: {e.code}")
    print("ERROR BODY:")
    print(e.read().decode("utf-8"))