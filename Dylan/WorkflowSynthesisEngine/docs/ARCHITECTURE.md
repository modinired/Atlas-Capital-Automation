
# Architecture and Rationale

## Alignment with Caesar SRC Vision
- Main Agent: `Orchestrator` is the single point of contact handling end-user requests.
- Hyper-Specialized Droids: `ExtractorAgent`, `ValidatorAgent`, `VisualizerAgent` each own a bounded context.
- Three LLMs: `LLMRouter` fans out to two local OpenAI-compatible servers and one remote cloud endpoint.

## Data Flow
1. Transcript enters Orchestrator.
2. Extractor calls the selected LLM endpoint to produce `JobWorkflowSchema` JSON.
3. Schema validation ensures referential integrity and DAG structure.
4. Mermaid renderer produces a machine-readable diagram for UIs and exports.
5. Repository persists the JSON plus Mermaid for downstream integrations.

## Error Handling
- Config schema validation with helpful exceptions.
- Router propagates HTTP and schema issues with rich text.
- Pydantic model validators surface graph errors early.
