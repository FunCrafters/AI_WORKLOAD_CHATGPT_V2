
# T3RN Agent

## Setup

### Create .env file in root dir of the project. Use template below
```
# Model configuration
# For vLLM, use HuggingFace model IDs or local paths
#FALLBACK_MODEL_ID=deepseek-r1:8b
#MAIN_MODEL1_ID=okamototk/deepseek-r1:8b
# TODO Check what models are used.
MAIN_MODEL1_NAME="Deepseek"
MAIN_MODEL2_ID=mistral-small3.1:24b-instruct-2503-q4_K_M
MAIN_MODEL2_NAME="Mistral Small 3.1 Instruct"
MAIN_MODEL3_ID=hermes3:8b
MAIN_MODEL3_NAME="Hermes"
MAIN_MODEL4_ID=magistral:latest
MAIN_MODEL4_NAME="Magistral"

#mistral-small3.1:24b-instruct-2503-q4_K_M
EMBEDDING_MODEL_ID=nomic-embed-text

# Ollama configuration
OLLAMA_HOST=100.83.28.7
OLLAMA_PORT=11434

# OpenAI configuration
OPENAI_API_KEY=<YOUR OPENAI API KEY>

# Database configuration
WORKLOAD_DB_PATH=/root/dev/WorkloadData/DB_V1
POSTGRES_HOST=localhost
POSTGRES_USER=tools
POSTGRES_PASSWORD=<PG PASSWORD>
POSTGRES_DB=llm_tools
POSTGRES_PORT=5432

# WORKLOAD SETTINGS 
WORKLOAD_TITLE=<YOUR WORKLOAD TITLE>
WORKLOAD_HASH=<WORKLOAD HASH>
WORKLOAD_DESC="T3RN workload model" 
```

### Create python .venv
```
python3 -m venv .venv
```
If you have vs code python extension it should detect .env and activate it. If you do not have that extention you should activate it manually
```
source .venv/bin/activate
```
Now you can pip install all deps!
```
pip install -r requirements.txt 
```
