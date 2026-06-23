# Updated Requirements - Platform Capabilities

1. Execution state machine with detailed lifecycle states.
2. Prompt registry using Jinja2 templates stored outside Python code.
3. LLM provider abstraction supporting Gemini, OpenAI, Ollama and Anthropic.
4. Agent configuration persistence in PostgreSQL.
5. LLM usage and cost tracking tables.
6. Artifact storage model for OCR results, summaries and extracted JSON.
7. Retry engine with exponential backoff for external services.
8. Agent Playground UI for direct agent execution and debugging.
9. Internal Event Bus abstraction.
10. Upgrade MedicalAgent from placeholder implementation to a fully working end-to-end reference agent.
