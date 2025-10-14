import logging
import os
import time
from collections import deque

from dotenv import load_dotenv
from openai import OpenAI

import config

# Set up basic logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class LLMService:
    """A resilient service for making LLM calls.

    This service manages API calls to multiple LLM providers. It includes
    features like rate limiting, exponential backoff retries, and a sequential
    fallback mechanism to ensure high availability.

    Attributes:
        nim_api_key: The API key for the NIM provider.
        vc_api_key: The API key for the VC provider.
        nim_client: An OpenAI client instance configured for the NIM provider.
        vc_client: An OpenAI client instance configured for the VC provider.
        timestamp_queues: A dictionary of deques to track request timestamps
            for rate limiting.
        providers: A list of provider configurations to try in sequence.
    """

    def __init__(self):
        """Initializes the LLMService and configures clients and providers."""
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
            base_url=config.NIM_BASE_URL,
            api_key=self.nim_api_key,
        )
        self.vc_client = OpenAI(
            base_url=config.VC_BASE_URL,
            api_key=self.vc_api_key,
        )

        # --- Shared Rate-Limiting Queues ---
        # All NIM models share one queue, VC has its own.
        self.timestamp_queues = {
            "nim_client": deque(),
            "vc_client": deque(),
        }

        # --- Provider Priority List (Sequential Fallback) ---
        self.providers = []
        for model in config.NIM_MODELS:
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
                "model": config.VC_MODEL,
                "queue": self.timestamp_queues["vc_client"],
            }
        )

    def _rate_limit_wait(self, provider):
        """Checks and waits if the rate limit for a provider has been exceeded.

        Args:
            provider: A dictionary containing the provider's configuration,
                including the timestamp queue.
        """
        now = time.time()
        timestamps = provider["queue"]  # Use the shared queue for the client

        # Remove timestamps older than the rate limit period
        while timestamps and timestamps[0] < now - config.RATE_LIMIT_PERIOD:
            timestamps.popleft()

        if len(timestamps) >= config.RATE_LIMIT:
            wait_time = timestamps[0] - (now - config.RATE_LIMIT_PERIOD)
            logging.warning(
                f"Rate limit for {provider['name']}'s client reached. "
                f"Waiting for {wait_time:.2f} seconds."
            )
            time.sleep(wait_time)

        # Record the new request time
        timestamps.append(time.time())

    def _make_request(self, provider, messages):
        """Makes a single request to a provider and handles exceptions.

        Args:
            provider: The provider configuration dictionary.
            messages: The list of messages to send to the LLM.

        Returns:
            A dictionary containing the response content and metadata on success,
            or None on failure.
        """
        try:
            self._rate_limit_wait(provider)
            logging.info(
                f"Attempting call to {provider['name']} with model {provider['model']}"
            )

            response = provider["client"].chat.completions.create(
                model=provider["model"],
                messages=messages,
                temperature=config.TEMPERATURE,
            )
            return {
                "content": response.choices[0].message.content,
                "provider_name": provider["name"],
                "model_name": provider["model"],
            }
        except OpenAI.APIError as e:
            logging.error(f"API error calling {provider['name']}: {e}")
            return None

    def chat_completion(self, messages):
        """Makes a resilient chat completion request.

        This method attempts to get a chat completion from the configured
        providers in sequence. It handles rate limiting, retries with
        exponential backoff, and falls back to the next provider if a request
        fails after all retries.

        Args:
            messages: A list of message dictionaries, each with 'role' and
                'content' keys, to be sent to the LLM.

        Returns:
            A dictionary containing the LLM response content and metadata.

        Raises:
            Exception: If all LLM providers fail after all retry attempts.
        """
        for provider in self.providers:
            for attempt in range(config.MAX_RETRIES):
                result = self._make_request(provider, messages)
                if result:
                    logging.info(
                        f"Successfully received response from {provider['name']}."
                    )
                    return result

                if attempt < config.MAX_RETRIES - 1:
                    backoff_time = config.INITIAL_BACKOFF * (2**attempt)
                    logging.warning(
                        f"Attempt {attempt + 1} for {provider['name']} failed. "
                        f"Retrying in {backoff_time} seconds."
                    )
                    time.sleep(backoff_time)

            logging.error(
                f"All {config.MAX_RETRIES} retries for {provider['name']} failed. Moving to next provider."
            )

        raise Exception(
            "All LLM providers and fallbacks failed after multiple retries."
        )

    def generate_text(self, prompt):
        """Generates text from a single prompt string.

        This is a convenience method that wraps the `chat_completion` method
        for use cases where only a single user prompt is needed.

        Args:
            prompt: The input prompt string.

        Returns:
            A dictionary containing the LLM response content and metadata.
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
    except OpenAI.APIError as e:
        logging.error(f"Failed to get response from any LLM provider: {e}")
