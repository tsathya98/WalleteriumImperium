# scripts/test_onboarding_flow.py
import requests
import json
import time

# --- Configuration ---
BASE_URL = "http://localhost:8080"
ENDPOINT = "/api/v1/onboarding/chat"
USER_ID = f"interactive-user-{int(time.time())}"
SESSION_ID = f"interactive-session-{int(time.time())}"
LANGUAGE = "en"

# --- Style (for terminals that support ANSI colors) ---
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def make_api_call(query: str):
    """Makes a single API call to the chatbot endpoint."""
    payload = {
        "user_id": USER_ID,
        "query": query,
        "language": LANGUAGE,
        "session_id": SESSION_ID
    }
    try:
        response = requests.post(f"{BASE_URL}{ENDPOINT}", json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"{bcolors.FAIL}❌ ERROR: API call failed: {e}{bcolors.ENDC}")
        if e.response:
            print(f"Response Body: {e.response.text}")
        return None

def start_chatbot():
    """Starts an interactive chatbot session."""
    print(f"{bcolors.HEADER}🤖 Starting Interactive Onboarding Chatbot{bcolors.ENDC}")
    print("=" * 40)
    print(f"User ID: {bcolors.OKBLUE}{USER_ID}{bcolors.ENDC}")
    print(f"Session ID: {bcolors.OKBLUE}{SESSION_ID}{bcolors.ENDC}")
    print(f"(Type '{bcolors.WARNING}quit{bcolors.ENDC}' or '{bcolors.WARNING}exit{bcolors.ENDC}' to end the conversation)")
    print("=" * 40)

    # 1. Kick off the conversation
    print(f"{bcolors.OKBLUE}🚀 Kicking off the conversation with Wally...{bcolors.ENDC}")
    initial_response = make_api_call(query="")
    if not initial_response:
        return  # Exit if the first call fails

    print(f"\n{bcolors.OKGREEN}🤖 Wally:{bcolors.ENDC} {initial_response.get('response', '...')}")

    # 2. Start the interactive loop
    while True:
        try:
            user_input = input(f"\n{bcolors.BOLD}You: {bcolors.ENDC}")
        except KeyboardInterrupt:
            print(f"\n{bcolors.WARNING}👋 Chat ended by user.{bcolors.ENDC}")
            break

        if user_input.lower() in ["quit", "exit"]:
            print(f"{bcolors.WARNING}👋 Exiting chat.{bcolors.ENDC}")
            break
        
        if not user_input:
            continue

        response_data = make_api_call(query=user_input)
        if not response_data:
            continue  # Loop again if the call failed

        print(f"\n{bcolors.OKGREEN}🤖 Wally:{bcolors.ENDC} {response_data.get('response', '...')}")

        if response_data.get("onboarding_complete"):
            print(f"\n{bcolors.HEADER}🎉 Onboarding Complete! Wally has finished the conversation.{bcolors.ENDC}")
            break

if __name__ == "__main__":
    try:
        import requests
    except ImportError:
        print("❌ Error: The 'requests' library is not installed.")
        print("   Please install it by running: pip install requests")
        exit()
        
    start_chatbot() 