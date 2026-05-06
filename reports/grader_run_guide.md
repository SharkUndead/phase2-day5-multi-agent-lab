# Huong Dan Chay Du An Cho Nguoi Cham

Du an nay hien thuc bai Lab 20 ve he thong nghien cuu da tac nhan
multi-agent research assistant. He thong bao gom:

- Baseline single-agent
- Workflow multi-agent gom Supervisor, Researcher, Analyst, Writer
- Search bang Tavily, co fallback offline
- Goi OpenAI LLM, co fallback offline
- Trace len LangSmith
- Bao cao benchmark baseline vs multi-agent

## 1. Cai Dat Moi Truong

Khuyen nghi dung Python 3.11 tro len.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,llm]"
```

Neu dung Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev,llm]"
```

Neu chua cai package o che do editable, co the chay cac lenh bang cach them:

```powershell
$env:PYTHONPATH='src'
```

## 2. Cau Hinh Bien Moi Truong

Tao file `.env` dua tren `.env.example`.

```env
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4o-mini

LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_API_KEY=...
LANGSMITH_PROJECT=multi-agent-research-lab

TAVILY_API_KEY=...

MAX_ITERATIONS=6
TIMEOUT_SECONDS=60
```

Luu y: du an da duoc cau hinh de gia tri trong `.env` uu tien hon bien moi
truong cu trong terminal. Dieu nay tranh loi dung nham API key cu.

Khong commit file `.env` vi file nay chua API key.

## 3. Chay Test

```bash
pytest
```

Ket qua mong doi:

```text
6 passed
```

## 4. Chay Baseline Single-Agent

```bash
python -m multi_agent_research_lab.cli baseline \
  --query "Compare single-agent and multi-agent research workflows"
```

Ket qua mong doi:

- He thong goi OpenAI thong qua `LLMClient`
- Tao mot cau tra loi cuoi cung trong mot buoc
- Ghi trace event cho baseline

## 5. Chay Workflow Multi-Agent

```bash
python -m multi_agent_research_lab.cli multi-agent \
  --query "Compare single-agent and multi-agent research workflows"
```

Thu tu route mong doi:

```text
researcher -> analyst -> writer -> done
```

Ket qua mong doi:

- Researcher tim nguon bang Tavily hoac mock fallback
- Analyst phan tich claims, evidence strength, trade-offs, open questions
- Writer viet cau tra loi cuoi cung co source references
- Supervisor ghi lai quyet dinh routing
- LangSmith nhan trace neu `LANGSMITH_TRACING=true`

## 6. Xem Trace Tren LangSmith

Mo:

```text
https://smith.langchain.com
```

Vao project:

```text
multi-agent-research-lab
```

Mot trace thanh cong nen co cac run:

- `multi_agent_workflow`
- `supervisor`
- `researcher`
- `analyst`
- `writer`

Trace da xac minh:

```text
multi_agent_workflow chain
2026-05-06 04:33:34 UTC
```

Tuong ung gio Viet Nam:

```text
2026-05-06 11:33:34 Asia/Saigon
```

Nguoi cham co the yeu cau screenshot man hinh LangSmith cho thay run tree gom
`supervisor`, `researcher`, `analyst`, va `writer`.

## 7. Tao Benchmark Report

```bash
python -m multi_agent_research_lab.cli benchmark \
  --query "Compare single-agent and multi-agent research workflows for technical learners"
```

File output:

```text
reports/benchmark_report.md
```

Benchmark da xac minh gan nhat:

```text
baseline latency: 11.53s
multi-agent latency: 37.73s
multi-agent citation coverage: 100%
failure rate: 0%
```

## 8. Cac File Quan Trong De Cham Bai

- `src/multi_agent_research_lab/agents/`
- `src/multi_agent_research_lab/graph/workflow.py`
- `src/multi_agent_research_lab/services/llm_client.py`
- `src/multi_agent_research_lab/services/search_client.py`
- `src/multi_agent_research_lab/observability/tracing.py`
- `reports/benchmark_report.md`
- `reports/lab_completion_report.md`

## 9. Ghi Chu Khi Cham

He thong co fallback offline de van chay duoc khi OpenAI, Tavily, hoac LangSmith
khong kha dung. Tuy nhien, lan benchmark va trace da xac minh gan nhat da chay
voi OpenAI va Tavily that, dong thoi trace da duoc ghi tren LangSmith.
