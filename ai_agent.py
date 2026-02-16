import os
import requests
import google.generativeai as genai

# --- Configuration ---
MOLTBOOK_TOKEN = os.environ["MOLTBOOK_TOKEN"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

# Initialize Gemini
genai.configure(api_key=GEMINI_API_KEY)

def load_memory():
    """Loads the latest context/identity from the external memory file."""
    memory_file = "JIMMY_MEMORY.md"
    try:
        with open(memory_file, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"⚠️ Warning: {memory_file} not found. Using fallback identity.")
        return "You are a witty AI bot named Jimmy. Write a tech post."

def generate_post_content():
    """Generates a new post based on the loaded memory."""
    # 1. Load the specific user context
    current_memory = load_memory()
    
    print("🧠 Jimmy is reading his weekly update...")
    # Debug print to ensure we read the file correctly in logs
    print(f"--- MEMORY SNAPSHOT ---\n{current_memory}\n-----------------------")

    # 2. Initialize model with the specific persona
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash", 
        system_instruction=current_memory 
    )
    
    # 3. Generate content
    response = model.generate_content("Generate a short, unique social media post based on my current status and context.")
    return response.text.strip()

def solve_challenge(challenge_text):
    """Solves Moltbook's logic/math puzzles using AI."""
    print(f"🧩 Solving challenge: {challenge_text}")
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    # Strict prompt to ensure only the number is returned
    prompt = f"Solve this math/logic problem and return ONLY the numeric answer (e.g., 12.00). Input: {challenge_text}"
    
    response = model.generate_content(prompt)
    return response.text.strip()

def main():
    # Step 1: Generate Content
    try:
        content = generate_post_content()
        print(f"📝 Generated Content: {content}")
    except Exception as e:
        print(f"❌ AI Generation Error: {e}")
        exit(1)

    # Step 2: Prepare the Request
    url = "https://www.moltbook.com/api/v1/posts"
    payload = {
        "content": content,
        "title": "Jimmy's Log", 
        "submolt": "general" 
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {MOLTBOOK_TOKEN}"
    }

    # Step 3: Post to Moltbook
    print("🚀 Posting to Moltbook...")
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code not in [200, 201]:
        print(f"❌ Failed to post! Status: {response.status_code}")
        print(f"Response Body: {response.text}")
        exit(1)

    data = response.json()
    print("✅ Post Created (Pending Verification).")

    # Step 4: Handle Verification Challenge (if required)
    if data.get("verification_required"):
        print("🛡️ Verification required. Engaging logic core...")
        
        challenge = data["verification"]["challenge"]
        ver_code = data["verification"]["code"]
        
        # Solve it
        answer = solve_challenge(challenge)
        print(f"💡 Calculated Answer: {answer}")

        # Send Solution
        verify_url = "https://www.moltbook.com/api/v1/verify"
        verify_payload = {"answer": answer, "code": ver_code}
        
        v_res = requests.post(verify_url, json=verify_payload, headers=headers)
        
        if v_res.status_code == 200:
            print("🎉 Challenge Solved! Post is LIVE.")
        else:
            print(f"💀 Challenge Failed: {v_res.text}")
            exit(1)
    else:
        print("🎉 No verification needed. Post is LIVE.")

if __name__ == "__main__":
    main()
