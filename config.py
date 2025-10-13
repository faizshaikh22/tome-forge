# config.py

# --- General Settings ---
SOURCES_DIR = "Sources"
PROGRESS_FILE = "_completed_chapters.log"
AUTHOR = "Nietzsche"

# --- Q&A Generation Parameters ---
TARGET_TOTAL_PAIRS = 10000
MIN_QUESTIONS_PER_CHAPTER = 10
MAX_QUESTIONS_PER_CHAPTER = 100
DEFAULT_QUESTIONS_PER_CHAPTER = 20

# --- LLM Service Settings ---
# Rate limiting
RATE_LIMIT = 20
RATE_LIMIT_PERIOD = 60  # in seconds

# Retries and backoff
MAX_RETRIES = 3
INITIAL_BACKOFF = 3  # seconds

# Model temperature
TEMPERATURE = 0.65

# --- Provider and Model Configuration ---
NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"
VC_BASE_URL = "https://vanchin.streamlake.ai/api/gateway/v1/endpoints"

NIM_MODELS = [
    "openai/gpt-oss-120b",
    "moonshotai/kimi-k2-instruct-0905",
    "deepseek-ai/deepseek-v3.1-terminus",
    "openai/gpt-oss-20b",
    "deepseek-ai/deepseek-r1-0528",
    "mistralai/mistral-nemotron",
    "nvidia/llama-3.1-nemotron-ultra-253b-v1",
]

VC_MODEL = "ep-8jycqu-1760113893946547399"

# --- Prompt Settings ---
# Defines the percentage distribution of question types
QUESTION_LAYER_DISTRIBUTION = {
    "semantic": 0.20,
    "episodic": 0.15,
    "procedural": 0.20,
    "emotional": 0.15,
    "structural": 0.15,
}

# --- Book Download Settings ---
BOOKS_TO_DOWNLOAD = {
    "The Dawn of Day": 39955,
    "Human, All Too Human": 38145,
    "Thus Spoke Zarathustra": 1998,
    "Beyond Good and Evil": 4363,
    "The Antichrist": 19322,
    "The WIll to Power - Book 1-3": 52914,
    "The WIll to Power - Book 3-4": 52915,
    "The Joyful Science": 52881,
    "The Birth of Tragedy": 51356,
    "Ecce Homo": 52190,
    "Twilight of the Idols": 52263,
    "The Genealogy of morals": 52319,
}
