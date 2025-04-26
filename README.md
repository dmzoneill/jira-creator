# jira-creator

[![Build Status](https://github.com/dmzoneill/jira-creator/actions/workflows/main.yml/badge.svg)](https://github.com/dmzoneill/jira-creator/actions/workflows/main.yml)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
[![License](https://img.shields.io/github/license/dmzoneill/jira-creator.svg)](https://github.com/dmzoneill/jira-creator/blob/main/LICENSE)
[![Last Commit](https://img.shields.io/github/last-commit/dmzoneill/jira-creator.svg)](https://github.com/dmzoneill/jira-creator/commits/main)

A powerful tool that streamlines the creation of JIRA issues such as stories, bugs, epics, spikes, and tasks. With the use of standardized templates and the option of AI-enhanced descriptions, you can create JIRA issues quickly and efficiently.

## ⚡ Quick Start

Get up and running in under 30 seconds.

### 1. Create your configuration file and enable autocomplete

Create a bash script with the values of your JIRA environment variables and enable the autocomplete feature with the following command:

```bash
mkdir -p ~/.bashrc.d
cat <<EOF > ~/.bashrc.d/jira.sh
# Your environment variables here...

# Enable autocomplete
eval "$(/usr/local/bin/rh-issue --_completion | sed 's/rh_jira.py/rh-issue/')"
EOF

source ~/.bashrc.d/jira.sh
```

### 2. Link the command-line tool wrapper

Make the command-line tool wrapper executable and link it to your local bin directory:

```bash
chmod +x jira_creator/rh-issue-wrapper.sh
sudo ln -s $(pwd)/jira_creator/rh-issue-wrapper.sh /usr/local/bin/rh-issue
```

### 3. Run the tool

You can create a new JIRA issue with the following command:

```bash
rh-issue create story "Improve onboarding experience"
```

## 🧪 Usage & Commands

// Your command list goes here...

## 🤖 AI Provider Support

Incorporate different AI providers by setting the `AI_PROVIDER` environment variable.

Use ollama for managing different models:

```bash
mkdir -vp ~/.ollama-models
docker run -d -v ~/.ollama-models:/root/.ollama -p 11434:11434 ollama/ollama
```
Various AI providers are supported, including OpenAI, LLama3, DeepSeek, and more. Setup details for each provider are provided below.

## 🛠 Dev Setup

Install development dependencies with pipenv:

```bash
pipenv install --dev
```

### Testing & Linting

Run the tests and linters with:

```bash
make test
make lint
make super-lint
```

## ⚙️ How It Works

The tool:

- Loads field definitions from `.tmpl` files located in the `templates/` directory.
- Uses `TemplateLoader` to generate Markdown descriptions.
- Optionally uses AI for improving readability and structure.
- Makes a request to the JIRA's REST API (or performs a dry-run).

## 📜 License

This project is licensed under the [Apache License](./LICENSE).