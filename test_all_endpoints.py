#!/usr/bin/env python3
"""
OmniSynth Full Endpoint Test Suite — matches actual API contract
Tests ALL API endpoints - no errors allowed
"""

import requests
import json
import sys
import time
import io

BASE_URL = "http://localhost:8000"
PASS = "✅"
FAIL = "❌"

results = []
access_token = None
refresh_token = None
workspace_id = None
session_id = None
document_id = None
draft_id = None
citation_id = None
ocr_doc_id = None
conversation_id = None

def hdr():
    h = {}
    if access_token:
        h["Authorization"] = f"Bearer {access_token}"
    return h

def test(name, method, path, expected_status, **kwargs):
    url = f"{BASE_URL}{path}"
    if "headers" not in kwargs:
        kwargs["headers"] = hdr()
    else:
        kwargs["headers"].update({k: v for k, v in hdr().items() if k not in kwargs["headers"]})
    try:
        resp = getattr(requests, method)(url, timeout=30, **kwargs)
        ok = resp.status_code == expected_status
        symbol = PASS if ok else FAIL
        print(f"{symbol} [{resp.status_code}] {method.upper()} {path}")
        if not ok:
            try:
                print(f"    BODY: {json.dumps(resp.json())[:300]}")
            except Exception:
                print(f"    BODY: {resp.text[:200]}")
        results.append((name, ok, resp.status_code, path))
        return resp if ok else None
    except Exception as e:
        print(f"{FAIL} [ERR] {method.upper()} {path} — {e}")
        results.append((name, False, 0, path))
        return None

def test_any(name, method, path, ok_statuses, **kwargs):
    url = f"{BASE_URL}{path}"
    if "headers" not in kwargs:
        kwargs["headers"] = hdr()
    else:
        kwargs["headers"].update({k: v for k, v in hdr().items() if k not in kwargs["headers"]})
    try:
        resp = getattr(requests, method)(url, timeout=30, **kwargs)
        ok = resp.status_code in ok_statuses
        symbol = PASS if ok else FAIL
        print(f"{symbol} [{resp.status_code}] {method.upper()} {path}")
        if not ok:
            try:
                print(f"    BODY: {json.dumps(resp.json())[:300]}")
            except Exception:
                print(f"    BODY: {resp.text[:200]}")
        results.append((name, ok, resp.status_code, path))
        return resp if ok else None
    except Exception as e:
        print(f"{FAIL} [ERR] {method.upper()} {path} — {e}")
        results.append((name, False, 0, path))
        return None

print("=" * 65)
print("  OmniSynth API — Full Endpoint Test Suite")
print("=" * 65)

# ─────────────────────────────────────────────────────────────────────────────
# 1. HEALTH & DOCS
# ─────────────────────────────────────────────────────────────────────────────
print("\n── HEALTH & DOCS ──")
r = test("health", "get", "/health", 200)
if r:
    d = r.json()
    print(f"    status={d['status']}  groq={d['checks'].get('groq')}  redis={d['checks'].get('redis')}")

test("swagger-ui", "get", "/docs",        200)
test("openapi",    "get", "/openapi.json", 200)

# ─────────────────────────────────────────────────────────────────────────────
# 2. AUTH
# ─────────────────────────────────────────────────────────────────────────────
print("\n── AUTH ──")
ts            = int(time.time())
test_email    = f"tester_{ts}@omnisynth.ai"
test_username = f"tester_{ts}"
test_pass     = "Test@123456"
new_pass      = "NewTest@123456"

# Register (requires email + username + password + full_name)
r = test("auth-register", "post", "/api/v1/auth/register", 201,
    json={"email": test_email, "username": test_username,
          "password": test_pass, "full_name": "Test User"})

# Login
r = test("auth-login", "post", "/api/v1/auth/login", 200,
    json={"email": test_email, "password": test_pass})
if r:
    d = r.json()
    access_token  = d["access_token"]
    refresh_token = d.get("refresh_token")
    print(f"    token_type={d.get('token_type')}  has_refresh={bool(refresh_token)}")

# GET /me
r = test("auth-me", "get", "/api/v1/auth/me", 200)
if r:
    print(f"    email={r.json().get('email')}  role={r.json().get('role')}")

# PUT /me
test("auth-update-me", "put", "/api/v1/auth/me", 200,
    json={"full_name": "Updated Tester"})

# PUT /me/profile
test("auth-update-profile", "put", "/api/v1/auth/me/profile", 200,
    json={"bio": "Testing OmniSynth API", "institution": "OmniSynth Labs"})

# POST /change-password
test("auth-change-password", "post", "/api/v1/auth/change-password", 200,
    json={"current_password": test_pass, "new_password": new_pass})

# Re-login with new password
r = test("auth-relogin", "post", "/api/v1/auth/login", 200,
    json={"email": test_email, "password": new_pass})
if r:
    access_token  = r.json()["access_token"]
    refresh_token = r.json().get("refresh_token")

# POST /refresh
if refresh_token:
    r = test("auth-refresh", "post", "/api/v1/auth/refresh", 200,
        json={"refresh_token": refresh_token})
    if r:
        new_at = r.json().get("access_token")
        if new_at:
            access_token = new_at

# POST /logout
test("auth-logout", "post", "/api/v1/auth/logout", 200)

# Final re-login for remaining tests
r = test("auth-final-login", "post", "/api/v1/auth/login", 200,
    json={"email": test_email, "password": new_pass})
if r:
    access_token = r.json()["access_token"]

# ─────────────────────────────────────────────────────────────────────────────
# 3. CHAT
# ─────────────────────────────────────────────────────────────────────────────
print("\n── CHAT ──")

r = test("chat-agents-list", "get", "/api/v1/chat/agents", 200)
if r:
    agents = r.json()
    count = len(agents.get("agents", agents) if isinstance(agents, dict) else agents)
    print(f"    agents_count={count}")

r = test("chat-send", "post", "/api/v1/chat/send", 200,
    json={"message": "Hello, what is AI?", "agent_type": "general"})
if r:
    d = r.json()
    conversation_id = d.get("conversation_id")
    print(f"    message_len={len(d.get('message', d.get('response','')))}  conv_id={conversation_id}")

r = test("chat-conversations-list", "get", "/api/v1/chat/conversations", 200)
if r:
    print(f"    conversations={len(r.json())}")

if conversation_id:
    r = test("chat-conversation-get", "get",
        f"/api/v1/chat/conversations/{conversation_id}", 200)
    if r:
        msgs = r.json().get("messages", [])
        print(f"    messages_in_conv={len(msgs)}")

    # GET /conversations/{id}/messages  ← newly added endpoint
    r = test("chat-conversation-messages", "get",
        f"/api/v1/chat/conversations/{conversation_id}/messages", 200)
    if r:
        print(f"    message_count={r.json().get('message_count')}")

# SSE stream
r = test("chat-stream", "get",
    "/api/v1/chat/stream?message=Hello+world&agent_type=general", 200)
if r:
    print(f"    content-type={r.headers.get('content-type','')[:40]}")

if conversation_id:
    test("chat-conversation-delete", "delete",
        f"/api/v1/chat/conversations/{conversation_id}", 200)

# ─────────────────────────────────────────────────────────────────────────────
# 4. RESEARCH  ← routes are flat: /research/documents, /research/query, etc.
# ─────────────────────────────────────────────────────────────────────────────
print("\n── RESEARCH ──")

# Sessions
r = test("research-sessions-list", "get", "/api/v1/research/sessions", 200)
if r:
    print(f"    existing sessions={len(r.json())}")

r = test("research-session-create", "post", "/api/v1/research/sessions", 201,
    json={"title": "AI Research Test", "description": "API validation session",
          "topic": "Artificial Intelligence"})
if r:
    session_id = r.json().get("id")
    print(f"    session_id={session_id}")

if session_id:
    test("research-session-get",    "get", f"/api/v1/research/sessions/{session_id}", 200)
    test("research-session-update", "put", f"/api/v1/research/sessions/{session_id}", 200,
        json={"title": "Updated AI Research"})

# Documents — flat routes, session_id passed as query param
r = test("research-docs-list", "get", "/api/v1/research/documents", 200)
if r:
    print(f"    existing docs={len(r.json())}")

# Upload document via /research/documents/upload (file upload)
pdf_content = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R/Resources<</Font<</F1<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>>>>>>>endobj
4 0 obj<</Length 58>>
stream
BT /F1 12 Tf 100 700 Td (OmniSynth Research Document Test) Tj ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000274 00000 n
trailer<</Size 5/Root 1 0 R>>
startxref
382
%%EOF"""

# Use session_id as form field for document upload
form_data = {"language": "en"}
if session_id:
    form_data["session_id"] = str(session_id)

r = test_any("research-doc-upload", "post", "/api/v1/research/documents/upload", [200, 201],
    files={"file": ("research_test.pdf", io.BytesIO(pdf_content), "application/pdf")},
    data=form_data)
if r:
    document_id = r.json().get("id")
    print(f"    document_id={document_id}  status={r.json().get('status')}")

if document_id:
    test("research-doc-get", "get", f"/api/v1/research/documents/{document_id}", 200)

# AI Query (flat route: /research/query)
r = test("research-query", "post", "/api/v1/research/query", 200,
    json={"query": "What is machine learning?", "use_hyde": False})
if r:
    print(f"    answer_len={len(r.json().get('answer',''))}")

# HyDE Query
r = test("research-hyde-query", "post", "/api/v1/research/query", 200,
    json={"query": "Explain transformer neural networks", "use_hyde": True})
if r:
    d = r.json()
    print(f"    HyDE answer_len={len(d.get('answer',''))}")

# Generate content (flat route: /research/generate-content)
r = test("research-generate-content", "post", "/api/v1/research/generate-content", 200,
    json={"prompt": "Brief intro about AI in research", "content_type": "introduction",
          "topic": "Artificial Intelligence in Research"})
if r:
    print(f"    generated_len={len(r.json().get('content',''))}")

# Drafts (flat routes)
r = test("research-drafts-list", "get", "/api/v1/research/drafts", 200)
if r:
    print(f"    existing drafts={len(r.json())}")

r = test("research-draft-create", "post", "/api/v1/research/drafts", 201,
    json={"title": "Test Draft", "content": "This is a test draft about AI research.",
          "draft_type": "outline", "session_id": session_id})
if r:
    draft_id = r.json().get("id")
    print(f"    draft_id={draft_id}")

if draft_id:
    test("research-draft-get",    "get",    f"/api/v1/research/drafts/{draft_id}", 200)
    test("research-draft-update", "put",    f"/api/v1/research/drafts/{draft_id}", 200,
        json={"title": "Updated Draft", "content": "Updated AI research draft."})
    test("research-draft-delete", "delete", f"/api/v1/research/drafts/{draft_id}", 200)

if session_id:
    test("research-session-delete", "delete", f"/api/v1/research/sessions/{session_id}", 200)

# ─────────────────────────────────────────────────────────────────────────────
# 5. CITATIONS
# ─────────────────────────────────────────────────────────────────────────────
print("\n── CITATIONS ──")

r = test("citation-styles", "get", "/api/v1/citations/styles", 200)
if r:
    styles = r.json().get("styles", [])
    print(f"    styles count={len(styles)}")

r = test("citations-list", "get", "/api/v1/citations/", 200)
if r:
    print(f"    existing citations={len(r.json())}")

r = test("citation-generate", "post", "/api/v1/citations/generate", 201,
    json={
        "title": "Deep Learning for NLP",
        "authors": ["LeCun, Y.", "Bengio, Y.", "Hinton, G."],
        "year": 2015,
        "journal": "Nature",
        "volume": "521",
        "pages": "436-444",
        "doi": "10.1038/nature14539",
        "citation_style": "APA",
        "source_type": "journal_article",
    })
if r:
    citation_id = r.json().get("id")
    print(f"    citation_id={citation_id}  style=APA")

r = test("citation-all-styles", "post", "/api/v1/citations/generate-all-styles", 200,
    json={"title": "Machine Learning Systems", "authors": ["Smith, J."],
          "year": 2023, "source_type": "book"})
if r:
    print(f"    all-styles={list(r.json().keys())[:4]}")

r = test("citation-extract-from-text", "post", "/api/v1/citations/extract-from-text", 200,
    json={"text": "LeCun, Y., Bengio, Y., & Hinton, G. (2015). Deep learning. Nature, 521(7553), 436-444."})
if r:
    print(f"    extracted fields={list(r.json().keys())}")

if citation_id:
    # GET /{id}  ← newly added endpoint
    r = test("citation-get",    "get",    f"/api/v1/citations/{citation_id}", 200)
    test("citation-delete", "delete", f"/api/v1/citations/{citation_id}", 200)

# ─────────────────────────────────────────────────────────────────────────────
# 6. PLAGIARISM
# ─────────────────────────────────────────────────────────────────────────────
print("\n── PLAGIARISM ──")

r = test("plagiarism-check", "post", "/api/v1/plagiarism/check", 200,
    json={
        "text": "Artificial intelligence is the simulation of human intelligence processes by machines, "
                "especially computer systems, including expert systems, natural language processing, "
                "speech recognition and machine vision.",
        "title": "AI Overview Test",
        "threshold": 0.8,
    })
if r:
    d = r.json()
    print(f"    similarity={d.get('similarity_score')}  plagiarized={d.get('is_plagiarized')}")

r = test("plagiarism-reports", "get", "/api/v1/plagiarism/reports", 200)
if r:
    print(f"    reports={len(r.json())}")

# ─────────────────────────────────────────────────────────────────────────────
# 7. OCR
# ─────────────────────────────────────────────────────────────────────────────
print("\n── OCR ──")

r = test("ocr-docs-list", "get", "/api/v1/ocr/documents", 200)
if r:
    print(f"    ocr_docs={len(r.json())}")

ocr_pdf = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R/Resources<</Font<</F1<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>>>>>>>endobj
4 0 obj<</Length 52>>
stream
BT /F1 12 Tf 100 700 Td (OmniSynth OCR Test Page) Tj ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000274 00000 n
trailer<</Size 5/Root 1 0 R>>
startxref
376
%%EOF"""

r = test_any("ocr-upload", "post", "/api/v1/ocr/upload", [200, 201],
    files={"file": ("test_ocr.pdf", io.BytesIO(ocr_pdf), "application/pdf")},
    data={"language": "eng"})
if r:
    d = r.json()
    ocr_doc_id = d.get("document_id") or d.get("id")
    print(f"    ocr_doc_id={ocr_doc_id}  text_len={len(d.get('extracted_text',''))}")

# ─────────────────────────────────────────────────────────────────────────────
# 8. COLLABORATION
# ─────────────────────────────────────────────────────────────────────────────
print("\n── COLLABORATION ──")

r = test("collab-list", "get", "/api/v1/collaboration/workspaces", 200)
if r:
    print(f"    workspaces={len(r.json())}")

r = test("collab-create", "post", "/api/v1/collaboration/workspaces", 201,
    json={"name": "Test Workspace", "description": "API test workspace", "is_public": False})
if r:
    workspace_id = r.json().get("id")
    print(f"    workspace_id={workspace_id}")

if workspace_id:
    r = test("collab-get", "get", f"/api/v1/collaboration/workspaces/{workspace_id}", 200)
    if r:
        print(f"    name={r.json().get('name')}  members={r.json().get('member_count')}")

    test("collab-update", "put", f"/api/v1/collaboration/workspaces/{workspace_id}", 200,
        json={"name": "Updated Workspace", "description": "Updated description"})

    # GET members  ← newly added endpoint
    r = test("collab-members-get", "get",
        f"/api/v1/collaboration/workspaces/{workspace_id}/members", 200)
    if r:
        print(f"    members={len(r.json())}")

    # GET conversations  ← newly added endpoint
    r = test("collab-conversations", "get",
        f"/api/v1/collaboration/workspaces/{workspace_id}/conversations", 200)
    if r:
        print(f"    workspace_conversations={len(r.json())}")

    # Comments
    r = test_any("collab-comment-add", "post",
        f"/api/v1/collaboration/workspaces/{workspace_id}/comments", [200, 201],
        json={"content": "Test comment from API test suite"})

    r = test("collab-comments-get", "get",
        f"/api/v1/collaboration/workspaces/{workspace_id}/comments", 200)
    if r:
        print(f"    comments={len(r.json())}")

    # Notifications
    r = test("collab-notifications", "get", "/api/v1/collaboration/notifications", 200)
    if r:
        print(f"    notifications={len(r.json())}")

    test("collab-delete", "delete",
        f"/api/v1/collaboration/workspaces/{workspace_id}", 200)

# ─────────────────────────────────────────────────────────────────────────────
# 9. ANALYTICS
# ─────────────────────────────────────────────────────────────────────────────
print("\n── ANALYTICS ──")

r = test("analytics-dashboard", "get", "/api/v1/analytics/dashboard", 200)
if r:
    d = r.json()
    summary = d.get("summary", {})
    print(f"    keys={list(d.keys())}  productivity={summary.get('productivity_score')}")

r = test("analytics-activity", "get", "/api/v1/analytics/activity", 200)
if r:
    print(f"    activity_entries={len(r.json())}")

r = test("analytics-productivity", "get", "/api/v1/analytics/productivity", 200)
if r:
    d = r.json()
    print(f"    efficiency={d.get('efficiency_score')}  period={d.get('period_days')}d")

r = test("analytics-recommendations", "get", "/api/v1/analytics/recommendations", 200)
if r:
    print(f"    recommendations={len(r.json())}")

# ─────────────────────────────────────────────────────────────────────────────
# 10. ADMIN  (superuser: admin@omnisynth.ai / Admin@123456)
# ─────────────────────────────────────────────────────────────────────────────
print("\n── ADMIN ──")

r_admin = requests.post(f"{BASE_URL}/api/v1/auth/login",
    json={"email": "admin@omnisynth.ai", "password": "Admin@123456"}, timeout=15)
if r_admin.status_code == 200:
    admin_token = r_admin.json()["access_token"]
    print(f"{PASS} [200] Admin login OK")
    results.append(("admin-login", True, 200, "/api/v1/auth/login"))
    ah = {"Authorization": f"Bearer {admin_token}"}

    for endpoint_name, path in [
        ("admin-users", "/api/v1/admin/users"),
        ("admin-stats", "/api/v1/admin/stats"),
        ("admin-logs",  "/api/v1/admin/logs"),
    ]:
        r = requests.get(f"{BASE_URL}{path}", headers=ah, timeout=15)
        ok = r.status_code == 200
        print(f"{'✅' if ok else '❌'} [{r.status_code}] GET {path}")
        results.append((endpoint_name, ok, r.status_code, path))
        if ok:
            body = r.json()
            if isinstance(body, list):
                print(f"    count={len(body)}")
            elif isinstance(body, dict):
                print(f"    keys={list(body.keys())[:5]}")
else:
    print(f"{FAIL} [{r_admin.status_code}] Admin login FAILED — {r_admin.text[:100]}")
    results.append(("admin-login", False, r_admin.status_code, "/api/v1/auth/login"))

# ─────────────────────────────────────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("  FINAL TEST RESULTS")
print("=" * 65)
passed = [r for r in results if r[1]]
failed = [r for r in results if not r[1]]
total  = len(results)
pct    = 100 * len(passed) // total if total else 0
print(f"\n  Total  : {total}")
print(f"  Passed : {len(passed)} ✅")
print(f"  Failed : {len(failed)} {'❌' if failed else '✅'}")
print(f"  Score  : {len(passed)}/{total}  ({pct}%)")

if failed:
    print(f"\n  ─── FAILED TESTS ───")
    for name, ok, status, path in failed:
        print(f"    ❌ [{status}] {name}: {path}")
else:
    print(f"\n  🎉 ALL {total} TESTS PASSED — 100% SUCCESS!")

print("=" * 65)
sys.exit(0 if not failed else 1)
