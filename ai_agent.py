import os
import requests
import json
import time

# --- Configuration ---
MOLTBOOK_TOKEN = os.environ["MOLTBOOK_TOKEN"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

def get_available_model():
    """מאתר אוטומטית את המודל הפתוח בחשבון"""
    url = f"{BASE_URL}/models?key={GEMINI_API_KEY}"
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
    """שולח בקשה למודל שנמצא"""
    clean_model_name = model_name.replace("models/", "")
    url = f"{BASE_URL}/models/{clean_model_name}:generateContent?key={GEMINI_API_KEY}"
    
    headers = {"Content-Type": "application/json"}
    # הנחיה קשוחה לפורמט התשובה
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
        content = ask_gemini_dynamic(
            working_model, 
            "Generate a short, unique social media post based on my context.", 
            system_context=memory
        )
        print(f"📝 Generated: {content}")
    except Exception as e:
        print(f"❌ Generation Failed: {e}")
        exit(1)

    # 3. שליחה ל-Moltbook
    url = "https://www.moltbook.com/api/v1/posts"
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
    
    if response.status_code not in [200, 201]:
        print(f"❌ Post Failed: {response.text}")
        exit(1)

    data = response.json()
    print("✅ Post Created (Status: Pending Verification).")

    # 4. חילוץ וטיפול באתגר (התיקון הגדול!)
    # אנחנו בודקים אם הסטטוס הוא PENDING ואם יש אובייקט VERIFICATION
    post_data = data.get("post", {})
    verification_data = post_data.get("verification", {})
    
    if post_data.get("verificationStatus") == "pending" and verification_data:
        print("🛡️ Verification required! Solving challenge...")
        
        challenge_text = verification_data["challenge_text"]
        verification_code = verification_data["verification_code"]
        
        print(f"🧩 Challenge: {challenge_text}")
        
        try:
            # אנחנו מבקשים מג'ימני לפתור ולהחזיר רק מספר עם 2 ספרות עשרוניות
            # הדוגמה בלוג שלך ביקשה במפורש: "with 2 decimal places, e.g., '525.00'"
            answer = ask_gemini_dynamic(
                working_model, 
                f"Solve this math problem. The text is obfuscated (e.g. 'TwEnTy'). Read carefully. Return ONLY the number formatted with 2 decimal places (e.g. 44.00). Input: {challenge_text}",
                system_context="You are a precise calculator. Output ONLY the number."
            )
            
            # ניקוי רעשים למקרה שהמודל החזיר טקסט נוסף
            answer = answer.replace("Answer:", "").strip()
            print(f"💡 Calculated Answer: {answer}")
            
            # שליחת האימות
            verify_url = "https://www.moltbook.com/api/v1/verify"
            verify_payload = {
                "answer": answer, 
                "verification_code": verification_code # שים לב: השם כאן הוא verification_code ולא code
            }
            
            v_res = requests.post(verify_url, json=verify_payload, headers=headers)
            
            if v_res.status_code == 200:
                print("🎉 SUCCESS! Post Verified & Live!")
                print(f"📡 Response: {v_res.text}")
            else:
                print(f"💀 Verification Failed: {v_res.text}")
                exit(1)
                
        except Exception as e:
             print(f"💀 Logic Core Failed: {e}")
             exit(1)
    else:
        print("🎉 No verification needed (or parsing failed).")

if __name__ == "__main__":
    main()
