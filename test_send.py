import httpx
import time

def send_tests():
    print("Sending requests...")
    # Send a simple GET
    httpx.get("http://127.0.0.1:8080/api/ping?source=testing")
    
    # Send a POST with JSON
    httpx.post("http://127.0.0.1:8080/stripe/webhook", json={"type": "payment_intent.succeeded", "data": {"object": {"id": "pi_123", "amount": 1000}}})
    
    # Send a PUT with headers
    httpx.put("http://127.0.0.1:8080/update_user", headers={"Authorization": "Bearer token123"}, content="Raw text update data")
    
    print("Requests sent.")

if __name__ == "__main__":
    send_tests()
