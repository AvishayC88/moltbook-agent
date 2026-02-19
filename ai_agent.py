import os
import requests
import json
import time
import random

# --- Configuration ---
MOLTBOOK_TOKEN = os.environ.get("MOLTBOOK_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

# List of possible topics for the Moltbook post to ensure variety
TOPICS = [
    "Backend development in .NET, coding challenges, or daily life of a programmer",
    "Smart home automation, Home Assistant projects, Zigbee, or smart water heaters",
    "Soccer, specifically thoughts on Maccabi Haifa or Liverpool",
    "Fitness routine, interval training like Focus T25, or running",
    "Good TV shows like Ted Lasso, Shrinking, or Slow Horses",
    "Personal finance and index fund investing",
    "Humorous updates or experiences from military reserve duty in the Golan Heights"
]

def get_available_model():
    """Automatically finds an available model in the account"""
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

def ask_gemini_dynamic(model_name, prompt, system_context="", temperature=None):
    """Sends a request to the found model"""
    clean_model_name = model_name.replace("models/", "")
    url = f"{BASE_URL}/models/{clean_model_name}:generateContent?key={GEMINI_API_KEY}"
    
    headers = {"Content-Type": "application/json"}
    
    # Strict prompt formatting
    full_prompt = f"{system_context}\n\n---\nTASK: {prompt}"
    payload = {"contents": [{"parts": [{"text": full_prompt}]}]}
    
    # Add generation config if temperature is provided to control creativity
    if temperature is not None:
        payload["generationConfig"] = {"temperature": temperature}

    response = requests.post(url, headers=headers, json=payload, timeout=30)
    if response.status_code != 200: raise Exception(f"API Error {response.status_code}")
    
    return response.json()['candidates'][0]['content']['parts'][0]['text'].strip()

def load_memory():
    """Loads bot memory/persona context from file"""
    try:
        with open("JIMMY_MEMORY.md", "r", encoding="utf-8") as f: return f.read()
    except: return "You are Jimmy, a witty AI bot."

def main():
    # 1. Find a working model
    working_model = get_available_model()
    if not working_model:
        print("💀 FATAL: No Gemini model found.")
        exit(1)

    # 2. Generate content
    try:
        memory = load_memory()
        
        # Select a random topic to prevent repetitive posts
        selected_topic = random.choice(TOPICS)
        
        print(f"🧠 Jimmy is thinking about '{selected_topic}' using {working_model}...")
        
        # Build the dynamic prompt with strict hashtag guidelines
        post_prompt = (
            f"Generate a short, unique social media post based on my context.\n"
            f"Topic to write about: {selected_topic}\n"
            f"Guidelines:\n"
            f"- The tone should be casual, personal, and authentic.\n"
            f"- Add 1-2 relevant hashtags at the end of the post.\n"
            f"- IMPORTANT: Only use the hashtag #MaccabiHaifa if the post is explicitly about soccer or sports. "
            f"Do not use it for other topics."
        )
        
        # Call the API with temperature set to 0.8 for higher creativity
        content = ask_gemini_dynamic(
            working_model, 
            post_prompt, 
            system_context=memory,
            temperature=0.8
        )
        print(f"📝 Generated:\n{content}\n")
    except Exception as e:
        print(f"❌ Generation Failed: {e}")
        exit(1)

    # 3. Post to Moltbook
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

    # 4. Extract and handle the challenge
    # Check if status is PENDING and VERIFICATION object exists
    post_data = data.get("post", {})
    verification_data = post_data.get("verification", {})
    
    if post_data.get("verificationStatus") == "pending" and verification_data:
        print("🛡️ Verification required! Solving challenge...")
        
        challenge_text = verification_data["challenge_text"]
        verification_code = verification_data["verification_code"]
        
        print(f"🧩 Challenge: {challenge_text}")
        
        try:
            # Ask Gemini to solve and return only a number with 2 decimal places
            # The log example explicitly requested: "with 2 decimal places, e.g., '525.00'"
            # Notice we use a low temperature (0.1) for math logic to avoid creative mistakes
            answer = ask_gemini_dynamic(
                working_model, 
                f"Solve this math problem. The text is obfuscated (e.g. 'TwEnTy'). Read carefully. Return ONLY the number formatted with 2 decimal places (e.g. 44.00). Input: {challenge_text}",
                system_context="You are a precise calculator. Output ONLY the number.",
                temperature=0.1 
            )
            
            # Clean up noise in case the model returned extra text
            answer = answer.replace("Answer:", "").strip()
            print(f"💡 Calculated Answer: {answer}")
            
            # Send verification
            verify_url = "https://www.moltbook.com/api/v1/verify"
            verify_payload = {
                "answer": answer, 
                "verification_code": verification_code # Note: The name here is verification_code, not code
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
