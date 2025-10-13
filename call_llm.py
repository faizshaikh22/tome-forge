from openai import OpenAI
import os
from dotenv import load_dotenv
import time
from collections import deque
import logging

# Set up basic logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class LLMService:
    """
    A resilient service for making LLM calls with rate limiting, retries, and fallback.
    """

    # Constants for rate limiting and retries
    RATE_LIMIT = 20
    RATE_LIMIT_PERIOD = 60  # in seconds
    MAX_RETRIES = 3
    INITIAL_BACKOFF = 3  # 60s / 20 req = 3s/req

    def __init__(self):
        """
        Initialize the LLM service with multiple clients and rate-limiting queues.
        """
        load_dotenv()

        # Load API keys from environment
        self.nim_api_key = os.getenv("NIM_API_KEY")
        if not self.nim_api_key:
            raise ValueError("NIM_API_KEY environment variable is required")

        self.vc_api_key = os.getenv("VC_API_KEY")
        if not self.vc_api_key:
            raise ValueError("VC_API_KEY environment variable is required")

        # --- Client Configuration ---
        self.nim_client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=self.nim_api_key,
        )
        self.vc_client = OpenAI(
            base_url="https://vanchin.streamlake.ai/api/gateway/v1/endpoints",
            api_key=self.vc_api_key,
        )

        # --- Shared Rate-Limiting Queues ---
        # All NIM models share one queue, VC has its own.
        self.timestamp_queues = {
            "nim_client": deque(),
            "vc_client": deque(),
        }

        # --- Provider Priority List (Sequential Fallback) ---
        nim_models = [
            "openai/gpt-oss-120b",
            "moonshotai/kimi-k2-instruct-0905",
            "deepseek-ai/deepseek-v3.1-terminus",
            "openai/gpt-oss-20b",
            "deepseek-ai/deepseek-r1-0528",
            "mistralai/mistral-nemotron",
            "nvidia/llama-3.1-nemotron-ultra-253b-v1",
        ]

        self.providers = []
        for model in nim_models:
            self.providers.append(
                {
                    "name": f"NIM-{model.split('/')[1]}",  # e.g., NIM-gpt-oss-120b
                    "client": self.nim_client,
                    "model": model,
                    "queue": self.timestamp_queues["nim_client"],
                }
            )

        # Add the final fallback provider
        self.providers.append(
            {
                "name": "VC",
                "client": self.vc_client,
                "model": "ep-8jycqu-1760113893946547399",
                "queue": self.timestamp_queues["vc_client"],
            }
        )

    def _rate_limit_wait(self, provider):
        """
        Checks and waits if the rate limit for a provider's client is exceeded.
        """
        now = time.time()
        timestamps = provider["queue"]  # Use the shared queue for the client

        # Remove timestamps older than the rate limit period
        while timestamps and timestamps[0] < now - self.RATE_LIMIT_PERIOD:
            timestamps.popleft()

        if len(timestamps) >= self.RATE_LIMIT:
            wait_time = timestamps[0] - (now - self.RATE_LIMIT_PERIOD)
            logging.warning(
                f"Rate limit for {provider['name']}'s client reached. "
                f"Waiting for {wait_time:.2f} seconds."
            )
            time.sleep(wait_time)

        # Record the new request time
        timestamps.append(time.time())

    def _make_request(self, provider, messages):
        """
        Makes a single request to a provider and handles exceptions.
        """
        try:
            self._rate_limit_wait(provider)
            logging.info(
                f"Attempting call to {provider['name']} with model {provider['model']}"
            )

            response = provider["client"].chat.completions.create(
                model=provider["model"],
                messages=messages,
                temperature=0.65,
            )
            return {
                "content": response.choices[0].message.content,
                "provider_name": provider["name"],
                "model_name": provider["model"],
            }
        except Exception as e:
            logging.error(f"Error calling {provider['name']}: {e}")
            return None

    def chat_completion(self, messages):
        """
        Makes a resilient chat completion request, handling retries and sequential fallbacks.

        Args:
            messages: List of message dictionaries with role and content.

        Returns:
            Dictionary containing the LLM response or raises an exception if all fail.
        """
        for provider in self.providers:
            for attempt in range(self.MAX_RETRIES):
                result = self._make_request(provider, messages)
                if result:
                    logging.info(
                        f"Successfully received response from {provider['name']}."
                    )
                    return result

                if attempt < self.MAX_RETRIES - 1:
                    backoff_time = self.INITIAL_BACKOFF * (2**attempt)
                    logging.warning(
                        f"Attempt {attempt + 1} for {provider['name']} failed. "
                        f"Retrying in {backoff_time} seconds."
                    )
                    time.sleep(backoff_time)

            logging.error(
                f"All {self.MAX_RETRIES} retries for {provider['name']} failed. Moving to next provider."
            )

        raise Exception(
            "All LLM providers and fallbacks failed after multiple retries."
        )

    def generate_text(self, prompt):
        """
        Generates text from a single prompt string using the resilient pipeline.

        Args:
            prompt: The input prompt string.

        Returns:
            Dictionary containing the LLM response.
        """
        messages = [{"role": "user", "content": prompt}]
        return self.chat_completion(messages)


# Example usage
if __name__ == "__main__":
    logging.info("Starting LLM service example with sequential fallback.")
    service = LLMService()

    try:
        # This will now try the whole sequence of models if failures occur
        result = service.generate_text("What is morality, and what is its origin?")
        logging.info("LLM Response:")
        print(result["content"])
    except Exception as e:
        logging.error(f"Failed to get response from any LLM provider: {e}")
