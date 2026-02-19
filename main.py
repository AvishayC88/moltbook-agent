import os
import sys
import bot_logic
import moltbook_client

def load_memory() -> str:
    """Loads bot memory from file."""
    try:
        with open("JIMMY_MEMORY.md", "r", encoding="utf-8") as f: 
            return f.read()
    except FileNotFoundError: 
        return "You are Jimmy, a witty AI bot."

def main():
    # 1. Configuration & Dependency Injection
    moltbook_token = os.environ.get("MOLTBOOK_TOKEN")
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    
    if not moltbook_token or not gemini_api_key:
        print("💀 FATAL: Missing API keys in environment variables.")
        sys.exit(1)

    memory_context = load_memory()

    try:
        # 2. Generate Content
        print("🧠 Generating new post content...")
        content = bot_logic.generate_post_content(gemini_api_key, memory_context)
        print(f"📝 Generated:\n{content}\n")

        # 3. Publish to Moltbook
        print("🚀 Publishing to Moltbook...")
        post_result = moltbook_client.publish_post(moltbook_token, content)

        if not post_result.success:
            print(f"❌ Post Failed: {post_result.error_message}")
            sys.exit(1)

        print("✅ Post Created.")

        # 4. Handle Verification Challenge (If Needed)
        if post_result.needs_verification:
            print("🛡️ Verification required! Solving challenge...")
            print(f"🧩 Challenge: {post_result.challenge_text}")
            
            # Use logic module to solve the math
            answer = bot_logic.solve_math_challenge(gemini_api_key, post_result.challenge_text)
            print(f"💡 Calculated Answer: {answer}")
            
            # Send the solved answer back to the client module
            is_verified = moltbook_client.send_verification(
                moltbook_token, 
                answer, 
                post_result.verification_code
            )
            
            if is_verified:
                print("🎉 SUCCESS! Post Verified & Live!")
            else:
                print("💀 Verification Failed.")
                sys.exit(1)
        else:
            print("🎉 No verification needed. Post is live!")

    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
