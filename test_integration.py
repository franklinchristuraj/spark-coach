#!/usr/bin/env python3
"""
SPARK Coach — Full Integration Test (FRA-41)
Tests the complete learning cycle: briefing → quiz → nudge → chat → stats

Usage:
    # Against local backend
    python test_integration.py

    # Against production
    SPARK_COACH_API_URL=https://coach-api.ziksaka.com python test_integration.py

    # With a specific resource path from the vault
    python test_integration.py --resource "04_resources/llmops-fundamentals.md"
"""
import os
import sys
import time
import argparse
import requests
from typing import Any, Dict, List, Optional

# ─────────────────────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────────────────────

API_BASE = os.getenv("SPARK_COACH_API_URL", "http://localhost:8080")
PASSWORD = os.getenv("SPARK_COACH_PASSWORD", "")

# ─────────────────────────────────────────────────────────────────────────────
# Terminal colours
# ─────────────────────────────────────────────────────────────────────────────

GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"

passed: List[str] = []
failed: List[str] = []


def ok(label: str, detail: str = ""):
    passed.append(label)
    suffix = f"  {DIM}{detail}{RESET}" if detail else ""
    print(f"  {GREEN}✓{RESET} {label}{suffix}")


def fail(label: str, detail: str = ""):
    failed.append(label)
    suffix = f"  {DIM}{detail}{RESET}" if detail else ""
    print(f"  {RED}✗{RESET} {label}{suffix}")


def section(title: str):
    print(f"\n{BOLD}{CYAN}── {title}{RESET}")


def info(msg: str):
    print(f"    {DIM}{msg}{RESET}")


# ─────────────────────────────────────────────────────────────────────────────
# HTTP helpers
# ─────────────────────────────────────────────────────────────────────────────

def get(path: str, token: str = None, params: Dict = None, timeout: int = 90) -> Optional[Dict]:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        r = requests.get(f"{API_BASE}{path}", headers=headers, params=params, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except requests.HTTPError as e:
        return {"_error": str(e), "_body": e.response.text if e.response else ""}
    except requests.RequestException as e:
        return {"_error": str(e)}


def post(path: str, body: Dict, token: str = None, timeout: int = 60) -> Optional[Dict]:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        r = requests.post(f"{API_BASE}{path}", headers=headers, json=body, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except requests.HTTPError as e:
        return {"_error": str(e), "_body": e.response.text if e.response else ""}
    except requests.RequestException as e:
        return {"_error": str(e)}


def is_ok(resp: Optional[Dict]) -> bool:
    return resp is not None and "_error" not in resp


# ─────────────────────────────────────────────────────────────────────────────
# Test groups
# ─────────────────────────────────────────────────────────────────────────────

def test_health() -> bool:
    section("1. Health Check")
    resp = get("/health")
    if is_ok(resp) and resp.get("status") == "healthy":
        ok("GET /health", f"v{resp.get('version', '?')}")
        return True
    fail("GET /health", resp.get("_error", "unexpected response") if resp else "no response")
    return False


def test_login() -> Optional[str]:
    section("2. Authentication")

    if not PASSWORD:
        fail("POST /api/v1/auth/login", "SPARK_COACH_PASSWORD env var not set")
        info("Set it: export SPARK_COACH_PASSWORD=your_password")
        return None

    resp = post("/api/v1/auth/login", {"password": PASSWORD})
    if is_ok(resp) and resp.get("access_token"):
        token = resp["access_token"]
        ok("POST /api/v1/auth/login", f"token: {token[:20]}…")
        return token

    fail("POST /api/v1/auth/login", resp.get("_body", resp.get("_error", "")) if resp else "no response")
    return None


def test_briefing(token: str) -> Optional[str]:
    """Returns a resource path from reviews_due, if any."""
    section("3. Morning Briefing")

    # Quick briefing (no LLM)
    resp = get("/api/v1/briefing/quick", token)
    if is_ok(resp) and resp.get("status") == "success":
        qb = resp.get("quick_briefing", {})
        ok("GET /api/v1/briefing/quick",
           f"reviews_due={qb.get('reviews_due_count', 0)}  at_risk={qb.get('at_risk_count', 0)}")
    else:
        fail("GET /api/v1/briefing/quick", resp.get("_error", "") if resp else "no response")

    # Full briefing (LLM — free tier can take 30-60s)
    info("Running full briefing (LLM)… this may take up to 60s")
    resp = get("/api/v1/briefing", token, timeout=120)
    if is_ok(resp) and resp.get("status") == "success":
        briefing = resp.get("briefing", {})
        reviews = briefing.get("reviews_due", [])
        ok("GET /api/v1/briefing", f"greeting present={bool(briefing.get('greeting'))}  reviews_due={len(reviews)}")

        # Return first reviewable resource path for quiz test
        if reviews:
            resource_path = reviews[0].get("resource_path") or reviews[0].get("path")
            if resource_path:
                info(f"Using resource for quiz: {resource_path}")
                return resource_path
    else:
        fail("GET /api/v1/briefing", resp.get("_body", resp.get("_error", "")) if resp else "no response")

    return None


def test_mcp(token: str):
    section("4. MCP Vault Connectivity")
    resp = get("/api/v1/test-mcp", token)
    if is_ok(resp) and resp.get("status") == "success":
        ok("GET /api/v1/test-mcp",
           f"notes_found={resp.get('total_notes_found', 0)}")
    else:
        fail("GET /api/v1/test-mcp", resp.get("_body", resp.get("_error", "")) if resp else "no response")

    # Keyword search
    resp = get("/api/v1/mcp/search", token, params={"query": "learning_path"})
    if is_ok(resp) and resp.get("status") == "success":
        ok("GET /api/v1/mcp/search", f"results={resp.get('results_count', 0)}")
    else:
        fail("GET /api/v1/mcp/search", resp.get("_error", "") if resp else "no response")


def test_quiz(token: str, resource_path: str):
    section("5. Quiz Flow")

    # Start quiz
    resp = post("/api/v1/quiz/start", {
        "resource_path": resource_path,
        "num_questions": 2,
        "difficulty": "medium"
    }, token, timeout=60)

    if not is_ok(resp) or not resp.get("session_id"):
        fail("POST /api/v1/quiz/start", resp.get("_body", resp.get("_error", "")) if resp else "no response")
        return

    session_id = resp["session_id"]
    total = resp.get("total_questions", 2)
    first_q = resp.get("current_question", {})
    ok("POST /api/v1/quiz/start",
       f"session={session_id[:8]}…  questions={total}  type={first_q.get('type','?')}")
    info(f"Q1: {first_q.get('question','')[:80]}…")

    # Answer all questions
    answers = [
        "This concept involves applying knowledge systematically to real problems, ensuring understanding through practice.",
        "The key principle connects to broader patterns of how information is structured and retained over time.",
    ]

    quiz_complete = False
    for i in range(1, total + 1):
        if i > 1:
            time.sleep(15)  # free-tier RPM buffer between LLM scoring calls
        answer = answers[i - 1] if i <= len(answers) else "Applying this concept requires understanding the core principles."
        resp = post("/api/v1/quiz/answer", {
            "session_id": session_id,
            "question_index": i,
            "answer": answer
        }, token, timeout=120)

        if not is_ok(resp):
            fail(f"POST /api/v1/quiz/answer Q{i}", resp.get("_body", resp.get("_error", "")) if resp else "no response")
            continue

        correct = resp.get("correct")
        score = resp.get("score", 0)
        quiz_complete = resp.get("quiz_complete", False)
        label = f"Q{i} answered  correct={correct}  score={score}"

        if quiz_complete:
            final_score = resp.get("final_score", score)
            retention_updated = resp.get("retention_updated", False)
            label += f"  final={final_score}  retention_updated={retention_updated}"

        ok(f"POST /api/v1/quiz/answer Q{i}", label)

    # Get session status
    resp = get(f"/api/v1/quiz/session/{session_id}", token)
    if is_ok(resp):
        session = resp.get("session", {})
        ok("GET /api/v1/quiz/session/{id}",
           f"status={session.get('status','?')}  score={session.get('score','?')}")
    else:
        fail("GET /api/v1/quiz/session/{id}", resp.get("_error", "") if resp else "no response")


def test_nudges(token: str):
    section("6. Abandonment Nudges")

    # Manually trigger abandonment check
    info("Triggering abandonment check…")
    resp = post("/api/v1/nudges/run-check", {}, token, timeout=60)
    if is_ok(resp):
        at_risk = resp.get("at_risk_count", 0)
        nudges_created = resp.get("nudges_created", 0)
        ok("POST /api/v1/nudges/run-check", f"at_risk={at_risk}  nudges_created={nudges_created}")
    else:
        fail("POST /api/v1/nudges/run-check", resp.get("_body", resp.get("_error", "")) if resp else "no response")

    # Get pending nudges
    resp = get("/api/v1/nudges", token)
    if is_ok(resp) and resp.get("status") == "success":
        nudges = resp.get("nudges", [])
        ok("GET /api/v1/nudges", f"pending={len(nudges)}")

        # Mark them delivered if any
        if nudges:
            nudge_ids = [n["id"] for n in nudges if "id" in n]
            if nudge_ids:
                resp2 = post("/api/v1/nudges/mark-delivered", {"nudge_ids": nudge_ids}, token)
                if is_ok(resp2):
                    ok("POST /api/v1/nudges/mark-delivered", f"marked={resp2.get('marked', 0)}")
                else:
                    fail("POST /api/v1/nudges/mark-delivered", resp2.get("_error", "") if resp2 else "no response")
    else:
        fail("GET /api/v1/nudges", resp.get("_error", "") if resp else "no response")


def test_chat(token: str):
    section("7. Coaching Chat (Rafiki)")

    # Hello endpoint (no LLM)
    resp = get("/api/v1/chat/hello", token)
    if is_ok(resp) and resp.get("available"):
        ok("GET /api/v1/chat/hello", resp.get("message", "")[:60])
    else:
        fail("GET /api/v1/chat/hello", resp.get("_error", "") if resp else "no response")

    # Coaching message (LLM)
    info("Sending chat message to Rafiki (LLM)…")
    resp = post("/api/v1/chat", {
        "message": "I feel like I understand the theory of LLMOps but struggle to apply it. Where should I focus?",
        "include_vault_context": True
    }, token, timeout=120)

    if is_ok(resp) and resp.get("status") == "success":
        message = resp.get("message", "")
        sources = resp.get("sources") or []
        ok("POST /api/v1/chat", f"response_len={len(message)}  sources={len(sources)}")
        if message:
            info(f"Rafiki: {message[:120]}…")
    else:
        fail("POST /api/v1/chat", resp.get("_body", resp.get("_error", "")) if resp else "no response")


def test_voice(token: str):
    section("8. Voice Router")

    test_cases = [
        ("new_seed intent", "I just had an insight: LLM evaluation should always include human judges for edge cases"),
        ("question intent", "What are the key principles of LLMOps production observability?"),
    ]

    for label, transcription in test_cases:
        resp = post("/api/v1/voice/process", {"transcription": transcription}, token, timeout=120)
        if is_ok(resp) and resp.get("status") == "success":
            intent = resp.get("intent", "?")
            ok(f"POST /api/v1/voice/process ({label})",
               f"intent={intent}  confidence={resp.get('confidence', 0):.2f}")
        else:
            fail(f"POST /api/v1/voice/process ({label})",
                 resp.get("_body", resp.get("_error", "")) if resp else "no response")


def test_stats(token: str):
    section("9. Stats & Dashboard")

    resp = get("/api/v1/stats/dashboard", token)
    if is_ok(resp) and resp.get("status") == "success":
        streaks = resp.get("streaks", {})
        hours = resp.get("learning_hours", {})
        quizzes = resp.get("quizzes", {})
        ok("GET /api/v1/stats/dashboard",
           f"streak={streaks.get('current_days',0)}d  hours={hours.get('this_week',0)}h  quizzes={quizzes.get('completed_this_week',0)}")
    else:
        fail("GET /api/v1/stats/dashboard", resp.get("_body", resp.get("_error", "")) if resp else "no response")

    resp = get("/api/v1/stats/streak", token)
    if is_ok(resp) and resp.get("status") == "success":
        ok("GET /api/v1/stats/streak",
           f"current={resp.get('current_days',0)}  longest={resp.get('longest_ever',0)}")
    else:
        fail("GET /api/v1/stats/streak", resp.get("_error", "") if resp else "no response")

    resp = get("/api/v1/stats/weekly-summary", token)
    if is_ok(resp) and resp.get("status") == "success":
        ok("GET /api/v1/stats/weekly-summary",
           f"quizzes={resp.get('quizzes_completed',0)}  on_track={resp.get('on_track',False)}")
    else:
        fail("GET /api/v1/stats/weekly-summary", resp.get("_error", "") if resp else "no response")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="SPARK Coach integration test")
    parser.add_argument("--resource", default=None,
                        help="Vault resource path for quiz (e.g. 04_resources/llmops-fundamentals.md)")
    parser.add_argument("--skip-llm", action="store_true",
                        help="Skip tests that require LLM (briefing, chat, voice)")
    args = parser.parse_args()

    print(f"\n{BOLD}SPARK Coach — Integration Test{RESET}  {DIM}{API_BASE}{RESET}")
    print("─" * 60)

    # 1. Health (no auth required)
    if not test_health():
        print(f"\n{RED}{BOLD}Backend unreachable. Start it first:{RESET}")
        print(f"  cd backend && python -m uvicorn main:app --host 0.0.0.0 --port 8080\n")
        sys.exit(1)

    # 2. Auth
    token = test_login()
    if not token:
        print(f"\n{RED}{BOLD}Authentication failed — cannot continue.{RESET}\n")
        sys.exit(1)

    # 3. Briefing → get resource path for quiz
    resource_path = args.resource
    if not args.skip_llm:
        briefing_resource = test_briefing(token)
        if not resource_path and briefing_resource:
            resource_path = briefing_resource
    else:
        section("3. Morning Briefing")
        info("Skipped (--skip-llm)")

    # 4. MCP connectivity
    test_mcp(token)

    # 5. Quiz (needs a resource path)
    if resource_path:
        test_quiz(token, resource_path)
    else:
        section("5. Quiz Flow")
        info("Skipped — no resource path found in briefing. Pass --resource to run.")

    # 6. Nudges
    test_nudges(token)

    # 7. Chat
    if not args.skip_llm:
        test_chat(token)
    else:
        section("7. Coaching Chat")
        info("Skipped (--skip-llm)")

    # 8. Voice
    if not args.skip_llm:
        test_voice(token)
    else:
        section("8. Voice Router")
        info("Skipped (--skip-llm)")

    # 9. Stats
    test_stats(token)

    # ── Summary ──────────────────────────────────────────────────────────────
    total = len(passed) + len(failed)
    print(f"\n{'─' * 60}")
    print(f"{BOLD}Results: {GREEN}{len(passed)} passed{RESET}  "
          f"{RED}{len(failed)} failed{RESET}  "
          f"{DIM}({total} total){RESET}")

    if failed:
        print(f"\n{RED}Failed checks:{RESET}")
        for f in failed:
            print(f"  • {f}")
        print()
        sys.exit(1)
    else:
        print(f"\n{GREEN}{BOLD}All checks passed!{RESET}\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
