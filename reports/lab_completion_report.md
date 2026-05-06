# Bao Cao Hoan Thanh Lab

## 1. Muc Dich Du An

Du an nay hien thuc mot he thong tro ly nghien cuu su dung multi-agent cho Lab
20. He thong nhan cau hoi tu nguoi dung, tim nguon, phan tich noi dung, viet cau
tra loi cuoi cung, sau do so sanh voi baseline single-agent.

Kien truc muc tieu:

```text
User Query
  -> Supervisor
  -> Researcher
  -> Analyst
  -> Writer
  -> Final Answer + Trace + Benchmark Report
```

## 2. Bang Doi Chieu Yeu Cau Va Ket Qua

| Yeu cau | Trang thai | Bang chung |
|---|---|---|
| Implement LLM client | Hoan thanh | `services/llm_client.py` goi OpenAI va co fallback offline |
| Implement search client | Hoan thanh | `services/search_client.py` goi Tavily va co mock fallback |
| Implement Supervisor routing | Hoan thanh | `agents/supervisor.py` route toi researcher, analyst, writer, done |
| Implement Researcher agent | Hoan thanh | Tao `sources` va `research_notes` |
| Implement Analyst agent | Hoan thanh | Tao `analysis_notes` gom claims, evidence, trade-offs |
| Implement Writer agent | Hoan thanh | Tao `final_answer` co source references |
| Implement workflow | Hoan thanh | `graph/workflow.py` chay duoc full multi-agent loop |
| Them guardrails | Hoan thanh | Max iterations, timeout, retry, fallback, error recording |
| Them tracing | Hoan thanh | Local trace va LangSmith trace |
| Benchmark baseline vs multi-agent | Hoan thanh | `reports/benchmark_report.md` |
| Cap nhat tests | Hoan thanh | `pytest` pass 6 tests |
| Giai thich failure mode | Hoan thanh | Co trong bao cao benchmark va muc 7 ben duoi |

## 3. Nhung Phan Da Hien Thuc

### 3.1 Service Layer

`LLMClient` da lam duoc:

- Doc `OPENAI_API_KEY` va `OPENAI_MODEL` tu `.env`
- Goi OpenAI Chat Completions
- Retry khi loi tam thoi
- Fallback sang output offline neu provider loi hoac mat ket noi
- Ghi metadata ve token neu provider tra ve

`SearchClient` da lam duoc:

- Dung Tavily khi co `TAVILY_API_KEY`
- Tra ve cac `SourceDocument` co kieu du lieu ro rang
- Fallback sang mock source khi chay offline hoac khi provider loi

### 3.2 Vai Tro Cac Agent

Supervisor:

- Doc shared state
- Quyet dinh agent tiep theo can chay
- Dung khi da co final answer hoac vuot gioi han iteration

Researcher:

- Tim nguon
- Loai bo nguon trung lap
- Viet research notes dua tren source

Analyst:

- Rut ra key claims
- Danh gia evidence strength
- Neu trade-offs va open questions

Writer:

- Tong hop cau tra loi cuoi cung
- Gan source references nhu `[S1]`, `[S2]`

Critic:

- Agent tuy chon de kiem tra citation coverage va final answer bi thieu

### 3.3 Workflow

Workflow chay theo thu tu:

```text
supervisor -> researcher -> supervisor -> analyst -> supervisor -> writer -> supervisor -> done
```

Workflow ghi lai:

- `route_history`
- `agent_results`
- `trace`
- `errors`

### 3.4 Observability

Tracing hien tai ho tro:

- Local trace trong `ResearchState.trace`
- LangSmith runs khi `LANGSMITH_TRACING=true`
- Root run: `multi_agent_workflow`
- Child runs: `supervisor`, `researcher`, `analyst`, `writer`

Project LangSmith da xac minh:

```text
multi-agent-research-lab
```

Run da xac minh:

```text
multi_agent_workflow chain
2026-05-06 04:33:34 UTC
```

Tuong ung:

```text
2026-05-06 11:33:34 Asia/Saigon
```

## 4. Ket Qua Benchmark

Benchmark gan nhat duoc chay voi OpenAI va Tavily that.

| Run | Latency | Quality heuristic | Citation coverage | Failure rate |
|---|---:|---:|---:|---:|
| Baseline | 11.53s | 3.0/10 | 0% | 0% |
| Multi-agent | 37.73s | 9.0/10 | 100% | 0% |

Nhan xet:

- Baseline nhanh hon vi chi can mot lan goi LLM.
- Multi-agent cham hon vi co nhieu buoc: search, research, analysis, writing.
- Multi-agent co trace ro hon, citation coverage tot hon, va de debug hon.
- Multi-agent phu hop hon voi task can evidence, handoff, va giai thich quy trinh.

## 5. Cach He Thong Dat Learning Outcomes

| Learning outcome | Cach dap ung |
|---|---|
| Thiet ke role ro rang cho nhieu agent | Moi agent co responsibility rieng |
| Xay dung shared state | `ResearchState` luu request, sources, notes, final answer, trace |
| Them guardrails | Co max iterations, timeout, retry, fallback |
| Trace duoc luong chay | Local trace va LangSmith trace |
| Benchmark single-agent vs multi-agent | Co `benchmark_report.md` voi latency, quality, citation, failure rate |

## 6. Deliverables

| Deliverable | Trang thai |
|---|---|
| GitHub repo ca nhan | San sang commit va push |
| Screenshot trace hoac link trace | Can nop screenshot tu LangSmith |
| `reports/benchmark_report.md` | Da co |
| Giai thich failure mode va cach fix | Da co trong muc 7 |

## 7. Failure Modes Va Cach Xu Ly

| Failure mode | Rui ro | Cach xu ly hien tai |
|---|---|---|
| API key cu trong terminal | App co the dung key cu thay vi `.env` | `.env` override environment mac dinh |
| OpenAI/Tavily/LangSmith mat ket noi | Workflow co the fail khi goi provider | Co fallback offline va warning log |
| Vong lap routing vo han | Supervisor co the route mai khong dung | `MAX_ITERATIONS` chan workflow |
| Thieu citations | Final answer kho kiem chung | Writer gan source references khi can |
| Nguon yeu hoac trung lap | Research notes kem chat luong | Researcher deduplicate va luu metadata |

## 8. Nhung Viec Con Lai Neu Muon Nang Cap

Nhung muc duoi day khong bat buoc de nop lab, nhung co the nang cap neu co them
thoi gian:

- Tinh cost USD chinh xac theo model va token usage
- Them CriticAgent vao workflow chinh
- Them scoring bang evaluator LLM thay vi heuristic
- Luu link LangSmith trace truc tiep vao benchmark report
- Them integration LangGraph that thay vi workflow runner tu viet

## 9. Kiem Tra Cuoi

Cac lenh da chay thanh cong:

```bash
pytest
python -m multi_agent_research_lab.cli baseline --query "Say one short sentence confirming OpenAI works"
python -m multi_agent_research_lab.cli multi-agent --query "LangSmith screenshot proof: compare single-agent and multi-agent research workflows"
python -m multi_agent_research_lab.cli benchmark --query "Compare single-agent and multi-agent research workflows for technical learners"
```

Ket qua test:

```text
6 passed
```

OpenAI da xac minh:

```text
HTTP/1.1 200 OK
```

Ket luan: phan code, benchmark, trace, va bao cao da hoan thanh. Phan can nop
thu cong con lai la screenshot LangSmith.
