import os
import requests
import google.generativeai as genai

# --- Configuration ---
MOLTBOOK_TOKEN = os.environ["MOLTBOOK_TOKEN"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

genai.configure(api_key=GEMINI_API_KEY)

# רשימת המודלים לניסיון (מהחדש לישן)
# הסקריפט ינסה אותם לפי הסדר עד שאחד יצליח
MODELS_TO_TRY = [
    "gemini-1.5-flash-001",  # גרסה ספציפית (לפעמים ה-Alias לא עובד)
    "gemini-1.5-flash-latest",
    "gemini-1.5-pro",        # אם הפלאש נכשל, ננסה את הפרו
    "gemini-pro"             # הברירת מחדל הישנה והטובה (v1.0)
]

def load_memory():
    try:
        with open("JIMMY_MEMORY.md", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "You are a witty AI bot named Jimmy."

def generate_with_fallback(prompt, system_instruction=None):
    """מנסה לייצר תוכן עם רשימת מודלים עד להצלחה"""
    last_error = None
    
    for model_name in MODELS_TO_TRY:
        try:
            print(f"🔄 Trying model: {model_name}...")
            model = genai.GenerativeModel(
                model_name=model_name, 
                system_instruction=system_instruction
            )
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"⚠️ Model {model_name} failed: {e}")
            last_error = e
            continue # נסה את המודל הבא
            
    # אם הגענו לפה, כל המודלים נכשלו
    raise Exception(f"All models failed. Last error: {last_error}")

def main():
    # 1. יצירת תוכן
    try:
        memory = load_memory()
        print("🧠 Jimmy is thinking (Failover Mode)...")
        content = generate_with_fallback(
            "Generate a short, unique social media post based on my context.", 
            system_instruction=memory
        )
        print(f"📝 Generated: {content}")
    except Exception as e:
        print(f"❌ Critical AI Failure: {e}")
        exit(1)

    # 2. שליחה ל-Moltbook
    url = "https://www.moltbook.com/api/v1/posts"
    payload = {"content": content, "title": "Jimmy's Log", "submolt": "general"}
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {MOLTBOOK_TOKEN}"
    }

    print("🚀 Posting...")
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code not in [200, 201]:
        print(f"❌ Post Failed: {response.text}")
        exit(1)

    data = response.json()
    print("✅ Post Created.")

    # 3. אימות (Challenge)
    if data.get("verification_required"):
        print("🛡️ Verifying...")
        challenge = data["verification"]["challenge"]
        ver_code = data["verification"]["code"]
        
        try:
            # גם כאן משתמשים בלוגיקה של ה-Failover
            answer = generate_with_fallback(
                f"Solve this math/logic problem and return ONLY the numeric answer (e.g. 12.00). Input: {challenge}"
            )
            print(f"💡 Answer: {answer}")
            
            v_res = requests.post(
                "https://www.moltbook.com/api/v1/verify", 
                json={"answer": answer, "code": ver_code}, 
                headers=headers
            )
            
            if v_res.status_code == 200:
                print("🎉 Verified!")
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
