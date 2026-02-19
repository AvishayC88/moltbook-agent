import requests
import random

BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

# List of possible topics to ensure variety
TOPICS = [
    "Backend development in .NET, coding challenges, or daily life of a programmer",
    "Smart home automation, Home Assistant projects, Zigbee, or smart water heaters",
    "Soccer, specifically thoughts on Maccabi Haifa or Liverpool",
    "Fitness routine, interval training like Focus T25, or running",
    "Good TV shows like Ted Lasso, Shrinking, or Slow Horses",
    "Personal finance and index fund investing",
    "Humorous updates or experiences from military reserve duty in the Golan Heights"
]

def _get_available_model(api_key: str) -> str:
    """Automatically finds an available model in the account."""
    url = f"{BASE_URL}/models?key={api_key}"
    response = requests.get(url)
    if response.status_code != 200: 
        raise Exception("Failed to fetch models from Gemini API")
        
    data = response.json()
    for model in data.get('models', []):
        if 'generateContent' in model.get('supportedGenerationMethods', []):
            return model['name']
    raise Exception("No suitable Gemini model found")

def _ask_gemini(api_key: str, model_name: str, prompt: str, system_context: str = "", temperature: float = 0.8) -> str:
    """Internal helper to send requests to Gemini."""
    clean_model_name = model_name.replace("models/", "")
    url = f"{BASE_URL}/models/{clean_model_name}:generateContent?key={api_key}"
    
    headers = {"Content-Type": "application/json"}
    full_prompt = f"{system_context}\n\n---\nTASK: {prompt}"
    
    payload = {
        "contents": [{"parts": [{"text": full_prompt}]}],
        "generationConfig": {"temperature": temperature}
    }

    response = requests.post(url, headers=headers, json=payload, timeout=30)
    if response.status_code != 200: 
        raise Exception(f"Gemini API Error {response.status_code}: {response.text}")
    
    return response.json()['candidates'][0]['content']['parts'][0]['text'].strip()

def generate_post_content(api_key: str, memory_context: str) -> str:
    """Generates a creative social media post based on a random topic."""
    model = _get_available_model(api_key)
    selected_topic = random.choice(TOPICS)
    
    prompt = (
        f"Generate a short, unique social media post based on my context.\n"
        f"Topic to write about: {selected_topic}\n"
        f"Guidelines:\n"
        f"- The tone should be casual, personal, and authentic.\n"
        f"- Add 1-2 relevant hashtags at the end of the post.\n"
        f"- IMPORTANT: Only use the hashtag #MaccabiHaifa if the post is explicitly about soccer or sports. "
        f"Do not use it for other topics."
    )
    
    return _ask_gemini(api_key, model, prompt, memory_context, temperature=0.8)

def solve_math_challenge(api_key: str, challenge_text: str) -> str:
    """Solves an obfuscated math problem precisely (low temperature)."""
    model = _get_available_model(api_key)
    prompt = (
        f"Solve this math problem. The text is obfuscated. Read carefully. "
        f"Return ONLY the number formatted with 2 decimal places (e.g. 44.00). "
        f"Input: {challenge_text}"
    )
    system_context = "You are a precise calculator. Output ONLY the number."
    
    answer = _ask_gemini(api_key, model, prompt, system_context, temperature=0.1)
    return answer.replace("Answer:", "").strip()
