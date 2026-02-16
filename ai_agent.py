import os
import json
import requests
import time

# --- קונפיגורציה ---
MOLTBOOK_TOKEN = os.environ["MOLTBOOK_TOKEN"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

# אנחנו משתמשים בכתובת הישירה של ה-API. זה עוקף את כל הבעיות של הספרייה.
# מודל 1.5 פלאש הוא היציב ביותר כרגע בגישה הזו.
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

def load_memory():
    try:
        with open("JIMMY_MEMORY.md", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "You are a witty AI bot named Jimmy."

def ask_gemini_direct(prompt, system_context=""):
    """
    פונקציה ששולחת בקשת HTTP ישירה לגוגל.
    בלי ספריות, בלי חוכמות, בלי שגיאות גרסה.
    """
    headers = {"Content-Type": "application/json"}
    
    # טריק: אנחנו מאחדים את ההנחיה (System) עם הבקשה (User) כדי למנוע סיבוכים במבנה ה-JSON
    full_prompt = f"{system_context}\n\n---\nTASK: {prompt}"
    
    payload = {
        "contents": [{
            "parts": [{"text": full_prompt}]
        }]
    }

    try:
        print(f"📡 Calling Gemini API directly...")
        response = requests.post(GEMINI_URL, headers=headers, json=payload, timeout=30)
        
        if response.status_code != 200:
            print(f"⚠️ API Error ({response.status_code}): {response.text}")
            raise Exception(f"Gemini API returned {response.status_code}")

        # פיענוח התשובה
        result = response.json()
        text_content = result['candidates'][0]['content']['parts'][0]['text']
        return text_content.strip()

    except Exception as e:
        print(f"❌ REST API Failed: {e}")
        raise e

def main():
    # 1. יצירת תוכן
    try:
        memory = load_memory()
        print("🧠 Jimmy is thinking (REST Mode)...")
        content = ask_gemini_direct(
            "Generate a short, unique social media post based on my context.", 
            system_context=memory
        )
        print(f"📝 Generated: {content}")
    except Exception as e:
        print("❌ Critical Failure in Generation via REST.")
        exit(1)

    # 2. שליחה ל-Moltbook
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

    # 3. אימות (Challenge)
    if data.get("verification_required"):
        print("🛡️ Verifying logic...")
        challenge = data["verification"]["challenge"]
        ver_code = data["verification"]["code"]
        
        try:
            # שימוש באותה פונקציית REST לפתרון החידה
            answer = ask_gemini_direct(
                f"Solve this math/logic problem and return ONLY the numeric answer (e.g. 12.00). Input: {challenge}",
                system_context="You are a precise calculator."
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
