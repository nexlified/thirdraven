"""Raven AI provider — Ollama with a rule-based fallback."""

import json
import uuid
from dataclasses import dataclass


@dataclass
class RavenDecision:
    decision: str  # created|merged|flagged|skipped|needs_clarification
    candidate_id: uuid.UUID | None = None
    reasoning: str | None = None
    question: str | None = None  # populated only for needs_clarification


class RavenProvider:
    """Wraps an Ollama model for import merge decisions.

    If *ollama_url* is None the provider falls back to simple rule-based
    logic that never raises ``needs_clarification``.
    """

    def __init__(self, ollama_url: str | None, model: str = "llama3.2") -> None:
        self._url = ollama_url
        self._model = model

    # ── Public API ─────────────────────────────────────────────────────────────

    async def check_merge(
        self,
        record: dict,
        candidates: list[dict],
        user_answer: str | None = None,
    ) -> RavenDecision:
        if self._url:
            return await self._ai_check(record, candidates, user_answer)
        return self._rule_check(record, candidates)

    # ── AI path ────────────────────────────────────────────────────────────────

    async def _ai_check(
        self,
        record: dict,
        candidates: list[dict],
        user_answer: str | None,
    ) -> RavenDecision:
        import ollama

        client = ollama.AsyncClient(host=self._url)

        _nc = "needs_clarification"
        system = (
            "You are a data deduplication assistant. "
            "Given an incoming contact record and a list of existing candidates, "
            "decide what to do. Reply with ONLY a JSON object with these keys:\n"
            f'  "decision": one of "created", "merged", "skipped", "flagged", "{_nc}"\n'
            '  "candidate_id": UUID string of the best match, or null\n'
            '  "reasoning": brief explanation\n'
            '  "question": clarifying question (only when decision is '
            f"{_nc}, else null)\n"
            "Rules:\n"
            "- created: no plausible match exists\n"
            "- merged: confident match (same person)\n"
            "- skipped: exact duplicate, nothing new to add\n"
            "- flagged: multiple weak candidates, human should review later\n"
            f"- {_nc}: one ambiguous candidate; ask the user ONE specific question\n"
            "When user_answer is provided you MUST resolve to a final "
            f"decision (not {_nc})."
        )

        parts: list[str] = [
            f"Incoming record:\n{json.dumps(record, default=str)}",
            f"Existing candidates:\n{json.dumps(candidates, default=str)}",
        ]
        if user_answer:
            parts.append(f"User's answer to your previous question: {user_answer}")

        response = await client.chat(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": "\n\n".join(parts)},
            ],
            format="json",
            options={"temperature": 0},
        )

        raw = response.message.content.strip()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return RavenDecision(decision="created", reasoning=raw)

        cid = data.get("candidate_id")
        return RavenDecision(
            decision=data.get("decision", "created"),
            candidate_id=uuid.UUID(cid) if cid else None,
            reasoning=data.get("reasoning"),
            question=data.get("question"),
        )

    # ── Rule-based fallback ────────────────────────────────────────────────────

    def _rule_check(self, record: dict, candidates: list[dict]) -> RavenDecision:
        """Deterministic fallback — never returns needs_clarification."""
        if not candidates:
            return RavenDecision(decision="created", reasoning="No candidates found.")

        email = (record.get("email") or "").strip().lower()
        phone = (record.get("phone") or "").strip()

        exact: list[dict] = []
        partial: list[dict] = []

        for c in candidates:
            c_email = (c.get("email") or "").strip().lower()
            c_phone = (c.get("phone") or "").strip()
            if (email and c_email and email == c_email) or (
                phone and c_phone and phone == c_phone
            ):
                exact.append(c)
            else:
                partial.append(c)

        if len(exact) == 1:
            cid = exact[0].get("id")
            new_info = any(
                record.get(k) and not exact[0].get(k)
                for k in ("email", "phone", "company", "job_title", "notes")
            )
            if new_info:
                return RavenDecision(
                    decision="merged",
                    candidate_id=uuid.UUID(str(cid)) if cid else None,
                    reasoning="Exact match with new information to merge.",
                )
            return RavenDecision(
                decision="skipped",
                candidate_id=uuid.UUID(str(cid)) if cid else None,
                reasoning="Exact duplicate — nothing new to add.",
            )

        if len(exact) > 1 or (not exact and len(partial) > 1):
            return RavenDecision(
                decision="flagged",
                reasoning="Multiple candidates — deferred for human review.",
            )

        if partial:
            cid = partial[0].get("id")
            return RavenDecision(
                decision="merged",
                candidate_id=uuid.UUID(str(cid)) if cid else None,
                reasoning="Single partial match — merged optimistically.",
            )

        return RavenDecision(decision="created", reasoning="No suitable match.")
