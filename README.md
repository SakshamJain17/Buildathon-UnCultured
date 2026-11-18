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

**Team:** UnCultured — Saksham Jain, Palakshi Purohit, Aditya Sharma. `team.json` includes the supplied SakshamJain17 account; the other members’ usernames still need to be recorded.

**Track:** Build for AI Agents (`ai-agents`).

**Problem:** Fashion assistants can describe clothes but often lack persistent taste, wardrobe context and reliable product evidence. ALLURÉ gives a personal stylist structured tools to understand preferences, act on feedback and help users find their own style.

**What we built:** A split-film editorial website, a simplified monochrome photographic swipe app, a native SwiftUI iPhone prototype, and a shared FastAPI backend. The single Ollama-powered stylist can retrieve context and perform explicit app actions such as saving a piece or changing preferences. Local vision handles clothing-reference analysis and garment-label suggestions. Daily weather and private wardrobe data inform the experience.

**Hardest part:** Making the assistant actually use tools and persist changes while keeping claims grounded: dislikes remain excluded by best-available identity, unknown prices do not pass budgets, exact matches require variant evidence, and reference imagery is never presented as verified merchant offers.

### Start

```bash
cd backend
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.txt
cp .env.example .env
.venv/bin/python scripts/fetch_reference_images.py
.venv/bin/python scripts/enrich_reference_colours.py
.venv/bin/python scripts/make_films.py  # ffmpeg required
.venv/bin/uvicorn app.main:app --port 8766
```

In another terminal, from repository root:

```bash
PORT=8790 node web/server.js
```

Open http://localhost:8790. API schemas: http://localhost:8766/docs. Native app: open ios/Allure.xcodeproj in Xcode and run on an installed iPhone simulator.

### Models and keys

Local demo: Ollama qwen3:8b for reasoning/actions and gemma3:4b for images; zero API keys. Set OLLAMA_VISION_MODEL=gemma3:4b in backend/.env after downloading it. Live shopping needs SERPAPI_API_KEY; real personal-photo try-on needs FASHN_API_KEY. Neither was supplied, so those features explicitly report unavailable and remain unverified live. Gemini is an optional configured alternative, not required by the local demo.

### Verification

32 backend tests pass. Actual local text/vision calls, a five-image analysis, hairstyle suggestions, model-designed vector avatar, multi-tool agent run, follow-up conversation, live weather and wardrobe persistence were rehearsed. A real browser conversation saved a selected piece and reflected its persisted saved count. Native compilation and Swift API decoding succeeded. The simulator is running; real iOS 26 runtime execution and device signing were not tested.

```bash
cd backend
.venv/bin/python -m pytest -q
.venv/bin/python scripts/rehearse_live_demo.py
```

Live rehearsal writes non-secret results to ignored runtime/live-integration-results.json. Fixture metrics are not live quality benchmarks.

### Demo and handoff

- [Five-minute demo walkthrough](docs/DEMO.md)
- [PRD wiring, keys, verification and unfinished requirements](docs/PRD_STATUS.md)
- [Backend blueprint and flowcharts](docs/BACKEND_BLUEPRINT.md)
- [API contract](docs/API_CONTRACT.md)
- [Website setup](web/README.md) · [iPhone setup](ios/README.md) · [Mac DMG launcher](macos/README.md)

### Honest limits

Reference photos come from the supplied H&M manifest; no affiliation, live price, quality rating or stock is claimed. Sample wardrobe and interactions are explicitly labelled. The avatar is an AI-styled vector illustration, not a generated personal likeness or physical-fit simulation. Palette advice is a curated heuristic from user-selected undertone; no complexion or sensitive-trait inference. Outfit compatibility is an initial attribute/category engine, not a validated fashion model.

No production account recovery/cross-device login, background notifications, live celebrity feeds, precise fit prediction, MCP, embeddings, distributed workers or permanent hosting is implemented. The public tunnel depends on the development Mac and local services remaining online. The DMG is an ad-hoc development WebKit launcher, not an iPhone installer or notarized Mac release.
