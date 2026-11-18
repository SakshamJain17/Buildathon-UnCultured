# ALLURÉ — five-minute working demo

## Prepare

1. Keep Ollama, the FastAPI backend (:8766), frontend server (:8790) and public tunnel running.
2. Open the landing page. Both split-screen films should play independently. Use Pause films to demonstrate motion control.
3. Select either side, then “Explore with a reference profile.” This creates a real session and adds clearly labelled sample data. It is not fake AI inference.
4. Walk through the five guided steps, or use You > Guided walkthrough to replay them.

## Demonstrate

1. **Discover:** one photographic card. Right/Like, left/Dismiss, down/Save. Reopen the app with the same session: disliked identities stay excluded.
2. **One bot, real actions:** “Save this piece and tell me how many I have saved.” Inspect the tool trace and the Saved collection. Then: “Change my preferred colours to black and white.” Inspect You > Your style and the fresh feed.
3. **Wardrobe:** six explicitly labelled sample garments. Add an authorised photo, ask vision to suggest labels, review, and save. Ask the bot to build an outfit from the wardrobe.
4. **Weather:** choose Gurugram or another city in the weather chip. Show the actual forecast, never pretend dry weather is rain. Rain behaviour is separately fixture-tested.
5. **Vision:** upload exactly five permitted outfit reference images. The local gemma3:4b model returns structured clothing attributes. There is no skin/ethnicity/health inference.
6. **AI style study:** ask the bot to open the avatar feature. It generates an illustrated fashion figure from model-chosen clothing colours, not a personal likeness.
7. **Progress:** show actual persisted likes, saves, dismissals and wardrobe counts. Sample interactions are illustrative. Progress is feature use, not AI confidence.
8. **Optional integrations:** show try-on or live shopping. If the keys are absent, demonstrate the explicit unavailable state honestly. Do not claim generated outputs or merchant offers exist.

## Key explanation for judges

Ollama chooses and executes validated tools. Ranking and exact price arithmetic remain deterministic. The agent reads a persistent style/wardrobe context, performs user-requested app mutations, and returns source-backed results and an observable trace. No automatic checkout tool exists.

The catalogue contains reference photography supplied in the design brief. Prices, quality ratings, stock and shipping are not fabricated. Reference images are not merchant verification.

## Repeatable checks

```bash
cd backend
.venv/bin/python -m pytest -q
.venv/bin/python scripts/rehearse_live_demo.py
```

The live rehearsal creates and deletes its own disposable test session. It uses only supplied reference photos, never unrelated personal photos. Requires downloaded reference images plus configured local models. Results are saved under ignored runtime/.
