# jira-creator

Create JIRA issues (stories, bugs, epics, spikes, tasks) quickly using standardized templates and optional AI-enhanced descriptions.

---

## ⚡ Quick Start (Under 30 Seconds)

### 1. Create your config file and enable autocomplete:

```bash
mkdir -p ~/.bashrc.d
cat <<EOF > ~/.bashrc.d/jira.sh
export JPAT="your_jira_personal_access_token"
export AI_PROVIDER=openai
export OPENAI_API_KEY=sk-...
export JIRA_URL="https://issues.redhat.com"
export PROJECT_KEY="AAP"
export AFFECTS_VERSION="aa-latest"
export COMPONENT_NAME="analytics-hcc-service"
export PRIORITY="Normal"
export JIRA_BOARD_ID=21125

# Enable autocomplete
eval "$(register-python-argcomplete rh-issue)"
EOF

source ~/.bashrc.d/jira.sh
```

---

### 2. Link the CLI wrapper:

```bash
chmod +x rh-issue-wrapper.sh
sudo ln -s $(pwd)/rh-issue-wrapper.sh /usr/local/bin/rh-issue
```

---

### 3. Run it:

```bash
rh-issue story "Improve onboarding experience"
```

---

## 🧪 Usage & Commands

### 🆕 Create Issues

```bash
rh-issue create bug "Fix login crash"
rh-issue create story "Refactor onboarding flow"
rh-issue create epic "Unify frontend UI" --edit
rh-issue create spike "Evaluate GraphQL support" --dry-run
```

Use `--edit` to use your `$EDITOR`, and `--dry-run` to print the payload without creating the issue.

### 🔁 Change Issue Type

```bash
rh-issue change-type AAP-12345 story
```

### 🔁 Migrate Issue

```bash
rh-issue migrate-to story AAP-54321
```

### ✏️ Edit Description

```bash
rh-issue edit-issue AAP-98765
rh-issue edit-issue AAP-98765 --no-ai
```

### 🧍 Unassign Issue

```bash
rh-issue unassign AAP-12345
```

### 📋 List Issues

```bash
rh-issue list-issues
rh-issue list-issues --project AAP --component api --user jdoe
```

### 🏷️ Set Priority

```bash
rh-issue set-priority AAP-123 High
```

### 📅 Sprint Management

```bash
rh-issue set-sprint AAP-456 1234
rh-issue remove-sprint AAP-456
rh-issue add-sprint AAP-456 "Sprint 33"
```

### 🚦 Set Status

```bash
rh-issue set-status AAP-123 "In Progress"
```

---

## 🤖 AI Provider Support

You can plug in different AI providers by setting `AI_PROVIDER`.

### ✅ OpenAI

```bash
export AI_PROVIDER=openai
export OPENAI_API_KEY=sk-...
export OPENAI_MODEL=gpt-4  # Optional
```

### 🖥 GPT4All

```bash
pip install gpt4all
export AI_PROVIDER=gpt4all
```

### 🧪 InstructLab

```bash
export AI_PROVIDER=instructlab
export INSTRUCTLAB_URL=http://localhost:11434/api/generate
export INSTRUCTLAB_MODEL=instructlab
```

### 🧠 BART

```bash
export AI_PROVIDER=bart
export BART_URL=http://localhost:8000/bart
```

### 🧠 DeepSeek

```bash
export AI_PROVIDER=deepseek
export DEEPSEEK_URL=http://localhost:8000/deepseek
```

### 🪫 Noop

```bash
export AI_PROVIDER=noop
```

---

## 🛠 Dev Setup

```bash
pipenv install --dev
```

### Testing & Linting

```bash
make test
make lint
make format  # auto-fix formatting
```

---

## ⚙️ How It Works

- Loads field definitions from `.tmpl` files under `templates/`
- Uses `TemplateLoader` to generate Markdown descriptions
- Optionally applies AI cleanup for readability and structure
- Sends to JIRA via REST API (or dry-runs it)

---

## 📁 Project Structure

```
jira-creator/
├── rh-jira.py
├── rh-issue-wrapper.sh
├── templates/
├── providers/
├── jira/
├── tests/
└── Pipfile
```