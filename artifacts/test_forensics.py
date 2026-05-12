import requests
import json

def test_report_generation():
    url = "http://localhost:8000/api/v1/ads-protection/generate-investigation-report"
    # Note: We need a valid session or bypass auth if testing inside container
    # Since I'm testing via docker exec, I'll assume the API is reachable or use a local bypass if needed.
    # But wait, the API has auth. 
    # I'll use a simpler way: check the service logs and see if the last request succeeded.
    
    # Actually, I'll run a python script INSIDE the container that calls the service directly.
    pass

if __name__ == "__main__":
    print("Starting forensic report verification...")
    # I'll use docker exec to run a small python snippet that calls the service method.
