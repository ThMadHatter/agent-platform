# LiteLLM Integration and Routing Guide

## 1. Architecture Overview: The Unified LLM Gateway

The Agent Platform has been refactored to use **LiteLLM** as its exclusive interface for Large Language Models. This architectural shift eliminates the need for provider-specific SDKs (like `google-generativeai` or `anthropic`) within the core logic, providing a standardized, "write-once, run-anywhere" interface.

### The `core/llm/` Module
- **`base.py`**: Defines the abstract `LLMProvider` interface, ensuring that any LLM interaction follows a strict contract (`generate` and `generate_structured`).
- **`litellm_client.py`**: The concrete implementation. It uses `litellm.acompletion` to handle requests to any supported backend. It abstracts away the differences in API parameters, error handling, and response formats.
- **`prompt_registry.py`**: Manages Jinja2 templates, allowing prompts to be versioned and modified without changing Python code.

### Benefits
- **Zero Lock-in**: Swap models (e.g., from GPT-4 to Claude 3.5 Sonnet) by changing a single environment variable or model string.
- **Unified Observability**: All usage data (tokens, cost) is captured in a standardized format regardless of the provider.
- **Simplified Dependency Management**: Only `litellm` is required, reducing the risk of dependency conflicts between multiple AI SDKs.

---

## 2. Environment Configuration

The platform relies on LiteLLM's ability to read standard environment variables or route through a LiteLLM Proxy.

### Basic Setup (`.env`)

```bash
# LiteLLM Configuration
DEFAULT_MODEL="openai/gpt-4o"
LITELLM_BASE_URL="http://localhost:4000" # Optional: if using a LiteLLM Proxy
LITELLM_API_KEY="sk-..."                 # Optional: proxy API key

# Direct Provider Keys
# LiteLLM will automatically use these if not routing through a proxy
OPENAI_API_KEY="sk-..."
ANTHROPIC_API_KEY="sk-..."
GEMINI_API_KEY="AIza..."
OPENROUTER_API_KEY="sk-or-..."
```

---

## 3. Provider Configuration Examples

### A. Local Inference (Ollama)
To use local models via Ollama, ensure Ollama is running and accessible.

**Model String:** `ollama/qwen3`, `ollama/llama3`

**Code Example:**
```python
from core.llm.litellm_client import LiteLLMProvider

# Explicitly use a local Ollama model
provider = LiteLLMProvider(model_name="ollama/qwen3")
response = await provider.generate("Analyze this log file...")
```

### B. Cloud Inference
LiteLLM handles the specific prefixes for different cloud providers.

- **OpenAI**: `openai/gpt-4o`, `openai/gpt-3.5-turbo`
- **Anthropic**: `anthropic/claude-3-5-sonnet-20240620`
- **Gemini**: `gemini/gemini-1.5-pro`
- **OpenRouter**: `openrouter/anthropic/claude-3.5-sonnet`

---

## 4. Advanced Scenarios

### A. Model Fallbacks
LiteLLM allows defining fallbacks if a primary model is rate-limited or down.

**Implementation Example:**
```python
import litellm

# Configure global fallbacks in litellm_client.py or at the call site
response = await litellm.acompletion(
    model="gemini/gemini-1.5-pro",
    messages=[{"role": "user", "content": "Hello"}],
    fallbacks=["openai/gpt-4o", "anthropic/claude-3-haiku"]
)
```

### B. Cost Tracking & Budgets
The `LiteLLMProvider` automatically extracts cost information from the response.

```python
response = await provider.generate("Expensive task...")
print(f"Tokens Used: {response.total_tokens}")
print(f"Estimated Cost: ${response.cost:.6f}")

# This data is persisted in the PostgreSQL metadata_store
await metadata_store.record_usage({
    "execution_id": "exec_123",
    "provider": "litellm",
    "model": "gpt-4o",
    "cost": response.cost,
    ...
})
```

### C. Dynamic Routing based on Complexity
The `LiteLLMRouter` implements a routing logic based on a 1-10 complexity score.

**Routing Logic:**
- **1-2**: Small local models (`ollama/qwen3`)
- **3-4**: Efficient coders (`openrouter/deepseek/deepseek-coder`)
- **5-8**: High-performance mid-range (`gemini/gemini-1.5-pro`)
- **9-10**: State-of-the-art flagship (`openai/gpt-4o`)

**Code Example:**
```python
from core.llm.litellm_client import LiteLLMRouter

router = LiteLLMRouter()

# Simple task
response = await router.route_and_execute(
    task_context="What is 2+2?",
    complexity_score=1
)
# Result: Executed on Ollama

# Complex architectural analysis
response = await router.route_and_execute(
    task_context="Refactor this microservices architecture...",
    complexity_score=10
)
# Result: Executed on GPT-4o
```

### D. Structured Output (JSON Schema)
LiteLLM supports native JSON mode and schema enforcement.

```python
schema = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "severity": {"type": "string", "enum": ["low", "medium", "high"]}
    },
    "required": ["summary", "severity"]
}

response = await provider.generate_structured(
    prompt="Analyze the incident report",
    schema=schema
)
# LiteLLM ensures the response is a valid JSON matching the schema
```
