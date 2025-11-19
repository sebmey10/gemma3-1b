import aiohttp
import asyncio
import json

# These are the sockets of each container that I'm going to deploy.
api_endpoints = {
    "promptimizer": "http://promptimizer:11434/api/generate",
    "llama": "http://llama:11434/api/generate",
    "qwen": "http://qwen:11434/api/generate",
    "qwen_small": "http://qwen-small:11434/api/generate",
    "judge": "http://judge:11434/api/generate",
}

# These are the models I'm using to execute the workflow
models = {
    "promptimizer": "granite4:350m",
    "llama": "llama3.2:1b",
    "qwen": "qwen2.5-coder:1.5b",
    "qwen_small": "qwen3:0.6b",
    "judge": "gemma3:1b"
}

llama_logfile = []
qwen_logfile = []
qwen_small_logfile = []


async def promptimizer(session, user_input):
    promptimizer_prompt = f"""
    Take {user_input} and rewrite it into a more concise query. The goal is to provide AI systems with a clear, 
    focused prompt for optimal interpretation and response. Only respond with the re-written query."""

    json_promptimizer = {
        "model": models["promptimizer"],
        "prompt": promptimizer_prompt,
        "stream": False
    }

    try:
        async with session.post(api_endpoints["promptimizer"], json=json_promptimizer) as response:
            response.raise_for_status()
            response_data = await response.json()
            message_promptimizer = response_data["response"]
            return message_promptimizer

    except aiohttp.ClientError as failed:
        raise Exception(f"Promptimizer didn't work: {str(failed)}")


async def call_qwen_small(session, optimized_prompt):
    json_qwen_small = {
        "model": models["qwen_small"],
        "prompt": optimized_prompt,
        "stream": False
    }
    
    try:
        async with session.post(api_endpoints["qwen_small"], json=json_qwen_small) as response:
            response.raise_for_status()
            response_data = await response.json()
            message_qwen_small = response_data["response"]
            qwen_small_logfile.append({"role": "assistant", "content": message_qwen_small})
            return message_qwen_small
            
    except aiohttp.ClientError as failed:
        raise Exception(f"Qwen Small didn't work: {str(failed)}")


async def call_llama(session, optimized_prompt):
    json_llama = {
        "model": models["llama"],
        "prompt": optimized_prompt,
        "stream": False
    }

    try:
        async with session.post(api_endpoints["llama"], json=json_llama) as response:
            response.raise_for_status()
            response_data = await response.json()
            message_llama = response_data["response"]
            llama_logfile.append({"role": "assistant", "content": message_llama})
            return message_llama
            
    except aiohttp.ClientError as failed:
        raise Exception(f"LLaMA didn't work: {str(failed)}")


async def call_qwen(session, optimized_prompt):
    json_qwen = {
        "model": models["qwen"],
        "prompt": optimized_prompt,
        "stream": False
    }

    try:
        async with session.post(api_endpoints["qwen"], json=json_qwen) as response:
            response.raise_for_status()
            response_data = await response.json()
            message_qwen = response_data["response"]
            qwen_logfile.append({"role": "assistant", "content": message_qwen})
            return message_qwen
            
    except aiohttp.ClientError as failed:
        raise Exception(f"Qwen didn't work: {str(failed)}")


async def send_message_models(session, user_input):
    # First, optimize the prompt
    optimized_prompt = await promptimizer(session, user_input)
    
    # Then call all three models in parallel
    results = await asyncio.gather(
        call_qwen_small(session, optimized_prompt),
        call_llama(session, optimized_prompt),
        call_qwen(session, optimized_prompt),
        return_exceptions=True
    )
    
    # Check for exceptions
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            raise result
    
    return results[0], results[1], results[2]


async def make_judgement(session, user_input):
    judge_prompt = f"""
    User query: {user_input}

    qwen_small answer: {qwen_small_logfile[-1]['content']}
    LLaMA answer: {llama_logfile[-1]['content']}
    Qwen answer: {qwen_logfile[-1]['content']}

    Choose the best answer based on correctness, completeness, clarity, and usefulness.
    Return the contents of the best answer, nothing else.
    """

    json_judge = {
        "model": models["judge"],
        "prompt": judge_prompt,
        "stream": False
    }

    try:
        async with session.post(api_endpoints["judge"], json=json_judge) as response:
            response.raise_for_status()
            response_data = await response.json()
            message_judge = response_data["response"]
            return str(message_judge)
    
    except aiohttp.ClientError as failed:
        raise Exception(f"Judge didn't work: {str(failed)}")


async def main():
    print("Chatting with gorkheavy-lite! (type 'exit' to quit)")
    
    # Create a single session for all requests
    timeout = aiohttp.ClientTimeout(total=300)  # 5 minute timeout for slow models
    async with aiohttp.ClientSession(timeout=timeout) as session:
        while True:
            # Use asyncio loop to get input (non-blocking for async context)
            user_input = await asyncio.get_event_loop().run_in_executor(
                None, lambda: input("YOU: ").strip()
            )

            if user_input.lower() == "exit":
                print("Bye!")
                break

            try:
                await send_message_models(session, user_input)
                reply = await make_judgement(session, user_input)
                print(f"Reply: {reply}\n")
            except Exception as failed:
                print(f"Error: {failed}")


if __name__ == "__main__":
    asyncio.run(main())