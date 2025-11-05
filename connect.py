import requests
import json

ollama_url = "http://127.0.0.1:11434"
model_name = "gemma3-1b"

def chat_with_model(prompt):

    payload = {
        
        "model": model_name,
        "prompt": prompt,
        "stream": False
    }

    try:
        response = requests.post(ollama_url, json = payload)

        if response.status_code == 200:

            result = response.json()

            return result['response']
        
        else:
            print("Error")
    except requests.exceptions.RequestException as e:
        return f"Error: Received status code {response.status_code}"
    
def main():
    print("Chat with Gemma")
    print("Type 'quit' or 'exit' to end the chat.")
    print("-" * 50)

    while True:
        user_input = input("n\You:")

        if user_input.lower() in ['quit','exit']:
            print("Goodbye")
            break
        print("\nGemma: ", end="", flush=True)
        response = chat_with_model(user_input)
        print(response)

if __name__ == "__main__":
    main()