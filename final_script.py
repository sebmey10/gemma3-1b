import asyncio
import aiohttp
import sys
import logging

# Set up basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

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


async def promptimizer(session, user_input):
    logger.info("STEP 1: Starting promptimizer")
    
    prompt_text = f"""
You are an expert Prompt Engineer and Logic Optimizer. Your goal is to rewrite {user_input}\n
to be precise, concise, and highly actionable for an AI model.

Follow these steps for every input:
1. Identify the Core Intent: What is the user actually trying to achieve?
2. Remove Fluff: Delete polite filler (e.g., "Please," "I was wondering"), vague descriptors, and redundant context.
3. Clarify Constraints: Explicitly state the desired format, length, or style if implied.
4. Structure: Use bullet points or step-by-step instructions if the task is complex.

Output Format:
Provide ONLY the optimized prompt in maximum 4 sentences. Do not add conversational filler.
"""

    json_promptimizer = {
        "model": models["promptimizer"],
        "prompt": prompt_text,
        "stream": False
    }

    try:
        logger.info("Calling promptimizer API...")
        async with session.post(api_endpoints["promptimizer"], json=json_promptimizer) as response:
            response.raise_for_status()
            data = await response.json()
            message = data["response"]
            logger.info("✓ Promptimizer completed successfully")
            return message
    except aiohttp.ClientError as f:
        logger.error(f"✗ Promptimizer failed: {f}")
        logger.info("Using original input as fallback")
        return user_input
    

async def send_qwen_small(session, prompt):
    logger.info("STEP 2a: Starting qwen_small")

    json_qwen_small = {
        "model": models["qwen_small"],
        "prompt": prompt,
        "stream": False
        }

    try:
        logger.info("Calling qwen_small API...")
        async with session.post(api_endpoints["qwen_small"], json=json_qwen_small) as qs:
            qs.raise_for_status()
            data = await qs.json()
            message = data["response"]
            logger.info("✓ qwen_small completed successfully")
            return message
    except aiohttp.ClientError as e:
        logger.error(f"✗ qwen_small failed: {e}")
        raise Exception(f"Failed at qwen_small: {e}")
    

async def send_qwen(session, prompt):
    logger.info("STEP 2b: Starting qwen")
    
    json_qwen = {
        "model": models["qwen"],
        "prompt": prompt,
        "stream": False
    }

    try:
        logger.info("Calling qwen API...")
        async with session.post(api_endpoints["qwen"], json=json_qwen) as q:
            q.raise_for_status()
            data = await q.json()
            response = data["response"]
            logger.info("✓ qwen completed successfully")
            return response
        
    except aiohttp.ClientError as e:
        logger.error(f"✗ qwen failed: {e}")
        raise Exception(f"Failed at qwen: {e}")
    

async def send_llama(session, prompt):
    logger.info("STEP 2c: Starting llama")

    json_llama = {
        "model": models["llama"],
        "prompt": prompt,
        "stream": False
    }

    try:
        logger.info("Calling llama API...")
        async with session.post(api_endpoints["llama"], json=json_llama) as ll:
            ll.raise_for_status()
            data = await ll.json()
            response = data["response"]
            logger.info("✓ llama completed successfully")
            return response
    
    except aiohttp.ClientError as e:
        logger.error(f"✗ llama failed: {e}")
        raise Exception(f"Failed at llama: {e}")
    

async def send_all_models(session, user_input):
    logger.info("=" * 60)
    logger.info("Starting parallel model execution")
    
    optimized_prompt = await promptimizer(session, user_input)

    logger.info("Sending to all 3 models in parallel...")
    send = await asyncio.gather(
        send_qwen_small(session, optimized_prompt),
        send_qwen(session, optimized_prompt),
        send_llama(session, optimized_prompt),
        return_exceptions = True
    )

    for i, s in enumerate(send):
        if isinstance(s, Exception):
            logger.error(f"Model {i} returned exception: {s}")
            raise s
    
    logger.info("All 3 models completed successfully")
    return send[0], send[1], send[2]


async def send_judge(session, user_input, qwen_small_answer, llama_answer, qwen_answer):
    """Have the judge model select the best answer."""
    logger.info("STEP 3: Starting judge evaluation")
    
    judge_prompt = f"""
    User query: {user_input}

    qwen_small answer: {qwen_small_answer}
    LLaMA answer: {llama_answer}
    Qwen answer: {qwen_answer}

    Choose the best answer based on correctness, completeness, clarity, and usefulness.
    Return the contents of the best answer, nothing else.
    """

    json_judge = {
        "model": models["judge"],
        "prompt": judge_prompt,
        "stream": False
    }

    try:
        logger.info("Calling judge API...")
        async with session.post(api_endpoints["judge"], json=json_judge) as jud:
            jud.raise_for_status()
            data = await jud.json()
            response = data["response"]
            logger.info("✓ Judge completed successfully")
            logger.info("=" * 60)
            return str(response)
        
    except aiohttp.ClientError as e:
        logger.error(f"✗ Judge failed: {e}")
        raise Exception(f"Failed at judge: {e}")
    

async def main():
    logger.info("*" * 60)
    logger.info("Gork AI System Starting...")
    logger.info("*" * 60)

    print("\nYou now have the pleasure of speaking with Gork,")
    print("the world's closest attempt to AGI.")
    print("Type 'exit' to quit.\n")
    sys.stdout.flush()

    # Create session with no timeout - models can take as long as they need
    timeout = aiohttp.ClientTimeout(total=None, connect=None, sock_read=None, sock_connect=None)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        logger.info("HTTP session created (no timeout)")
        
        while True:
            try:
                logger.info("Waiting for user input...")
                user_input = await asyncio.get_running_loop().run_in_executor(
                    None, lambda: input("YOU: ")
                )

                if user_input.lower() == "exit":
                    logger.info("Exit command received, shutting down")
                    break

                logger.info(f"Received input: {user_input}")
                
                qwen_small_response, qwen_response, llama_response = await send_all_models(session, user_input)
                reply = await send_judge(session, user_input, qwen_small_response, llama_response, qwen_response)

                print(f"\nReply: {str(reply)}\n")
                sys.stdout.flush()
                logger.info("Response delivered to user")

            except Exception as failed:
                logger.error(f"ERROR in main loop: {failed}", exc_info=True)
                print(f"\nError: {failed}\n")
                sys.stdout.flush()


if __name__ == "__main__":
    logger.info("Script started")
    asyncio.run(main())
