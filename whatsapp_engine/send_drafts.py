import os
import sys
import json
from playwright.sync_api import sync_playwright

SESSION_DIR = os.path.join(os.getcwd(), ".whatsapp_session")
DRAFTS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "copilot_drafts.json")

def send_approved_drafts():
    if not os.path.exists(DRAFTS_FILE):
        print("❌ No drafts found to send!")
        return

    with open(DRAFTS_FILE, "r") as f:
        drafts = json.load(f)

    if not drafts:
        print("🎉 No drafts pending.")
        return

    with sync_playwright() as p:
        print("🚀 Launching Co-Pilot Auto-Sender...")
        browser = p.chromium.launch_persistent_context(
            user_data_dir=SESSION_DIR,
            headless=False,
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        page = browser.new_page()
        page.goto("https://web.whatsapp.com", wait_until="domcontentloaded")
        page.wait_for_selector('div[id="pane-side"]', timeout=60000)
        page.wait_for_timeout(2000)

        for item in drafts:
            group_name = item["group"]
            message = item["draft"]
            
            print(f"🔍 Searching for: '{group_name}'...")
            try:
                search_box = page.locator('div#side').get_by_role("textbox")
                search_box.click(force=True)
                page.keyboard.press("Meta+A")
                page.keyboard.press("Backspace")
                
                search_box.press_sequentially(group_name, delay=50)
                page.wait_for_timeout(2000)
                
                group_button = page.locator(f'span[title="{group_name}"]').first
                if group_button.count() == 0:
                    print(f"⚠️ Could not find group '{group_name}'. Skipping.")
                    continue
                    
                group_button.click(force=True)
                page.wait_for_selector('div#main header', timeout=5000)
                page.wait_for_timeout(1000)
                
                chat_box = page.locator('div#main').get_by_role("textbox")
                chat_box.click(force=True)
                
                print(f"✍️ Typing drafted reply to '{group_name}'...")
                chat_box.fill(message)
                page.wait_for_timeout(1000)
                
                print(f"📤 Sending...")
                page.keyboard.press("Enter")
                page.wait_for_timeout(1500)
                
                print(f"✅ Success: Sent reply to '{group_name}'!\n")
                
            except Exception as e:
                print(f"❌ Error sending to '{group_name}': {e}\n")
            finally:
                page.keyboard.press("Escape")
                page.wait_for_timeout(500)
                page.keyboard.press("Escape")
                page.wait_for_timeout(1000)

        browser.close()
        
    # Clean up the drafts file so they don't get sent twice!
    os.remove(DRAFTS_FILE)
    print("🎉 All approved drafts have been sent and cleared!")

if __name__ == "__main__":
    send_approved_drafts()