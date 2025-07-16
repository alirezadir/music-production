import requests

API_KEY = "your_lalal_ai_api_key"
AUDIO_FILE = "song.mp3"
STEM_TYPE = "vocals"  # or "drums", "bass", etc.

# Step 1: Upload
upload_response = requests.post(
    "https://api.lalal.ai/v1/upload",
    headers={"Authorization": f"Bearer {API_KEY}"},
    files={"file": open(AUDIO_FILE, "rb")}
)
file_id = upload_response.json()["id"]

# Step 2: Request stem separation
process_response = requests.post(
    "https://api.lalal.ai/v1/separate",
    headers={"Authorization": f"Bearer {API_KEY}"},
    json={"id": file_id, "stem": STEM_TYPE}
)

# Step 3: Download stem
stem_url = process_response.json()["stem_url"]
stem_data = requests.get(stem_url)
with open(f"{STEM_TYPE}.wav", "wb") as f:
    f.write(stem_data.content)