import os
import sys
import requests
from playwright.sync_api import sync_playwright

# --- FOOLPROOF CONFIG IMPORT ---
# Get the absolute path of your main folder and force it into Python's brain
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

def get_unread_messages():
    unread_data = {}
    processed_chats = set()

    with sync_playwright() as p:
        print("🚀 Launching WhatsApp Engine (Morning Digest)...")
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
                    
                    chat_messages = []
                    start_index = max(0, msg_count - 5)
                    
                    for j in range(start_index, msg_count):
                        raw_text = message_rows.nth(j).inner_text().strip()
                        if raw_text:
                            clean_msg = " | ".join(raw_text.split('\n'))
                            chat_messages.append(clean_msg)
                    
                    unread_data[actual_chat_name] = chat_messages
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
    return unread_data

def generate_ai_dashboard(raw_data):
    if not raw_data:
        return "🎉 Inbox Zero! No unread messages to analyze."
        
    prompt_data = ""
    for chat, messages in raw_data.items():
        prompt_data += f"\n--- CHAT: {chat} ---\n"
        for msg in messages:
            prompt_data += f"- {msg}\n"
            
    prompt = f"""
    Darshan manages SME clients across WhatsApp groups. 
    Analyze the following unread WhatsApp messages and categorize them into a Morning Digest Dashboard.

    Priorities to sort by:
    🔴 URGENT: Requires immediate action from Darshan (e.g., explicit mentions of "@Darshan", escalations, blocked workflows, angry clients, or urgent questions).
    🟡 PENDING/FYI: Important context, ongoing discussions, feature requests, or technical issues being handled by others but Darshan should be aware.
    🟢 IGNORE/RESOLVED: Thank yous, "okays", internal team chatter not requiring Darshan's input, generic bot messages, or resolved queries.

    Raw Data:
    {prompt_data}

    Format your response cleanly. 
    Use the Emojis for headers. 
    For URGENT and PENDING items, provide a crisp 1-2 sentence summary of what is happening and what Darshan's recommended action is.
    """
    
    # --- GROQ REST API CALL (Ultra-Fast Llama-3.3 70B) ---
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.3-70b-versatile", # Updated to current flagship model
        "messages": [
            {"role": "system", "content": "You are an elite Client Success AI Assistant for Darshan Sheregar."},
            {"role": "user", "content": prompt}
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        # Explicit error logging: If Groq rejects it, print exactly WHY
        if response.status_code != 200:
            return f"❌ Groq API Error ({response.status_code}): {response.text}"
            
        data = response.json()
        return data['choices'][0]['message']['content']
        
    except Exception as e:
        return f"❌ Groq Execution Error: {e}"

if __name__ == "__main__":
    data = get_unread_messages()
    report = generate_ai_dashboard(data)
    print(report)