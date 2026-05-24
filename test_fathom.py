import requests
import config

def test_api():
    print("--------------------------------------------------")
    print("🔍 TESTING FATHOM API CONNECTION...")
    print("--------------------------------------------------")
    
    # Check if key exists
    api_key = getattr(config, "FATHOM_API_KEY", None)
    if not api_key:
        print("❌ ERROR: FATHOM_API_KEY is missing from your config.py file.")
        return

    headers = {"X-Api-Key": api_key}
    
    # TEST 1: Can we connect and get your meetings?
    print("📡 1. Fetching recent meetings...")
    url = "https://api.fathom.ai/external/v1/meetings"
    
    try:
        response = requests.get(url, headers=headers)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 401 or response.status_code == 403:
            print("   ❌ ERROR: Unauthorized! Your API Key is invalid or expired.")
            print(f"   Raw Response: {response.text}")
            return
            
        response.raise_for_status()
        data = response.json()
        meetings = data.get("items", [])
        
        print(f"   ✅ SUCCESS: Found {len(meetings)} meetings in your account.")
        
        if not meetings:
            print("   ⚠️ No meetings found. Have you recorded a call on Fathom yet?")
            return
            
        last_meeting = meetings[0]
        recording_id = last_meeting.get("recording_id")
        title = last_meeting.get("meeting_title", "Untitled")
        print(f"   🎙️ Most recent meeting: '{title}' (ID: {recording_id})")
        
        # TEST 2: Can we fetch the transcript?
        print("\n📡 2. Fetching transcript for the most recent meeting...")
        t_url = f"https://api.fathom.ai/external/v1/recordings/{recording_id}/transcript"
        t_response = requests.get(t_url, headers=headers)
        print(f"   Status Code: {t_response.status_code}")
        
        if t_response.status_code == 200:
            transcript_data = t_response.json().get("transcript", [])
            print(f"   ✅ SUCCESS: Downloaded transcript with {len(transcript_data)} lines of dialogue.")
            print("\n   --- SNEAK PEEK ---")
            for line in transcript_data[:3]:
                speaker = line.get("speaker", {}).get("display_name", "Unknown")
                text = line.get("text", "")
                print(f"   🗣️ {speaker}: {text}")
        else:
            print(f"   ❌ ERROR getting transcript: {t_response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ NETWORK ERROR: {str(e)}")

if __name__ == "__main__":
    test_api()