# Implementation Plan: AI Chat with Guardrails 💬🤖

## Goal
Implement an interactive AI Chat interface using **Gemini 1.5 Flash**. The AI should act as a personal coach, aware of the user's health data, but strictly limited to health/fitness topics (Guardrails).

## User Review Required
> [!IMPORTANT]
> **Privacy:** Chat history will not be persisted permanently in database for MVP (session-based) to simplify GDPR.
> **Model:** Using `gemini-1.5-flash` for speed and cost-efficiency.

## Proposed Changes

### Backend (`backend/`)

#### [NEW] `backend/ai_chat_manager.py`
- Class `AIChatManager` handles interacting with Google GenAI SDK.
- **System Prompt:** "You are an elite endurance coach..."
- **Guardrails:** Explicit instructions to refuse non-health topics.
- **Context Injection:** Fetches recent health data (Sleep, Body Battery, Load) and injects it into the system prompt.

#### [MODIFY] `backend/main.py`
- Add POST `/ai/chat` endpoint.
- Rate limiting: 10 messages/minute.
- Input: `{ "message": "...", "history": [...] }`
- Output: `{ "reply": "..." }`
- Uses `AIChatManager` to process the request.

### Frontend (`frontend/`)

#### [NEW] `components/ChatInterface.tsx`
- Floating Action Button (FAB) or dedicated tab.
- Chat window with "User" and "Coach" bubbles.
- Typing indicator.
- Auto-scroll to bottom.

#### [MODIFY] `app/dashboard/page.tsx`
- Integrate `ChatInterface` into the layout.

## System Prompt Strategy (The Guardrails)

```text
ROLE: You are Health AI, an elite personal endurance coach.
CONTEXT:
- User's recent stats: [Sleep Score: 85, Body Battery: 90, weekly Load: 450]
- User's goals: [Marathon in 3 months]

RULES:
1. ONLY answer questions about training, recovery, sleep, nutrition, and physiology.
2. IF the user asks about politics, coding, weather, or general knowledge -> REFUSE politiely: "I focus only on your training and health."
3. DO NOT give medical diagnoses.
4. Be concise and motivating.
```

## Verification Plan
1. **Manual Test (Guardrails):** Ask "Who is the president?" -> Expect refusal.
2. **Manual Test (Context):** Ask "Can I train hard today?" -> Expect answer based on Body Battery.
3. **Manual Test (Latency):** Ensure response time is < 2 seconds.
