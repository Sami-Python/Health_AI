# Implementation Plan: AI Chat with Guardrails

> [!NOTE]
> **TOTEUTETTU.** Tämä suunnitelma on arkistoitu. Ominaisuus on valmis ja tuotannossa (Phase 11 web, Phase 15 mobiili). Alla alkuperäinen suunnitelma viitteeksi – toteutus eroaa hieman yksityiskohdista.

## Alkuperäinen tavoite
Interaktiivinen AI Chat -käyttöliittymä **Gemini Flash** -mallilla (`gemini-flash-latest`). AI toimii henkilökohtaisena valmentajana, joka tuntee käyttäjän terveysdatan mutta on rajattu tiukasti terveys- ja urheiluaiheisiin (Guardrails).

## Toteutustiedot
> [!IMPORTANT]
> **Endpoint:** `POST /ai/chat` (ei `/chat` kuten alkuperäisessä suunnitelmassa)  
> **Malli:** `gemini-flash-latest` (ei `gemini-1.5-flash`)  
> **Backend:** `ai_chat_manager.py` (ei `chat_routes.py`)  
> **Rate limit:** 10/min (ei 30/min)

## Proposed Changes

### Backend (`backend/`)

#### [NEW] `chat_routes.py`
- `POST /chat` endpoint with request body `{ message: string }`
- Uses `verify_token` middleware for authentication
- System prompt includes user's latest health data (readiness, goals)
- Maintains session-based conversation history (in-memory, per user)
- Guardrails: System prompt instructs model to decline non-health topics
- Rate limiting: 30 messages/minute

#### [MODIFY] `main.py`
- Register chat router: `app.include_router(chat_router)`

### Frontend (`frontend/src/`)

#### [NEW] `app/chat/page.tsx`
- Full-page chat interface (like ChatGPT/Gemini)
- Message bubbles (user = right/blue, AI = left/gray)
- Input field with send button
- Auto-scroll to latest message
- Loading indicator while AI responds
- Mobile-responsive design

#### [MODIFY] `components/Sidebar.tsx`
- Add "AI Chat" navigation link with chat icon

## Verification Plan

### Automated Tests
- Backend: Unit test for chat endpoint (mocked Gemini response)
- Frontend: E2E test for chat page load and message sending

### Manual Verification
- Test chat with health questions (should answer)
- Test chat with non-health questions (should politely decline)
- Test rate limiting (30+ messages in 1 minute)
