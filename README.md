# DS-STAR: A Data Science Agentic Framework

DS-STAR (Data Science - Structured Thought and Action) is a Python-based agentic framework for automating data science tasks. It leverages a multi-agent system to analyze data, devise a plan, write and execute code, and iteratively refine the solution to answer a user's query.

The project extends the original agentic architecture ( https://github.com/JulesLscx/DS-Star) which is based on the paper from Google Research [DS-STAR: A State-of-the-Art Versatile Data Science Agent], with improved task understanding, conversational context handling, structured outputs, and verifier-guided planning.

The goal of this work is to improve the robustness and reasoning capabilities of DS-STAR by enabling the system to:

* Support project level conversation memory.
* Understand whether a user query is standalone or a follow-up question.
* Reconstruct ambiguous follow-up questions into self-contained queries.
* Dataset profiling before planning.
* Explicitly analyze the type of task requested by the user before planning.
* Task decomposition.
* Use structured JSON outputs enforced through schemas.
* Improve iterative planning through structured verifier feedback.

## Main Contributions
Components outlined in intense blue represent our architectural contributions and enhancements to the core DS-STAR pipeline.

![DS-STAR Improved Pipeline Architecture](assets/pipeline_diagram.png)

### Chat History

* A fully containerized PostgreSQL 17 database was integrated using Docker Compose, serving as the central repository for storing multi-turn interaction logs.
*  To automatically identify projects, the system generates a deterministic conversation ID by normalizing and alphabetically sorting dataset paths and applying SHA-256 hashing, enabling project recognition without manual configuration.
*  Additionally, each pipeline execution automatically creates a unique run ID, ensuring complete isolation and traceability of generated artifacts, outputs, and logs.

The system automatically retrieves the four most recent question–answer records from PostgreSQL and formats them as structured conversational context. This context is supplied to both the Planner Init and Planner Next agents, enriching the planning process with project history. As a result, even standalone queries are handled with awareness of previous decisions, dataset characteristics, and user requirements, ensuring consistent and context-aware execution.

#### Query Classification
A new Query Classifier agent was introduced to determine whether a user query:
* starts a new conversation (standalone)
* continues a previous discussion (follow_up)

This allows the framework to distinguish between independent requests and context-dependent questions.

#### Contextualization
A new Contextualizer agent rewrites follow-up questions into self-contained standalone queries using retrieved conversation history.

Example:
User: Find the target variable.

History:The target variable is species.

Follow-up:What is its distribution?

Contextualized query: What is the distribution of the species variable?

### Data Profiling
Instead of relying solely on the LLM to infer dataset characteristics from sample rows, the system integrates the ydata-profiling library to generate a comprehensive dataset profile. A full interactive HTML report containing statistical summaries, correlations, and feature distributions is produced and stored. To avoid overwhelming the LLM context window, only the most relevant information—such as data schemas, inferred task types, and structural warnings—is extracted into a compact JSON representation and provided directly to the planning agents.
All artifacts for each run are stored in the `runs/` directory, organized by `run_id`.

### Task Analysis
A new Task Analyzer agent performs explicit task understanding before planning.
The agent identifies:
* primary task
* secondary tasks
* machine learning requirements
* problem type
* target variable
* requested outputs

This information is then provided to the Planner to improve planning quality.

### Structured Outputs
The framework was extended to use Structured Outputs through JSON Schemas.
Structured schemas were implemented for:
*Query Classifier
*Contextualizer
*Task Analyzer
*Verifier
This improves output consistency and reduces parsing failures.

### Verifier-Guided Planning
The Verifier was redesigned to return structured feedback containing:
* completion status
* satisfied requirements
* missing requirements
* execution errors
* recommended next action

The Planner uses this feedback during refinement rounds to generate more targeted plans.

## Project Structure

```
/
├─── dsstar.py               # Main script containing the agent logic and CLI
├─── db_conn.py              # PostgreSQL connection manager and session pooling
├─── db_tables.py            # Database schema setup, SQL queries, and chat history management
├─── docker-compose.yml      # Docker configuration for the PostgreSQL 17 database
├─── config.yaml             # Main configuration file
├─── prompt.yaml             # Prompts for the different AI agents
├─── pyproject.toml          # Project metadata and dependencies (uv format)
├─── uv.lock                 # Locked dependency versions for reproducibility
├─── .python-version         # Python version specification for uv
├─── data/                   # Directory for your data files
├─── db/                     # Local persistent storage volume for PostgreSQL data
└─── runs/                   # Directory where all experiment runs and artifacts are stored
```

## Getting Started

### Prerequisites

- Python 3.11
- [uv](https://docs.astral.sh/uv/) package manager (recommended)
- [Docker](https://docs.docker.com/engine/install) 

### Installation

#### Using uv (Recommended)

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd DS-Star
    ```

2.  **Install uv (if not already installed):**
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

3.  **Install dependencies with uv:**
    ```bash
    uv sync
    ```
4.  **Install Docker:**
    https://docs.docker.com/engine/install

5. **DB Setup:**
    ```bash
    docker compose up ds-star-postgres
    ```

### Configuration

2.  **Customize `config.yaml`:**
    Create a `config.yaml` file in the root of the project and customize the settings. See the "Configuration" section below for details.

    ```yaml
    # config.yaml
    model_name: 'ollama/qwen3:8b'
    max_refinement_rounds: 3
    interactive: false
    # api_key: 'your-api-key' # Alternatively, place it here
    
    # Optional: Configure specific models for different agents
    agent_models:
      PLANNER: 'ollama/gemma4:12b'
      CODER: 'ollama/qwen3-coder'
      VERIFIER: ollama/gemma4:12b'
    ```

## Usage

Place your data files (e.g., `.xlsx`, `.csv`) in the `data/` directory.

### Starting a New Run

To start a new analysis, you need to provide the data files and a query.

Using uv:
```bash
uv run python dsstar.py --data-files file1.xlsx file2.xlsx --query "What is the total sales for each department?"
```

### Resuming a Run

If a run was interrupted, you can resume it using its `run_id`.

```bash
uv run python dsstar.py --resume <run_id>
```

### Editing Code During a Run

You can manually edit the last generated piece of code and re-run it. This is useful for manual debugging or tweaking the agent's logic.

```bash
uv run python dsstar.py --edit-last --resume <run_id>
```
This will open the last code file in your default text editor (`nano`, `vim`, etc.). After you save and close the editor, the script will re-execute the modified code.

### Interactive Mode

To review each step before proceeding, use the interactive flag.

```bash
uv run python dsstar.py --interactive --data-files ... --query "..."
```

## UV Package Manager

This project uses `uv` for fast and reliable dependency management. Here are some useful commands:

### Common UV Commands

- **Install dependencies**: `uv sync`
- **Add a new dependency**: `uv add package-name`
- **Remove a dependency**: `uv remove package-name`
- **Update dependencies**: `uv sync --upgrade`
- **Run a command in the virtual environment**: `uv run python script.py`
- **Show installed packages**: `uv pip list`

### Benefits of UV

- **Speed**: uv is 10-100x faster than pip
- **Reliability**: Consistent dependency resolution with lock files
- **No virtual environment activation needed**: Use `uv run` to execute commands directly
- **Better dependency resolution**: Automatically resolves complex dependency conflicts

## Configuration

The following options are available in `config.yaml` and can be overridden by CLI arguments:

- `max_refinement_rounds` (int): The maximum number of times the agent will try to refine its plan.
- `api_key` (string): Your Gemini API key.
- `model_name` (string): The Gemini model to use (e.g., `gemini-1.5-flash`).
- `interactive` (bool): If true, waits for user input before executing each step.
- `auto_debug` (bool): If true, the `Debugger` agent will automatically try to fix failing code.
- `execution_timeout` (int): Timeout in seconds for code execution.
- `execution_timeout` (int): Timeout in seconds for code execution.
- `preserve_artifacts` (bool): If true, all step artifacts are saved to the `runs` directory.
- `agent_models` (dict): A dictionary mapping agent names (e.g., `PLANNER`, `CODER`) to specific model names. If not specified, `model_name` is used.

## Providers

DS-STAR supports multiple AI model providers. Each provider requires specific environment variables to be configured:

### Google Gemini

**Provider Identifier**: Default provider (no prefix required)

**Environment Variable**:
```bash
export GEMINI_API_KEY='your-gemini-api-key'
```

**Model Examples**:`gemini-2.5-pro`, `gemini-2.0-flash`

### OpenAI

**Provider Identifier**: Models prefixed with `gpt` or `o1`

**Environment Variable**:
```bash
export OPENAI_API_KEY='your-openai-api-key'
```

**Model Examples**: `gpt-4`, `gpt-4-turbo`, `o1`

### Ollama

**Provider Identifier**: Models prefixed with `ollama/`

**Environment Variables**:
```bash
export OLLAMA_API_KEY='your-ollama-api-key'  # Optional
export OLLAMA_HOST='http://localhost:11434'  # Optional, defaults to http://localhost:11434
```

**Model Examples**: `ollama/llama3`, `ollama/qwen3-coder`
## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue for any bugs or feature requests.

```
