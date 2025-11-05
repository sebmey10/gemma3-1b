# import requests
# import json

# ollama_url = "http://127.0.0.1:11434"
# model_name = "gemma3-1b"

# def chat_with_model(prompt):

#     payload = {
        
#         "model": model_name,
#         "prompt": prompt,
#         "stream": True
#     }

#     try:
#         response = requests.post(ollama_url, json = payload)

#         if response.status_code == 200:

#             result = response.json()

#             return result['response']
        
#         else:
#             return f"Error: Received status code {response.status_code}"
        
#     except requests.exceptions.RequestException as e:
#         return f"Error: {str(e)}"
    
# def main():
#     print("Chat with Gemma")
#     print("Type 'quit' or 'exit' to end the chat.")
#     print("-" * 50)

#     while True:
#         user_input = input("n\You: ")

#         if user_input.lower() in ['quit','exit']:
#             print("Goodbye")
#             break
#         print("\nGemma: ", end="", flush=True)
#         response = chat_with_model(user_input)
#         print(response)

# if __name__ == "__main__":
#     main()

import requests 
import json

ollama_url = "http://127.0.0.1:11434/api/chat"

model = "gemma3:1b"

logfile = []

def send_message(user_input):

    json_payload = {
        "model": model,
        "messages": [{"role": "user", "content": user_input}],
        "stream": False
    }

    send_input = requests.post(ollama_url, data = json_payload)

    send_input.raise_for_status()

    response = send_input.json()
    print(response)

    message = response["message"]["content"]
    print(message)

    logfile.append(message)

    return message

def main():
    print("Chatting with Ollama(type 'quit' to exit)")

    while True:

        user_input = input("YOU: ").strip()

        if user_input.lower() in ["quit"]:
            print("Goodbye")
            break

        try:
            reply = send_message(user_input)
            print(f"Gemma: {reply}\n")

        except Exception as e:
            print(f"Error {e}")

if __name__ == "__main__":
    main()