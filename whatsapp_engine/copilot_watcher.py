import os
import sys
import json
import requests
from playwright.sync_api import sync_playwright

# --- FOOLPROOF CONFIG IMPORT ---
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)
sys.path.insert(0, os.getcwd())

try:
    from config import GROQ_API_KEY
    print("✅ Successfully loaded Groq API Key from config.py!")
except ImportError as e:
    print(f"⚠️ Could not find config.py. Error details: {e}")
    GROQ_API_KEY = ""

# --- CONFIGURATION ---
SESSION_DIR = os.path.join(os.getcwd(), ".whatsapp_session")
DRAFTS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "copilot_drafts.json")

def get_mentions():
    mentions_found = []
    processed_chats = set()

    with sync_playwright() as p:
        print("🚀 Launching Co-Pilot Scanner...")
        browser = p.chromium.launch_persistent_context(
            user_data_dir=SESSION_DIR,
            headless=False, 
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        page = browser.new_page()
        page.goto("https://web.whatsapp.com", wait_until="domcontentloaded")
        page.wait_for_selector('div[id="pane-side"]', timeout=60000)
        page.wait_for_timeout(3000)

        max_chats_to_process = 20
        
        for _ in range(max_chats_to_process):
            badges = page.locator('div#pane-side span[aria-label*="unread" i]')
            count = badges.count()
            
            if count == 0:
                break
                
            clicked_something = False
            
            for i in range(count):
                try:
                    badge = badges.nth(i)
                    
                    visible_text = badge.inner_text().strip().lower()
                    if "unread" in visible_text:
                        continue
                        
                    row_text = badge.evaluate("""el => { 
                        let p = el; 
                        for(let j=0; j<7; j++) { if(p.parentElement) p = p.parentElement; } 
                        return p.innerText || ''; 
                    }""")
                    
                    chat_name = row_text.split('\n')[0].strip() if row_text else f"Unknown_{i}"
                    
                    if "Archived" in row_text or chat_name == "Archived" or chat_name in processed_chats:
                        continue
                        
                    badge.click(force=True)
                    clicked_something = True
                    
                    page.wait_for_selector('div#main header', timeout=5000)
                    page.wait_for_timeout(1000)
                    
                    header_text = page.locator('div#main header').inner_text()
                    actual_chat_name = header_text.split('\n')[0].strip() if header_text else chat_name
                    
                    processed_chats.add(chat_name) 
                    processed_chats.add(actual_chat_name) 
                    
                    message_rows = page.locator('div#main div[role="row"]')
                    msg_count = message_rows.count()
                    
                    chat_context = []
                    start_index = max(0, msg_count - 5)
                    darshan_mentioned = False
                    
                    for j in range(start_index, msg_count):
                        raw_text = message_rows.nth(j).inner_text().strip()
                        if raw_text:
                            clean_msg = " | ".join(raw_text.split('\n'))
                            chat_context.append(clean_msg)
                            # Check if you were mentioned!
                            if "@darshan" in clean_msg.lower():
                                darshan_mentioned = True
                    
                    if darshan_mentioned:
                        print(f"🚨 Mention detected in: {actual_chat_name}!")
                        mentions_found.append({
                            "group": actual_chat_name,
                            "context": chat_context
                        })
                    else:
                        print(f"👀 Scanned {actual_chat_name} - No mentions found.")
                    
                    page.keyboard.press("Escape")
                    page.wait_for_timeout(1000)
                    break 
                    
                except Exception:
                    if 'chat_name' in locals():
                        processed_chats.add(chat_name)
                    break

            if not clicked_something:
                break

        browser.close()
    return mentions_found

def generate_drafts(mentions_data):
    if not mentions_data:
        print("🎉 Inbox Zero! No mentions found.")
        return []
        
    print("\n🧠 Sending context to Groq Llama-3.3 to draft replies...")
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    drafts = []
    
    for item in mentions_data:
        group_name = item["group"]
        context_str = "\n".join(item["context"])
        
        prompt = f"""
        You are Darshan Sheregar, a highly professional and helpful Client Success Manager.
        You have just been mentioned in a WhatsApp group named "{group_name}".
        
        Recent Chat Context:
        {context_str}
        
        Draft a polite, concise, and helpful reply to address the mention.
        - Speak in the first person ("I will look into this", "Let me check").
        - Keep it under 3 sentences.
        - DO NOT include placeholders. If you don't know the answer, say "I will check on this and get back to you shortly."
        - Output ONLY the exact message text to be sent, nothing else.
        """
        
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": "You are a professional Client Success Manager drafting direct WhatsApp replies."},
                {"role": "user", "content": prompt}
            ]
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            if response.status_code == 200:
                draft_text = response.json()['choices'][0]['message']['content'].strip()
                # Remove quotes if the AI wrapped it in quotes
                if draft_text.startswith('"') and draft_text.endswith('"'):
                    draft_text = draft_text[1:-1]
                    
                drafts.append({
                    "group": group_name,
                    "draft": draft_text,
                    "context": context_str
                })
                print(f"✅ Drafted reply for {group_name}")
            else:
                print(f"❌ Groq Error for {group_name}: {response.text}")
        except Exception as e:
            print(f"❌ Execution Error for {group_name}: {e}")
            
    # Save drafts to JSON so the UI can read them later
    with open(DRAFTS_FILE, "w") as f:
        json.dump(drafts, f, indent=4)
        
    return drafts

if __name__ == "__main__":
    mentions = get_mentions()
    drafts = generate_drafts(mentions)
    
    if drafts:
        print("\n" + "="*50)
        print("🤖 CO-PILOT DRAFTS GENERATED")
        print("="*50)
        for d in drafts:
            print(f"📍 Group: {d['group']}")
            print(f"✍️ Draft: {d['draft']}")
            print("-" * 50)