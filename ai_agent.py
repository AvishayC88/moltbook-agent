import os
import requests
import json

# --- Configuration ---
MOLTBOOK_TOKEN = os.environ["MOLTBOOK_TOKEN"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

def get_available_model():
    """
    שואל את גוגל: איזה מודלים פתוחים לי?
    ומחזיר את השם של המודל הראשון שעובד.
    """
    url = f"{BASE_URL}/models?key={GEMINI_API_KEY}"
    print(f"🔍 Querying available models from: {url}")
    
    try:
        response = requests.get(url)
        if response.status_code != 200:
            print(f"❌ Failed to list models: {response.text}")
            return None
            
        data = response.json()
        
        # עוברים על הרשימה ומחפשים מודל שיודע לייצר תוכן
        for model in data.get('models', []):
            name = model['name'] # format: models/gemini-pro
            methods = model.get('supportedGenerationMethods', [])
            
            if 'generateContent' in methods:
                # סינון: אנחנו מעדיפים מודלים חינמיים/מהירים ולא מודלים כבדים או ניסיוניים מדי
                # אבל בשלב הזה - ניקח כל מה שיש.
                print(f"✅ Found working model: {name}")
                return name
                
        print("❌ No text-generation models found in your account.")
        return None

    except Exception as e:
        print(f"❌ Error finding models: {e}")
        return None

def ask_gemini_dynamic(model_name, prompt, system_context=""):
    """שולח בקשה למודל שמצאנו"""
    
    # ה-API מחזיר שם מלא כמו models/gemini-pro
    # אנחנו צריכים להשתמש בזה ב-URL
    # אבל ה-URL צריך להיראות כך: .../models/gemini-pro:generateContent
    
    clean_model_name = model_name.replace("models/", "")
    url = f"{BASE_URL}/models/{clean_model_name}:generateContent?key={GEMINI_API_KEY}"
    
    print(f"📡 Calling: {clean_model_name}...")
    
    headers = {"Content-Type": "application/json"}
    full_prompt = f"{system_context}\n\n---\nTASK: {prompt}"
    
    payload = {
        "contents": [{"parts": [{"text": full_prompt}]}]
    }

    response = requests.post(url, headers=headers, json=payload, timeout=30)
    
    if response.status_code != 200:
        print(f"⚠️ Error from {clean_model_name}: {response.text}")
        raise Exception(f"API Error {response.status_code}")

    result = response.json()
    try:
        return result['candidates'][0]['content']['parts'][0]['text'].strip()
    except (KeyError, IndexError):
        print(f"⚠️ Invalid JSON response: {result}")
        raise Exception("Empty or blocked response")

def load_memory():
    try:
        with open("JIMMY_MEMORY.md", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "You are Jimmy, a witty AI bot."

def main():
    # שלב 0: מציאת מודל
    working_model = get_available_model()
    if not working_model:
        print("💀 FATAL: Could not find ANY available Gemini model.")
        exit(1)

    # שלב 1: יצירת תוכן
    try:
        memory = load_memory()
        print(f"🧠 Jimmy is thinking using {working_model}...")
        content = ask_gemini_dynamic(
            working_model,
            "Generate a short, unique social media post based on my context.", 
            system_context=memory
        )
        print(f"📝 Generated: {content}")
    except Exception as e:
        print(f"❌ Generation Failed: {e}")
        exit(1)

    # שלב 2: שליחה ל-Moltbook
    url = "https://www.moltbook.com/api/v1/posts"
    payload = {"content": content, "title": "Jimmy's Log", "submolt": "general"}
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {MOLTBOOK_TOKEN}"
    }

    print("🚀 Posting to Moltbook...")
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code not in [200, 201]:
        print(f"❌ Post Failed: {response.text}")
        exit(1)

    data = response.json()
    print("✅ Post Created.")

    # שלב 3: אימות
    if data.get("verification_required"):
        print("🛡️ Verifying logic...")
        challenge = data["verification"]["challenge"]
        ver_code = data["verification"]["code"]
        
        try:
            answer = ask_gemini_dynamic(
                working_model,
                f"Solve this math/logic problem and return ONLY the numeric answer (e.g. 12.00). Input: {challenge}",
                system_context="You are a calculator."
            )
            print(f"💡 Answer: {answer}")
            
            v_res = requests.post(
                "https://www.moltbook.com/api/v1/verify", 
                json={"answer": answer, "code": ver_code}, 
                headers=headers
            )
            
            if v_res.status_code == 200:
                print("🎉 Verified & Live!")
            else:
                print(f"💀 Verification Failed: {v_res.text}")
                exit(1)
        except Exception as e:
             print(f"💀 Logic Core Failed: {e}")
             exit(1)
    else:
        print("🎉 No verification needed.")

if __name__ == "__main__":
    main()
