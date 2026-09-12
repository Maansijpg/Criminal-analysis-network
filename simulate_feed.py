def main():
    print(f"Simulating a live CCTV feed every {INTERVAL_SECONDS}s. Ctrl+C to stop.")
    while True:
        try:
            res = requests.post(API_URL, json={})
            data = res.json()
            
            # Check if backend returned an error response
            if res.status_code != 200:
                print(f"[ERROR {res.status_code}]", data)
                time.sleep(INTERVAL_SECONDS)
                continue

            tag = "ALERT" if data.get("alert") else "sighting"
            
            # Use .get() or access nested sighting dictionary safely
            sighting = data.get("sighting", data)
            suspect = sighting.get("suspect_name", "Unknown Suspect")
            location = sighting.get("camera_location", "Unknown Location")
            confidence = sighting.get("confidence", "N/A")

            print(f"[{tag}] {suspect} @ {location} (confidence {confidence})")
        except requests.RequestException as e:
            print("Backend not reachable yet:", e)
        time.sleep(INTERVAL_SECONDS)