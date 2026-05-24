import os
import sys
import time
import json
from playwright.sync_api import sync_playwright

# --- CONFIGURATION ---
SESSION_DIR = os.path.join(os.getcwd(), ".whatsapp_session")
PAYLOAD_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "broadcast_payload.json")

def broadcast_message(groups, message):
    results = {"success": [], "failed": []}

    with sync_playwright() as p:
        print("🚀 Launching WhatsApp Broadcaster...")
        browser = p.chromium.launch_persistent_context(
            user_data_dir=SESSION_DIR,
            headless=False, 
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        page = browser.new_page()
        page.goto("https://web.whatsapp.com", wait_until="domcontentloaded")
        
        print("⏳ Waiting for WhatsApp to load...")
        page.wait_for_selector('div[id="pane-side"]', timeout=60000)
        print("✅ WhatsApp loaded! Starting broadcast...\n")
        page.wait_for_timeout(2000)

        for group_name in groups:
            group_name = group_name.strip()
            if not group_name: continue
            
            print(f"🔍 Searching for: '{group_name}'...")
            try:
                # 1. Search Bar
                search_box = page.locator('div#side').get_by_role("textbox")
                search_box.click(force=True)
                page.keyboard.press("Meta+A") 
                page.keyboard.press("Backspace")
                
                # 2. Type Name
                search_box.press_sequentially(group_name, delay=50)
                page.wait_for_timeout(2000)
                
                # 3. Click Group
                group_button = page.locator(f'span[title="{group_name}"]').first
                if group_button.count() == 0:
                    print(f"⚠️ Could not find group '{group_name}'. Skipping.")
                    results["failed"].append(group_name)
                    continue
                    
                group_button.click(force=True)
                
                # 4. Wait for Chat
                page.wait_for_selector('div#main header', timeout=5000)
                page.wait_for_timeout(1000)
                
                # 5. Message Box
                chat_box = page.locator('div#main').get_by_role("textbox")
                chat_box.click(force=True)
                
                # 6. Type & Send
                print(f"✍️ Typing message to '{group_name}'...")
                chat_box.fill(message)
                page.wait_for_timeout(1000)
                
                print(f"📤 Sending to '{group_name}'...")
                page.keyboard.press("Enter")
                page.wait_for_timeout(1500)
                
                print(f"✅ Success: Sent to '{group_name}'!\n")
                results["success"].append(group_name)
                
            except Exception as e:
                print(f"❌ Error sending to '{group_name}': {e}\n")
                results["failed"].append(group_name)
                
            finally:
                page.keyboard.press("Escape")
                page.wait_for_timeout(500)
                page.keyboard.press("Escape")
                page.wait_for_timeout(1000)

        print("🎉 Broadcast Complete!")
        print(f"📊 Summary: {len(results['success'])} Sent | {len(results['failed'])} Failed")
        browser.close()

if __name__ == "__main__":
    if not os.path.exists(PAYLOAD_FILE):
        print("❌ Error: No payload file found.")
        sys.exit(1)
        
    with open(PAYLOAD_FILE, "r") as f:
        data = json.load(f)
        
    broadcast_message(data["groups"], data["message"])
    
    # Clean up the payload file after running
    os.remove(PAYLOAD_FILE)