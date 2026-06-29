# Architectural Audit - Agent Platform

## 1. Findings

### 1.1 Architectural Weaknesses
- **Tight Coupling in API Layer**: `apps/api/main.py` hardcodes agent instances. Adding a new agent requires manual registration in the main application file.
- **Inconsistent Agent Instantiation**: Some agents are instantiated in `apps/api/dependencies.py` (shared instances), while the n8n webhook router reinstantiates `RepoAnalyzerAgent` on every request.
- **Linear Execution Flow**: The `AgentRunner` follows a fixed sequence of steps (`validate` -> `retrieve_context` -> `plan` -> `execute` -> `validate_output` -> `persist`). While structured, it doesn't easily support branching or complex internal loops without embedding that logic inside the `execute` step.
- **Missing Retry Logic**: There is no built-in mechanism for retrying failed steps or executions at the platform level.
- **Hardcoded Routing**: `LiteLLMRouter` contains a hardcoded complexity-to-model mapping.
- **Resource Management**: No explicit artifact management for large files beyond simple JSON/text storage in the database.

### 1.2 Unnecessary Abstractions
- The `AgentInput` and `AgentOutput` in `BaseAgent` are somewhat redundant with Pydantic's native capabilities if not strictly enforced by the runner in a more dynamic way.

### 1.3 Missing Interfaces / Extension Points
- **Agent Registry**: No central way to discover available agents and their capabilities (input/output schemas).
- **Service Discovery**: Agents don't have a standardized way to request shared services (OCR, Search, etc.) beyond manual dependency injection.

### 1.4 Scalability Issues
- The current `AgentRunner` is synchronous in its `run` method (it waits for completion), which might lead to timeouts for long-running agents if not called via a background task or handled asynchronously by the client (polling).

---

## 2. Proposed Architecture

### 2.1 Decoupled Agent Registry
Implement a `CapabilityRegistry` that allows agents to register themselves with metadata. The API layer should discover agents through this registry.

### 2.2 Orchestration vs. Execution
Maintain the `AgentRunner` as the execution engine but enhance it with a `RetryEngine`. Agents should be thin orchestrators of specialized `Services`.

### 2.3 Shared Service Layer
Standardize "Services" (e.g., `OCRService`, `SearchService`) that agents can consume. This prevents code duplication across domains (e.g., Medical and Job domains both needing OCR or Web Scraping).

### 2.4 n8n Optimized Endpoints
Ensure all agent executions support both synchronous (blocking) and asynchronous (returns `execution_id` immediately) modes to suit different n8n workflow patterns.

---

## 3. Migration Plan

1. **Phase 1: Core Refactoring**
   - Implement `AgentRegistry`.
   - Implement `RetryEngine`.
   - Update `AgentRunner` to use the registry and retry logic.
2. **Phase 2: Job Domain Implementation**
   - Build the `JobAgent` using a service-oriented approach.
   - Decouple LinkedIn scraping and Resume parsing into services.
3. **Phase 3: API Standardization**
   - Refactor `apps/api/main.py` to use the registry.
   - Expose `GET /agents` for discovery.

---

## 4. Future Improvements
- **Dynamic Routing 2.0**: Allow model routing to be configured via the database or a config file instead of code.
- **Artifact Store**: Integrate with S3 or similar for large binary artifacts.
- **Real-time Monitoring**: WebSocket support for streaming execution updates to n8n or a dashboard.
