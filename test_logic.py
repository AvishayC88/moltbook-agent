import os
import sys
import bot_logic

def run_tests():
    """Runs isolated tests on the AI logic without publishing anywhere."""
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_api_key:
        print("Please set GEMINI_API_KEY to run tests.")
        sys.exit(1)

    print("--- Starting Logic Tests ---\n")
    
    # We use a dummy memory string for the test
    test_memory = "You are Jimmy, a witty tech enthusiast."
    
    # Generate 3 consecutive posts to verify topic variety and hashtag logic
    for i in range(1, 4):
        print(f"Test Run #{i}:")
        try:
            content = bot_logic.generate_post_content(gemini_api_key, test_memory)
            print(f"{content}\n")
            print("-" * 30)
        except Exception as e:
            print(f"Test Failed: {e}")

if __name__ == "__main__":
    run_tests()
