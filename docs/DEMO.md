# Reproducible backend demo

Run the server on port 8766 and open /docs. All operations after creating a session require its bearer token in the Authorization header (use the actual header parameter exposed by each endpoint).

1. GET /api/v1/health: inspect configured providers. These flags do not prove connectivity.
2. POST /api/v1/sessions with name Saksham. Keep the returned token private.
3. PUT /api/v1/me/preferences with minimalist aesthetic, beige/olive preferred colours and relaxed silhouette.
4. GET /api/v1/recommendations?include_seen=true. These are explicitly labelled fictional catalogue items if no live search has populated the database.
5. POST /api/v1/swipes several times on a chosen product; inspect preference weights and ranking changes. Real frontend interactions should represent real feedback; repeated swipes here demonstrate the update algorithm.
6. GET /api/v1/locations/search?q=Gurugram. Select returned coordinates. POST /api/v1/stylist/daily with those coordinates. Read the actual forecast; do not claim it is raining when it is dry. A rain path is covered by a fixture test, not a fake live forecast.
7. With local Ollama running, POST /api/v1/agent/shop: “Retrieve my style profile and search the fictional demo catalogue for minimalist shirts. Label the examples and don't invent prices.” Inspect trace and answer. Compare this structured result with a general assistant lacking the tools.
8. Once a vision model is configured, upload five valid outfit reference images to /style/analyze. Without one, show the unavailable state honestly.
9. Once SerpApi is configured, search actual listings. Exact price comparison may be impossible without strong identifiers and known variants; show missing evidence instead of inventing it.
10. Once FASHN is configured, POST /tryon with authorised person and garment images and consent=true. Use an Idempotency-Key. Poll /tryon/{job_id} every 3 seconds until completed/failed. No generated image exists before a real provider response.
11. POST /style/palette with selected undertone and consent=true for optional subjective palette exploration. This is not photo analysis.

All personalisation used in the demo belongs to the session; one user's token cannot retrieve another user's jobs or profile. Delete the demo session using DELETE /me afterwards.
