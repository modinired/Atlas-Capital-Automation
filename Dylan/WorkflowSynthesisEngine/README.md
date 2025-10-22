
# CESAR-SRC (EJWCS core) - Multi-Agent, Multi-Model

This system implements the Caesar SRC vision: **hyper-specialized agent droids** orchestrated by a **single main agent** that is the user's sole point of contact. It natively supports **three LLMs** (two local, one remote) via an OpenAI-compatible router.

## Key Characteristics
- **Multi-agent**: Orchestrator delegates to Extractor, Validator, Visualizer (extensible: Taxonomy, PII, Publisher, Telemetry).
- **Multi-model**: Router targets `local1`, `local2`, and `remote` endpoints simultaneously or selectively.
- **Production-grade**: Strict schema validation, database persistence, deterministic visualization, unit + integration tests, clear configuration validation.

## Configuration
Provide a YAML config with the following keys. Do not use placeholders; populate with your actual values and endpoint URLs. The application validates that `primary_endpoint` exists among `llm_endpoints` and that each endpoint defines `base_url` and `model`.

## Usage

1. Create and activate a Python 3.10+ virtual environment, then install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Create a config file with your database URL, OpenAI-compatible endpoints, and integration paths. Example:
   ```yaml
   environment: dev
   database_url: sqlite:///workflows.db
   primary_endpoint: remote
   llm_endpoints:
     local1:
       base_url: http://127.0.0.1:11434/v1
       model: qwen2.5:7b
       api_key_env: ""
     remote:
       base_url: https://generativelanguage.googleapis.com/v1beta/openai
       model: gemini-1.5-flash
       api_key_env: GOOGLE_API_KEY
   living_data_brain_db: /Users/modini_red/Desktop/living_data_brain.db
   master_job_tree_root: /Users/modini_red/Desktop/master-job-tree
   autogen_creator_path: /Users/modini_red/autogen_workflow_creator/creator.py
   autogen_workflows_dir: /Users/modini_red/autogen_workflow_creator/workflows
   skill_node_registry: /Users/modini_red/Library/Mobile Documents/com~apple~CloudDocs/Mr. Mayhem SkillsNodeDB/enterprise_agent/enterprise_agent/registry
   automation_matrix_root: /Users/modini_red/Library/Mobile Documents/com~apple~CloudDocs/automation-matrix-pack
   ```
3. Export any API keys the config references (e.g. `export GOOGLE_API_KEY=...`).
4. Provide a transcript text file and run the extractor CLI:
   ```bash
   python -m cesar_src.cli.extract ./config.yaml ./transcript.txt --endpoint remote
   ```
   - Ensure the Mr. Mayhem SkillNode registry and Automation Matrix pack are available locally so enrichment and automation suggestions can run deterministically.
The command outputs the workflow identifier, Mermaid diagram, automation hand-off path, and task count as JSON.


### Optional GUI

- Launch the FastAPI UI (requires `uvicorn` from `requirements.txt`):
  ```bash
  uvicorn cesar_src.ui.app:app --reload
  ```
- Or use the desktop-friendly wrapper:
  ```bash
  python scripts/launch_gui.py
  ```
  This will start the server and open your browser to the dashboard.
- The interface now includes endpoint selection, workflow history, download links, and live Mermaid rendering with a modern theme.

### External Knowledge Packs

- Skill nodes: `/Users/modini_red/Library/Mobile Documents/com~apple~CloudDocs/Mr. Mayhem SkillsNodeDB/enterprise_agent/enterprise_agent/registry`
- Automation matrix: `/Users/modini_red/Library/Mobile Documents/com~apple~CloudDocs/automation-matrix-pack`
- Reference these paths in `config.yaml` to enable skill tagging and automation recommendations.

### Desktop Launcher (Script Launcher Pro)

- Install launcher dependencies:
  ```bash
  pip install -r external_launchers/script_launcher/requirements.txt
  ```
- Launch the macOS desktop interface that now includes the CESAR workflow script:
  ```bash
  python scripts/launch_script_launcher.py
  ```
- Select "CESAR Workflow Synthesis" in the launcher, adjust config/transcript parameters if needed, and press Launch. Output, history, and automation artifacts are captured automatically via the integrations above.


## Development

- Install tooling for tests and lint checks:
  ```bash
  pip install -r requirements-dev.txt
  ```
- Run the unit tests (pins avoid the pytest 8 vs pytest-asyncio incompatibility on Python 3.13):
  ```bash
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest
  ```

## Extending Agents
Add new droids under `cesar_src/agents/` and wire them in the `Orchestrator`. Patterns are intentionally small and composable.
