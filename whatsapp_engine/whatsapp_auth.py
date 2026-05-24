import os
from playwright.sync_api import sync_playwright

SESSION_DIR = os.path.join(os.getcwd(), ".whatsapp_session")

def setup_whatsapp_session():
    with sync_playwright() as p:
        print("🚀 Launching Playwright in persistent mode...")
        
        browser = p.chromium.launch_persistent_context(
            user_data_dir=SESSION_DIR,
            headless=False,
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        page = browser.new_page()
        print("🌐 Loading WhatsApp Web...")
        
        try:
            # wait_until="domcontentloaded" prevents the script from waiting for infinite network requests
            page.goto("https://web.whatsapp.com", wait_until="domcontentloaded", timeout=120000)
        except Exception as e:
            print(f"⚠️ Warning during page load (ignorable if the QR code appears): {e}")
        
        print("📱 Please scan the QR code with your phone.")
        print("⏳ Waiting for WhatsApp to sync (this can take up to 2 minutes)...")
        
        try:
            # We wait for the main chat list container (pane-side) to appear
            page.wait_for_selector('div[id="pane-side"]', timeout=120000)
            print("✅ Successfully logged in and synced to WhatsApp Web!")
            
            # Let it sit for 5 seconds to ensure all local storage saves properly
            page.wait_for_timeout(5000)
            
        except Exception as e:
            print("❌ Authentication failed.")
            print(f"\nTechnical Error: {e}")
            
        finally:
            print("🔒 Closing browser and saving session state.")
            browser.close()

if __name__ == "__main__":
    setup_whatsapp_session()