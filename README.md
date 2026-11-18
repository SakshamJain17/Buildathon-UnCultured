# 🚀 Buildathon: Make Wednesdays Great Again

**Masters' Union · For AI Developers · Winner gets Rs. 25,000**

> **Every team must build in a fork of this repository.** Projects not built in a fork of this repo won't be judged.

| | |
|---|---|
| **Date** | Wednesday, 18 November 2026 |
| **Hacking** | **3:00 PM – 7:00 PM IST** (code freeze at 7:00 PM sharp) |
| **Venue** | CDS Audi, 8th floor |
| **Prize** | Rs. 25,000 to the winning team |
| **Register your fork** | 👉 **[https://forms.gle/ZJUYKwTYjsMsVB2b9](https://forms.gle/ZJUYKwTYjsMsVB2b9)** (**deadline 3:30 PM IST**) |
| **Final submission** | Your fork as it stands at **7:00 PM IST**. There's nothing else to submit. |

> 🤖 **Using an AI coding agent?** Point it at [`AGENTS.md`](AGENTS.md). It has the full event brief, tracks, judging and rules in a form agents can read directly. Claude Code loads it automatically through `CLAUDE.md`, and Codex reads `AGENTS.md` natively.

---

## 🎯 Pick one build track

| # | Track | Brief |
|---|---|---|
| **01** | **Build for the Physical World** | Make a real-world task easier, faster or more reliable. Show it in a realistic scenario. |
| **02** | **Build for AI Agents** | Find something an agent struggles with. Build the tool that fixes it, then demo the agent using it. |
| **03** | **Build in Your Area of Expertise** | Pick a field you know firsthand. Ship a working product that improves how people handle it today. |

## ⚖️ How you'll be judged (each criterion is ⅓ of your score)

| Criterion | The question judges ask |
|---|---|
| **Working product** | Does it do what you say it does? Show the core workflow in your demo. |
| **Problem insight** | Who faces this problem, and why does it happen? |
| **Depth of execution** | How well did you solve the hardest part of the build? |

---

## Why fork this repo?

Everyone starts from the same commit (the **genesis commit**) at the same time. Organizers can then check that:
- all code was written **during** the Buildathon and not brought in from an earlier project,
- teams commit steadily instead of pasting in one huge AI-generated dump at the end,
- every repo stays public and visible while you build.

The organizers track every fork automatically: commits, timing and activity. Read [RULES.md](RULES.md) before you write any code.

---

## ✅ Setup (about 5 minutes, do it at 3:00 PM)

**In short:** fork → register your fork in the form **by 3:30 PM** → build → push before 7:00 PM.

### 1. Fork this repo
Click **Fork** (top right). On the fork screen:
- **Owner:** one team member's personal account. Only **one fork per team**.
- **Repository name:** `buildathon-<team-name>`, for example `buildathon-byte-bandits`
- Click **Create fork**.

> ⚠️ Don't download a ZIP or copy the files into a new repo. **It has to be a real GitHub fork**, or the tracker can't see you.

### 2. Keep it public
Forks of a public repo are public. **Don't make it private, archive it, or delete it** until judging is over.

### 3. Add your teammates
In your fork: **Settings → Collaborators → Add people**. Add each teammate's GitHub account so their commits count toward the team.

### 4. Enable Actions
Open the **Actions** tab of your fork and click **"I understand my workflows, go ahead and enable them"**. This runs the automatic check on every push.

### 5. Make your registration commit (your first commit)
Fill in [`team.json`](team.json). `track` must be one of `physical-world`, `ai-agents` or `area-of-expertise`. Then:

```bash
git clone https://github.com/<your-username>/buildathon-<team-name>.git
cd buildathon-<team-name>
# edit team.json
git add team.json
git commit -m "register: <team name>"
git push
```

The **Hackathon check** in the Actions tab should go green ✅. If it's red, open the run to see what's wrong in `team.json`.

### 6. Register your fork (deadline: 3:30 PM IST)
👉 **[https://forms.gle/ZJUYKwTYjsMsVB2b9](https://forms.gle/ZJUYKwTYjsMsVB2b9)**

It's a 4-question Google Form: team name, fork link, track, team members. It connects your repo to the organizers' live tracker.

- Fill it in **once per team**, right after forking, and **no later than 3:30 PM IST**. **Teams that don't register can't be tracked.**
- Paste your **fork's** URL (`https://github.com/<you>/buildathon-<team-name>`), not this starter repo's.
- Need to change something? Use the **"Edit your response"** link on the confirmation page. Don't fill it in twice.
- **Final submission is automatic.** Whatever is pushed to your fork at 7:00 PM IST is what gets judged.

---

## 🛠 While you build (3:00 – 7:00 PM)

- Put your code anywhere in the repo (`app/`, `src/`, `frontend/`, `backend/`…). There's no required layout.
- **Commit early, commit often**, at least every 30 minutes of real work, with messages that say what changed.
- **Push regularly.** Commits you never push don't exist to the tracker.
- AI coding tools (Claude Code, Codex, Cursor, Copilot…) are **allowed and encouraged**. Keep `AGENTS.md` and `CLAUDE.md` in the repo; they keep your agent within the rules.
- Before 7:00 PM, replace the "Your project" section below with your project's README.

## 🧊 Code freeze: 7:00 PM IST

At 7:00 PM the tracker takes a snapshot of every fork. **Commits pushed after code freeze are ignored.** Judges look at your last commit before 7:00 PM.

## ❌ Things that get you flagged

- Rewriting history (`git push --force`, rebasing away the genesis commit, squashing everything into one commit)
- Commits dated before 3:00 PM
- One or two giant commits containing most of the project
- A repo that isn't a fork of this one, or that's private or deleted

See [RULES.md](RULES.md) for the full list.

---

## Your project

_Replace this section with your project README:_
- **Team:**
- **Track:**
- **Problem:** who faces it and why it happens
- **What we built:** the core workflow
- **The hardest part:** how we solved it
- **How to run it:**
- **Demo / screenshots:**

---

## ALLURÉ — Find your kind of style.

**Team:** UnCultured — Saksham Jain, Palakshi Purohit, Aditya Sharma. `team.json` currently includes the supplied, verified SakshamJain17 account; the other members' usernames still need to be recorded.

**Track:** Build for AI Agents (`ai-agents`).

ALLURÉ is a personalised fashion experience centred on individuality, expression and personal style. Inspired by the French word *allure*—charm, appeal and the distinctive way someone carries themselves—the brand reflects a belief that fashion is a way to express who you are. Our vision is to use AI to understand individual aesthetics, preferences and colour choices, helping people discover fashion that resonates with them.

*ALLURÉ isn’t just about finding your next outfit; it’s about finding your kind of style.*

**Problem:** Shopping assistants can describe fashion, but often lack a persistent understanding of someone's taste, local weather, and evidence that two listings represent the same garment variant. ALLURÉ gives agents callable fashion tools and gives users explanations grounded in preferences and retrieved data.

**What we built:** A FastAPI backend with session-scoped preferences, five-image style-analysis integration, bounded swipe learning, weather-aware daily outfit suggestions, optional user-selected undertone palettes, real shopping-search integration, conservative offer matching, price arithmetic, and asynchronous virtual try-on integration. A local Ollama agent chooses tools and reads their results. A native SwiftUI iOS 26+ prototype is included under ios/. Website development is handled separately by the teammate.

**The hardest part:** Keeping unsupported claims out of recommendations: unknown prices do not pass budgets, different sizes cannot be exact matches, shipping uncertainty stays visible, fictional fixtures are labelled, and the agent's structured tool results accompany its answer.

### Run

Python 3.11+ (tested with 3.12), uv, and optionally a running Ollama server:

```bash
cd backend
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.txt
cp .env.example .env
.venv/bin/uvicorn app.main:app --reload --port 8766
```

Open http://localhost:8766/docs. Default agent configuration uses local Ollama with `qwen3:8b`; configure a model installed on your machine. Weather and deterministic ranking work independently of LLM credentials. To use the original prompt's port, replace 8766 with 8000 if available.

### Provider configuration

See [model setup](docs/MODEL_SETUP.md). Ollama handles reasoning and optionally photo understanding. Open-Meteo supplies weather. FASHN generates try-on images only when its API credential is configured. SerpApi supplies actual merchant listings only when configured. Gemini is an alternative reasoning/vision provider. No API keys are required simply to start the backend.

### Frontend handoff

[API contract](docs/API_CONTRACT.md) · [UI brief](docs/FRONTEND_BRIEF.md) · [demo guide](docs/DEMO.md)

### Validate

```bash
cd backend
.venv/bin/python -m pytest -q
.venv/bin/python scripts/run_evaluations.py
.venv/bin/python scripts/check_models.py
```

Evaluation JSON is written under ignored `backend/runtime/`. Fixture tests and evaluations do not demonstrate live-provider quality.

### Verified during implementation

- 20 automated tests passed: ownership, invalid inputs/images, profile aggregation, swipe adaptation, idempotency, weather recommendations, matching, prices, adapter behaviour, agent iteration limits, try-on lifecycle, deletion and CORS.
- Actual Open-Meteo geocoding and forecast request succeeded for Gurugram.
- Actual local Ollama `qwen3:8b` agent called retrieve_style_profile and search_demo_catalogue and completed a two-tool task in approximately 6 seconds on the development Mac. This is one smoke test, not a general latency benchmark.
- API health, session creation, preference updates and daily weather-styling endpoints succeeded through a running HTTP server.

### Not yet verified / unfinished

No local vision model was installed, and no live Gemini, SerpApi or FASHN call was made. Real five-photo model analysis, merchant discovery and generated try-on images therefore remain unverified. Their API adapters have unit coverage, not live integration evidence. The website frontend, photo-based complexion analysis, MCP, streaming, embeddings, distributed workers, production authentication and deployment are not implemented. Outfit completion currently uses preferences and category diversity, not a full compatibility model. Occasion and palette intensity are accepted but not applied. Demo catalogue entries are fictional, unpriced and have no product photos or purchase links. Do not use them as proof of live shopping.


### Native iPhone prototype

Open [ios/Allure.xcodeproj](ios/Allure.xcodeproj) in Xcode and press Command+R with an iPhone simulator selected. See [iOS setup](ios/README.md). Native SwiftUI build succeeded using the installed iOS 27.2 simulator SDK, targeting iOS 26+. The actual iOS 26 runtime is not installed. Production Swift API decoding was verified against the running backend, including live weather and durable dismissal. UI interaction automation was unavailable due to desktop-control permissions.

Added backend capabilities: private photo-backed wardrobe, simple owned-item outfits, explicit creator inspiration tags, hairstyle suggestions from user-entered choices, and persistent dislike filtering across catalogue feeds/daily outfits/agent search. There are now 23 passing backend tests.

[Full backend flowchart and frontend blueprint](docs/BACKEND_BLUEPRINT.md)
