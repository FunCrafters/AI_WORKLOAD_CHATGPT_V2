
# T3RN Agent

## Setup

### Create .env file in root dir of the project. Use template below
```
EMBEDDING_MODEL_ID=nomic-embed-text

# Ollama configuration
OLLAMA_HOST=100.83.28.7
OLLAMA_PORT=11434

OPENAI_API_KEY=<YOUR OPENAI API KEY>

WORKLOAD_DB_PATH=/root/dev/WorkloadData/DB_V1
POSTGRES_HOST=localhost
POSTGRES_USER=tools
POSTGRES_PASSWORD=<PG PASSWORD>
POSTGRES_DB=llm_tools
POSTGRES_PORT=5432

# WORKLOAD SETTINGS 
WORKLOAD_TITLE=<YOUR WORKLOAD TITLE>
# 8 chars required
WORKLOAD_HASH=<WORKLOAD HASH>
WORKLOAD_DESC="T3RN workload model" 
```

### Create python .venv
```
python3 -m venv .venv
```
If you have vs code python extension it should detect .venv and activate it. If you do not have that extention you should activate it manually
```
source .venv/bin/activate
```
Now you can pip install all deps!
```
pip install -r requirements.txt 
```

### Running
```
python workload_main.py
```
```
`ctrl+shift+p` -> `Debug: Select and Start Debugging` -> `Debug Workload`
(Alt: `Ctrl+shfit+g` -> `F5`)
```

### Install required extensions
For this project you should install recommended vs code extensions. 
VS code should showup popup and it will ask if it can install recommended extensions.
You can find them in `.vscode/extensions.json`.

### Typing rules
Use `Pylance` Language server and set typeCheckingMode set to `basic`. 
Typing settings for vs code are in `.vscode/settings.json` file. Install and use `Ruff` Linter.

### Main merge rules
Before merge you should
* Resolve all pylance typing errors and warnings
* Reslove all ruff warnings
* Format all unformatted files with ruff
* Run tests

