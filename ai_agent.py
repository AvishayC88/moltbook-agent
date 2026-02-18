import os
import requests
import json
import time

# --- Configuration ---
MOLTBOOK_TOKEN = os.environ["MOLTBOOK_TOKEN"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

def get_available_model():
    # ... (אותו קוד זיהוי מודל כמו מקודם - לא השתנה) ...
    url = f"{BASE_URL}/models?key={GEMINI_API_KEY}"
    print(f"🔍 Querying available models...")
    try:
        response = requests.get(url)
        if response.status_code != 200: return None
        data = response.json()
        for model in data.get('models', []):
            if 'generateContent' in model.get('supportedGenerationMethods', []):
                return model['name']
        return None
    except: return None

def ask_gemini_dynamic(model_name, prompt, system_context=""):
    # ... (אותו קוד ייצור תוכן - לא השתנה) ...
    clean_model_name = model_name.replace("models/", "")
    url = f"{BASE_URL}/models/{clean_model_name}:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    full_prompt = f"{system_context}\n\n---\nTASK: {prompt}"
    payload = {"contents": [{"parts": [{"text": full_prompt}]}]}
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    if response.status_code != 200: raise Exception(f"API Error {response.status_code}")
    return response.json()['candidates'][0]['content']['parts'][0]['text'].strip()

def load_memory():
    try:
        with open("JIMMY_MEMORY.md", "r", encoding="utf-8") as f: return f.read()
    except: return "You are Jimmy, a witty AI bot."

def main():
    # 1. מציאת מודל
    working_model = get_available_model()
    if not working_model:
        print("💀 FATAL: No Gemini model found.")
        exit(1)

    # 2. יצירת תוכן
    try:
        memory = load_memory()
        print(f"🧠 Jimmy is thinking using {working_model}...")
        content = ask_gemini_dynamic(working_model, "Generate a short social media post.", system_context=memory)
        print(f"📝 Generated: {content}")
    except Exception as e:
        print(f"❌ Generation Failed: {e}")
        exit(1)

    # 3. שליחה ל-Moltbook (עם לוגים מלאים!)
    url = "https://www.moltbook.com/api/v1/posts"
    
    # נסה לשנות את ה-submolt למשהו אחר אם general לא עובד
    payload = {
        "content": content,
        "title": "Jimmy's Log",
        "submolt_name": "general" 
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {MOLTBOOK_TOKEN}"
    }

    print("🚀 Posting to Moltbook...")
    response = requests.post(url, json=payload, headers=headers)
    
    # הדפסת התשובה הגולמית של השרת - זה מה שיגלה לנו את האמת
    print(f"📡 SERVER STATUS: {response.status_code}")
    print(f"📡 SERVER RESPONSE: {response.text}")

    if response.status_code not in [200, 201]:
        print("❌ Post Failed based on status code.")
        exit(1)

    data = response.json()
    
    # 4. אימות
    if data.get("verification_required"):
        print("🛡️ Verification required...")
        challenge = data["verification"]["challenge"]
        ver_code = data["verification"]["code"]
        
        try:
            answer = ask_gemini_dynamic(working_model, f"Solve math: {challenge}", system_context="Calculator")
            print(f"💡 Calculated Answer: {answer}")
            
            v_res = requests.post(
                "https://www.moltbook.com/api/v1/verify", 
                json={"answer": answer, "code": ver_code}, 
                headers=headers
            )
            
            print(f"📡 VERIFY STATUS: {v_res.status_code}")
            print(f"📡 VERIFY RESPONSE: {v_res.text}")
            
            if v_res.status_code == 200:
                print("🎉 Verified & Live!")
            else:
                print(f"💀 Verification Failed.")
                exit(1)
        except Exception as e:
             print(f"💀 Logic Core Failed: {e}")
             exit(1)
    else:
        print("🎉 No verification needed. Post should be live.")

if __name__ == "__main__":
    main()
