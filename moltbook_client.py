import requests
from dataclasses import dataclass
from typing import Optional

# --- DTO Definitions ---

@dataclass
class PostResult:
    success: bool
    needs_verification: bool
    challenge_text: Optional[str] = None
    verification_code: Optional[str] = None
    error_message: Optional[str] = None

# --- API Functions ---

def publish_post(token: str, content: str) -> PostResult:
    """Publishes a post to Moltbook and returns a strongly-typed result."""
    url = "https://www.moltbook.com/api/v1/posts"
    payload = {
        "content": content,
        "title": "Jimmy's Log",
        "submolt_name": "general"
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code not in [200, 201]:
            return PostResult(success=False, needs_verification=False, error_message=response.text)
            
        data = response.json()
        post_data = data.get("post", {})
        verification_data = post_data.get("verification", {})
        
        # Check if verification is required
        if post_data.get("verificationStatus") == "pending" and verification_data:
            return PostResult(
                success=True, 
                needs_verification=True,
                challenge_text=verification_data.get("challenge_text"),
                verification_code=verification_data.get("verification_code")
            )
            
        return PostResult(success=True, needs_verification=False)

    except requests.exceptions.RequestException as e:
        return PostResult(success=False, needs_verification=False, error_message=str(e))

def send_verification(token: str, answer: str, verification_code: str) -> bool:
    """Sends the solved math challenge back to Moltbook."""
    verify_url = "https://www.moltbook.com/api/v1/verify"
    payload = {
        "answer": answer, 
        "verification_code": verification_code
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    try:
        response = requests.post(verify_url, json=payload, headers=headers)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False
