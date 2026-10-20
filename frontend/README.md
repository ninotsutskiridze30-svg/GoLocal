# goLocal frontend

An immersive, 3D-first event discovery journey built with Next.js (App Router), React Three Fiber, Three.js and drei. The whole site lives inside one full-viewport WebGL canvas. Scrolling moves the camera through four zones, and every piece of UI is a 3D Html portal or a floating 3D element.

## Journey

| Zone | What it does |
| --- | --- |
| 01 Entrance | Floating "GoLocal AI" wordmark, a glass orb that drifts toward the pointer, and the call to action. |
| 02 Mood | A glass mood wheel (Relaxed, Tech & Innovation, Nightlife, Art & Culture) and a budget dial. The chosen mood rotates to the top. |
| 03 Picks | A 3D grid of glass event cards. Cards tilt toward the pointer. Selecting one flies the camera in to show details and the AI reasoning. |
| 04 Ask AI | A floating console for natural-language search, with live status and the strongest matches. |

Wheel, touch and the HUD station buttons all drive the same scroll path. `Esc` closes an inspected card.

## Run locally

From this folder:

```powershell
npm install
npm run dev
```

Open `http://localhost:3000`.

The interface runs in demo mode by default. Its example listings are fictional, marked as demo, and link to no real source. Saved events are stored in this browser.

## Connect the API

Create `.env.local` in this folder and set:

```text
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

The app reads `GET /events?page=1&page_size=30` for browse results and sends `POST /search` with `{ "query": "..." }` for natural-language search. The search response should follow `docs/api-contract.md` in the repository root. Restart the development server after changing the environment file.

## Structure

- `app/` routes, global styles and the page shell that wires data to the scene.
- `components/scene/` the 3D zones, camera rig, scroll bridge and HUD. `SceneHtml` is the one place Html portals are created.
- `components/ui/` the DOM panels rendered inside the 3D Html portals (event card, AI console, HUD, mood and budget controls).
- `hooks/useEventEngine.ts` loads events, runs search and falls back to preview matches when the API is unavailable.
- `lib/api.ts` the FastAPI client. `lib/layout.ts` the journey geometry and mood rules. `lib/scroll-bus.ts` the scroll helpers. `lib/scene-portal.ts` the shared Html portal.
- `types/event.ts` the event and search types.

## Known limits

- The journey is designed for desktop and wide screens. On phone-width screens the three-column grid does not fit, so the layout needs a dedicated narrow-screen version.
- The wordmark uses drei's default font, which loads from a CDN at runtime.
