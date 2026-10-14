# Wiring this into your existing backend

You already have `app/main.py`, `app/auth.py`, `app/database.py`, etc. —
I don't have their contents, so here's exactly what to add rather than
a file to overwrite.

## 1. Register the router

In `app/main.py`, alongside wherever your other routers are included:

```python
from app.routers.agent_turn import router as agent_turn_router

app.include_router(agent_turn_router)
```

This adds `POST /agent/turn` to your API. It does not conflict with
your existing `routers/agent.py` — different prefix (`/agent` vs
whatever `agent.py` uses), different file. Once you're happy with it,
you can fold `agent_turn.py`'s contents into `agent.py` yourself, or
keep them separate — your call.

## 2. CORS — make sure your frontend origin is allowed

If you don't already have CORS middleware in `main.py`, add:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5500", "http://127.0.0.1:5500"],  # wherever you serve frontend/ from
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Adjust the origin to match however you're serving `frontend/` (e.g. VS
Code Live Server, `python -m http.server`, etc.). If you already have
CORS configured, just make sure that origin is in the allowed list.

## 3. Drop in the LLM wrapper

`app/agents/requirement_manager/agents/conversation_agent.py` and
`question_planner.py` both do:

```python
from app.ai.llm import llm
```

This assumes `app/ai/llm.py` exposes an object called `llm` with a
`.generate(prompt: str) -> str` method — matching what your original
`nodes.py` was already using. If your actual `app/ai/llm.py` has a
different interface, this is the only place the mismatch would show up.

## 4. Run it

```bash
cd backend
uvicorn app.main:app --reload
```

Then open `frontend/pages/agent-test.html` directly in a browser (or
serve `frontend/` with any static server), set the API base URL field
to wherever uvicorn is running (default `http://localhost:8000`), and
it starts a session automatically.

## What the test page does NOT touch

`agent.js`, `agent.html`, `auth.js`, and everything else in your real
frontend are untouched. `agent-test.html` / `agent-test.js` are new,
separate files — safe to delete once you're satisfied and ready to wire
the real UI up the same way.
