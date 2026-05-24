import os
import sys
import time
import json
import requests
from playwright.sync_api import sync_playwright

# --- FOOLPROOF CONFIG IMPORT ---
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)
sys.path.insert(0, os.getcwd())

try:
    from config import GROQ_API_KEY
except ImportError:
    GROQ_API_KEY = ""

# --- CONFIGURATION ---
SESSION_DIR = os.path.join(os.getcwd(), ".whatsapp_session")
DRAFTS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "copilot_drafts.json")
CHECK_INTERVAL_SECONDS = 600 # Checks every 10 minutes

def send_mac_notification(title, text):
    """Triggers a native macOS notification banner with a sound!"""
    os.system(f"""osascript -e 'display notification "{text}" with title "{title}" sound name "Glass"'""")

def scan_and_draft():
    mentions_found = []
    
    with sync_playwright() as p:
        # headless=True makes the browser completely invisible!
        browser = p.chromium.launch_persistent_context(
            user_data_dir=SESSION_DIR,
            headless=True, 
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        page = browser.new_page()
        page.goto("https://web.whatsapp.com", wait_until="domcontentloaded")
        
        try:
            page.wait_for_selector('div[id="pane-side"]', timeout=45000)
            page.wait_for_timeout(3000)
            
            badges = page.locator('div#pane-side span[aria-label*="unread" i]')
            count = badges.count()
            
            for i in range(min(count, 15)): # Cap at 15 to keep background processing light
                badge = badges.nth(i)
                visible_text = badge.inner_text().strip().lower()
                if "unread" in visible_text:
                    continue
                    
                row_text = badge.evaluate("""el => { 
                    let p = el; 
                    for(let j=0; j<7; j++) { if(p.parentElement) p = p.parentElement; } 
                    return p.innerText || ''; 
                }""")
                
                chat_name = row_text.split('\n')[0].strip() if row_text else ""
                
                if "Archived" in row_text or chat_name == "Archived":
                    continue
                    
                badge.click(force=True)
                page.wait_for_selector('div#main header', timeout=5000)
                page.wait_for_timeout(1000)
                
                message_rows = page.locator('div#main div[role="row"]')
                msg_count = message_rows.count()
                
                chat_context = []
                darshan_mentioned = False
                
                for j in range(max(0, msg_count - 5), msg_count):
                    raw_text = message_rows.nth(j).inner_text().strip()
                    if raw_text:
                        clean_msg = " | ".join(raw_text.split('\n'))
                        chat_context.append(clean_msg)
                        if "@darshan" in clean_msg.lower():
                            darshan_mentioned = True
                
                if darshan_mentioned:
                    mentions_found.append({
                        "group": chat_name,
                        "context": chat_context
                    })
                
                page.keyboard.press("Escape")
                page.wait_for_timeout(1000)
                break # Resync DOM
                
        except Exception as e:
            print(f"Background Error: {e}")
        finally:
            browser.close()
            
    return mentions_found

def run_daemon():
    print("👻 Co-Pilot Daemon is now running invisibly in the background.")
    send_mac_notification("Co-Pilot Active", "Watching your WhatsApp groups for @Darshan mentions.")
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    
    while True:
        print(f"[{time.strftime('%I:%M %p')}] Scanning for mentions...")
        mentions = scan_and_draft()
        
        if mentions:
            # Load existing drafts so we don't overwrite them
            drafts = []
            if os.path.exists(DRAFTS_FILE):
                try:
                    with open(DRAFTS_FILE, "r") as f:
                        drafts = json.load(f)
                except:
                    pass

            new_drafts_count = 0
            
            for item in mentions:
                # Check if we already drafted this one today
                if any(d["group"] == item["group"] for d in drafts):
                    continue 

                context_str = "\n".join(item["context"])
                prompt = f"""You are Darshan Sheregar, a professional Client Success Manager.
                Draft a polite, concise, 1-2 sentence reply addressing this mention in group '{item["group"]}'.
                Context: {context_str}
                Output ONLY the text to send."""
                
                try:
                    response = requests.post(url, headers=headers, json={"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": prompt}]}, timeout=30)
                    if response.status_code == 200:
                        draft_text = response.json()['choices'][0]['message']['content'].strip(' "')
                        drafts.append({"group": item["group"], "draft": draft_text})
                        new_drafts_count += 1
                except:
                    continue
            
            if new_drafts_count > 0:
                with open(DRAFTS_FILE, "w") as f:
                    json.dump(drafts, f, indent=4)
                
                # TRIGGER THE MAC NOTIFICATION!
                send_mac_notification("AI Co-Pilot Alert", f"Drafted {new_drafts_count} new replies! Open CS Command Center to approve.")
                print(f"🚨 Drafted {new_drafts_count} new replies. Sent Mac Notification.")

        print(f"💤 Sleeping for {CHECK_INTERVAL_SECONDS // 60} minutes...")
        time.sleep(CHECK_INTERVAL_SECONDS)

if __name__ == "__main__":
    run_daemon()