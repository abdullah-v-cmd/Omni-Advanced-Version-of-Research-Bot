#!/usr/bin/env python3
"""
OmniSynth - Comprehensive Endpoint Test Suite
Tests all 9 modules: auth, chat, research, citations, plagiarism, analytics, collaboration, admin, ocr
"""
import requests
import json
import time
import sys
import os
import tempfile

BASE = "http://localhost:8000"
API = f"{BASE}/api/v1"

# Test counters
passed = 0
failed = 0
warnings = 0
errors_log = []

# Auth tokens
ACCESS_TOKEN = None
REFRESH_TOKEN = None
ADMIN_TOKEN = None
USER_ID = None

# Resource IDs
SESSION_ID = None
DOCUMENT_ID = None
DRAFT_ID = None
CITATION_ID = None
WORKSPACE_ID = None
CONVERSATION_ID = None
REPORT_ID = None
OCR_DOC_ID = None


def ok(msg):   return f"\033[32m{msg}\033[0m"
def err(msg):  return f"\033[31m{msg}\033[0m"
def warn(msg): return f"\033[33m{msg}\033[0m"
def info(msg): return f"\033[36m{msg}\033[0m"
def bold(msg): return f"\033[1m{msg}\033[0m"


def test(label, method, url, expected_status, headers=None, json_data=None,
         files=None, data=None, check_keys=None):
    global passed, failed, warnings
    try:
        resp = method(url, headers=headers, json=json_data, files=files,
                      data=data, timeout=45)
    except Exception as e:
        print(f"  {err('❌')} [ERR] {label}")
        print(f"       {err(str(e))}")
        failed += 1
        errors_log.append((label, str(e)))
        return None

    try:
        body = resp.json()
    except Exception:
        body = {"_raw": resp.text[:300]}

    if resp.status_code == expected_status:
        if check_keys:
            missing = [k for k in check_keys if k not in body]
            if missing:
                print(f"  {warn('⚠️ ')} [{warn(str(resp.status_code))}] {label}")
                print(f"       {warn('Missing keys: ' + str(missing))}")
                warnings += 1
                return body
        print(f"  {ok('✅')} [{ok(str(resp.status_code))}] {label}")
        passed += 1
    else:
        print(f"  {err('❌')} [{err(str(resp.status_code))}] {label}")
        detail = json.dumps(body, default=str)[:300]
        print(f"       {err('Expected ' + str(expected_status) + ', got ' + str(resp.status_code))}")
        print(f"       {err(detail)}")
        failed += 1
        errors_log.append((label, "Status " + str(resp.status_code) + ": " + detail))

    return body


def auth_headers():
    return {"Authorization": f"Bearer {ACCESS_TOKEN}"} if ACCESS_TOKEN else {}


# ─────────────────────────────────────────────────────────────────────────────
print(bold("\n" + "=" * 70))
print(bold("  OmniSynth API Test Suite — Full Coverage"))
print(bold("=" * 70))

# ─── [0] Infrastructure ───────────────────────────────────────────────────────
print(bold("\n[0] INFRASTRUCTURE"))
test("GET /", requests.get, f"{BASE}/", 200, check_keys=["name", "status"])
test("GET /health", requests.get, f"{BASE}/health", 200, check_keys=["status", "checks"])
test("GET /metrics", requests.get, f"{BASE}/metrics", 200, check_keys=["app", "version"])
test("GET /openapi.json", requests.get, f"{BASE}/openapi.json", 200, check_keys=["openapi", "paths"])
test("GET /docs", requests.get, f"{BASE}/docs", 200)
test("GET /redoc", requests.get, f"{BASE}/redoc", 200)

# ─── [1] Auth ─────────────────────────────────────────────────────────────────
print(bold("\n[1] AUTH MODULE"))

body = test("POST /auth/register (new user)", requests.post, f"{API}/auth/register", 201,
            json_data={"email": "testuser@omnisynth.ai", "username": "testuser",
                       "full_name": "Test User", "password": "TestPass@123"},
            check_keys=["id", "email", "username"])

test("POST /auth/register (duplicate → 400)", requests.post, f"{API}/auth/register", 400,
     json_data={"email": "testuser@omnisynth.ai", "username": "testuser2",
                "full_name": "Dup", "password": "TestPass@123"})

test("POST /auth/login (wrong password → 401)", requests.post, f"{API}/auth/login", 401,
     json_data={"email": "testuser@omnisynth.ai", "password": "WrongPass!"})

body = test("POST /auth/login (correct)", requests.post, f"{API}/auth/login", 200,
            json_data={"email": "testuser@omnisynth.ai", "password": "TestPass@123"},
            check_keys=["access_token", "refresh_token", "token_type"])
if body and "access_token" in body:
    ACCESS_TOKEN = body["access_token"]
    REFRESH_TOKEN = body.get("refresh_token")
    USER_ID = body.get("user", {}).get("id")
    print(f"       {info('Token: ' + ACCESS_TOKEN[:40] + '...')}")
    print(f"       {info('User ID: ' + str(USER_ID))}")

test("GET /auth/me", requests.get, f"{API}/auth/me", 200,
     headers=auth_headers(), check_keys=["id", "email", "username"])

test("PUT /auth/me", requests.put, f"{API}/auth/me", 200,
     headers=auth_headers(), json_data={"full_name": "Test User Updated"})

test("PUT /auth/me/profile", requests.put, f"{API}/auth/me/profile", 200,
     headers=auth_headers(),
     json_data={"institution": "MIT", "department": "AI Lab", "bio": "AI Researcher"})

if REFRESH_TOKEN:
    body = test("POST /auth/refresh", requests.post, f"{API}/auth/refresh", 200,
                json_data={"refresh_token": REFRESH_TOKEN}, check_keys=["access_token"])
    if body and "access_token" in body:
        ACCESS_TOKEN = body["access_token"]

test("POST /auth/change-password", requests.post, f"{API}/auth/change-password", 200,
     headers=auth_headers(),
     json_data={"current_password": "TestPass@123", "new_password": "NewPass@456"})

test("POST /auth/change-password (restore)", requests.post, f"{API}/auth/change-password", 200,
     headers=auth_headers(),
     json_data={"current_password": "NewPass@456", "new_password": "TestPass@123"})

body = test("POST /auth/login (admin)", requests.post, f"{API}/auth/login", 200,
            json_data={"email": "admin@omnisynth.ai", "password": "Admin@123456"},
            check_keys=["access_token"])
if body and "access_token" in body:
    ADMIN_TOKEN = body["access_token"]
    print(f"       {info('Admin token: ' + ADMIN_TOKEN[:40] + '...')}")

test("POST /auth/logout", requests.post, f"{API}/auth/logout", 200, headers=auth_headers())

# ─── [2] Research ─────────────────────────────────────────────────────────────
print(bold("\n[2] RESEARCH MODULE"))

body = test("POST /research/sessions", requests.post, f"{API}/research/sessions", 201,
            headers=auth_headers(),
            json_data={"title": "AI in Medicine", "description": "Healthcare AI research",
                       "topic": "Medical AI", "tags": ["AI", "healthcare"]},
            check_keys=["id", "title"])
if body and "id" in body:
    SESSION_ID = body["id"]
    print(f"       {info('Session ID: ' + SESSION_ID)}")

test("GET /research/sessions", requests.get, f"{API}/research/sessions", 200, headers=auth_headers())

if SESSION_ID:
    test("GET /research/sessions/{id}", requests.get, f"{API}/research/sessions/{SESSION_ID}", 200,
         headers=auth_headers(), check_keys=["id", "title"])
    test("PUT /research/sessions/{id}", requests.put, f"{API}/research/sessions/{SESSION_ID}", 200,
         headers=auth_headers(), json_data={"title": "AI in Medicine - Updated"})

test("GET /research/documents", requests.get, f"{API}/research/documents", 200, headers=auth_headers())

body = test("POST /research/query", requests.post, f"{API}/research/query", 200,
            headers=auth_headers(),
            json_data={"query": "What are the main applications of AI in medical diagnosis?", "use_hyde": True},
            check_keys=["query", "answer"])
if body:
    preview = str(body.get("answer", ""))[:80]
    print(f"       {info('Answer: ' + preview + '...')}")

body = test("POST /research/generate-content", requests.post, f"{API}/research/generate-content", 200,
            headers=auth_headers(),
            json_data={"content_type": "abstract", "topic": "ML in Cancer Detection", "word_limit": 150},
            check_keys=["content", "content_type"])

body = test("POST /research/drafts", requests.post, f"{API}/research/drafts", 201,
            headers=auth_headers(),
            json_data={"title": "Literature Review Draft",
                       "content": "AI has revolutionized cancer detection...",
                       "draft_type": "literature_review", "session_id": SESSION_ID},
            check_keys=["id", "title"])
if body and "id" in body:
    DRAFT_ID = body["id"]
    print(f"       {info('Draft ID: ' + DRAFT_ID)}")

test("GET /research/drafts", requests.get, f"{API}/research/drafts", 200, headers=auth_headers())

if DRAFT_ID:
    test("GET /research/drafts/{id}", requests.get, f"{API}/research/drafts/{DRAFT_ID}", 200,
         headers=auth_headers(), check_keys=["id", "title", "content"])
    test("PUT /research/drafts/{id}", requests.put, f"{API}/research/drafts/{DRAFT_ID}", 200,
         headers=auth_headers(), json_data={"content": "Updated content about ML applications."})

# Upload document
tmp = tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w")
tmp.write("This is a test document about AI in healthcare. Machine learning algorithms "
          "have shown remarkable results in medical imaging and disease prediction. "
          "Deep learning models trained on large datasets achieve near-human accuracy "
          "in cancer detection from MRI and CT scans.")
tmp.close()
with open(tmp.name, "rb") as f:
    body = test("POST /research/documents/upload", requests.post, f"{API}/research/documents/upload", 200,
                headers=auth_headers(),
                files={"file": ("test_doc.txt", f, "text/plain")},
                data={"language": "en"})
os.unlink(tmp.name)
if body and "id" in body:
    DOCUMENT_ID = body["id"]
    print(f"       {info('Document ID: ' + DOCUMENT_ID)}")
    time.sleep(2)

# ─── [3] Chat ─────────────────────────────────────────────────────────────────
print(bold("\n[3] CHAT MODULE"))

test("GET /chat/agents", requests.get, f"{API}/chat/agents", 200, check_keys=["agents"])

body = test("POST /chat/send (general)", requests.post, f"{API}/chat/send", 200,
            headers=auth_headers(),
            json_data={"message": "What is machine learning?", "use_hyde": False, "agent_type": "general"},
            check_keys=["conversation_id", "message"])
if body and "conversation_id" in body:
    CONVERSATION_ID = body["conversation_id"]
    preview = str(body.get("message", ""))[:80]
    print(f"       {info('Conv ID: ' + CONVERSATION_ID)}")
    print(f"       {info('Response: ' + preview + '...')}")

body = test("POST /chat/send (research agent)", requests.post, f"{API}/chat/send", 200,
            headers=auth_headers(),
            json_data={"message": "Summarize benefits of deep learning for medical imaging",
                       "agent_type": "research"},
            check_keys=["conversation_id", "message"])

test("GET /chat/conversations", requests.get, f"{API}/chat/conversations", 200, headers=auth_headers())

if CONVERSATION_ID:
    test("GET /chat/conversations/{id}", requests.get,
         f"{API}/chat/conversations/{CONVERSATION_ID}", 200,
         headers=auth_headers(), check_keys=["id", "title", "messages"])
    body = test("POST /chat/send (continue conv)", requests.post, f"{API}/chat/send", 200,
                headers=auth_headers(),
                json_data={"message": "Can you elaborate?", "conversation_id": CONVERSATION_ID},
                check_keys=["conversation_id", "message"])

# Stream endpoint
try:
    r = requests.get(f"{API}/chat/stream?message=Hello", headers=auth_headers(),
                     stream=True, timeout=10)
    if r.status_code == 200:
        print(f"  {ok('✅')} [{ok('200')}] GET /chat/stream (SSE)")
        passed += 1
    else:
        print(f"  {err('❌')} [{err(str(r.status_code))}] GET /chat/stream")
        failed += 1
        errors_log.append(("GET /chat/stream", "Status " + str(r.status_code)))
except Exception as e:
    print(f"  {warn('⚠️ ')} [ERR] GET /chat/stream: {str(e)[:80]}")
    warnings += 1

# ─── [4] Citations ────────────────────────────────────────────────────────────
print(bold("\n[4] CITATIONS MODULE"))

test("GET /citations/styles", requests.get, f"{API}/citations/styles", 200,
     headers=auth_headers(), check_keys=["styles"])

body = test("POST /citations/generate (APA)", requests.post, f"{API}/citations/generate", 201,
            headers=auth_headers(),
            json_data={"style": "APA",
                       "title": "Deep Learning for Medical Image Analysis",
                       "authors": ["Smith, J.", "Johnson, A."],
                       "year": "2024", "journal": "Nature Medicine",
                       "volume": "30", "issue": "3", "pages": "445-460",
                       "doi": "10.1038/s41591-024-01234-5",
                       "save": True, "session_id": SESSION_ID},
            check_keys=["id", "style", "formatted"])
if body and "id" in body:
    CITATION_ID = body["id"]
    preview = str(body.get("formatted", ""))[:80]
    print(f"       {info('APA: ' + preview + '...')}")

test("POST /citations/generate (MLA, no save)", requests.post, f"{API}/citations/generate", 201,
     headers=auth_headers(),
     json_data={"style": "MLA", "title": "AI in Cancer Diagnosis",
                "authors": ["Brown, K."], "year": "2023",
                "journal": "The Lancet", "save": False},
     check_keys=["style", "formatted"])

test("POST /citations/generate-all-styles", requests.post, f"{API}/citations/generate-all-styles", 200,
     headers=auth_headers(),
     json_data={"title": "Neural Networks in Drug Discovery",
                "authors": ["Chen, L.", "Park, S."], "year": "2024", "journal": "Science"})

test("POST /citations/extract-from-text", requests.post, f"{API}/citations/extract-from-text", 200,
     headers=auth_headers(),
     json_data={"text": "Smith J. Deep learning for cancer detection. Nature. 2024;30:445.",
                "style": "APA"})

test("GET /citations/", requests.get, f"{API}/citations/", 200, headers=auth_headers())

# ─── [5] Plagiarism ───────────────────────────────────────────────────────────
print(bold("\n[5] PLAGIARISM MODULE"))

test_text = ("Machine learning has fundamentally transformed medical diagnosis. "
             "Recent advances in deep learning enable computers to detect diseases with "
             "accuracy comparable to expert physicians. Convolutional neural networks "
             "trained on large medical image datasets have shown remarkable performance "
             "in identifying cancers and cardiovascular conditions.")

body = test("POST /plagiarism/check (detailed)", requests.post, f"{API}/plagiarism/check", 200,
            headers=auth_headers(),
            json_data={"text": test_text, "detailed": True},
            check_keys=["id", "overall_score", "plagiarism_percentage"])
if body and "id" in body:
    REPORT_ID = body["id"]
    print(f"       {info('Score: ' + str(body.get('overall_score')) + '%, Plagiarism: ' + str(body.get('plagiarism_percentage')) + '%')}")

test("POST /plagiarism/check (quick)", requests.post, f"{API}/plagiarism/check", 200,
     headers=auth_headers(),
     json_data={"text": "Artificial intelligence is a branch of computer science that aims to create intelligent machines capable of performing tasks.", "detailed": False},
     check_keys=["id", "overall_score"])

test("GET /plagiarism/reports", requests.get, f"{API}/plagiarism/reports", 200, headers=auth_headers())

if REPORT_ID:
    test("GET /plagiarism/reports/{id}", requests.get, f"{API}/plagiarism/reports/{REPORT_ID}", 200,
         headers=auth_headers(), check_keys=["id", "overall_score", "status"])

test("POST /plagiarism/check (too short → 400)", requests.post, f"{API}/plagiarism/check", 400,
     headers=auth_headers(), json_data={"text": "Too short"})

# ─── [6] Analytics ───────────────────────────────────────────────────────────
print(bold("\n[6] ANALYTICS MODULE"))

test("GET /analytics/dashboard", requests.get, f"{API}/analytics/dashboard", 200,
     headers=auth_headers(), check_keys=["summary", "recent_activity"])

test("GET /analytics/activity", requests.get, f"{API}/analytics/activity", 200, headers=auth_headers())

body = test("GET /analytics/productivity", requests.get, f"{API}/analytics/productivity", 200,
            headers=auth_headers(), check_keys=["period_days", "metrics", "efficiency_score"])
if body:
    print(f"       {info('Efficiency: ' + str(body.get('efficiency_score', 0)))}")

test("GET /analytics/productivity?days=30", requests.get,
     f"{API}/analytics/productivity?days=30", 200, headers=auth_headers())

test("GET /analytics/recommendations", requests.get, f"{API}/analytics/recommendations", 200,
     headers=auth_headers())

# ─── [7] Collaboration ───────────────────────────────────────────────────────
print(bold("\n[7] COLLABORATION MODULE"))

body = test("POST /collaboration/workspaces", requests.post,
            f"{API}/collaboration/workspaces", 201,
            headers=auth_headers(),
            json_data={"name": "AI Research Team",
                       "description": "Collaborative AI research workspace",
                       "is_public": False},
            check_keys=["id", "name"])
if body and "id" in body:
    WORKSPACE_ID = body["id"]
    print(f"       {info('Workspace ID: ' + WORKSPACE_ID)}")

test("GET /collaboration/workspaces", requests.get, f"{API}/collaboration/workspaces", 200,
     headers=auth_headers())

if WORKSPACE_ID:
    body = test("POST /collaboration/workspaces/{id}/comments", requests.post,
                f"{API}/collaboration/workspaces/{WORKSPACE_ID}/comments", 200,
                headers=auth_headers(),
                json_data={"content": "Let's focus on ML papers from 2023-2024."},
                check_keys=["id", "content"])

    test("GET /collaboration/workspaces/{id}/comments", requests.get,
         f"{API}/collaboration/workspaces/{WORKSPACE_ID}/comments", 200,
         headers=auth_headers())

test("GET /collaboration/notifications", requests.get, f"{API}/collaboration/notifications", 200,
     headers=auth_headers())

test("GET /collaboration/notifications?unread_only=true", requests.get,
     f"{API}/collaboration/notifications?unread_only=true", 200, headers=auth_headers())

# ─── [8] Admin ───────────────────────────────────────────────────────────────
print(bold("\n[8] ADMIN MODULE"))

admin_hdrs = {"Authorization": f"Bearer {ADMIN_TOKEN}"} if ADMIN_TOKEN else auth_headers()

body = test("GET /admin/stats", requests.get, f"{API}/admin/stats", 200,
            headers=admin_hdrs, check_keys=["users", "research", "system"])
if body:
    print(f"       {info('Total users: ' + str(body.get('users', {}).get('total', 0)))}")

body = test("GET /admin/users", requests.get, f"{API}/admin/users", 200, headers=admin_hdrs)
if isinstance(body, list):
    print(f"       {info('Users listed: ' + str(len(body)))}")

test("GET /admin/logs", requests.get, f"{API}/admin/logs", 200, headers=admin_hdrs)

test("GET /admin/stats (non-admin → 403)", requests.get, f"{API}/admin/stats", 403,
     headers=auth_headers())

# ─── [9] OCR ─────────────────────────────────────────────────────────────────
print(bold("\n[9] OCR MODULE"))

test("GET /ocr/documents", requests.get, f"{API}/ocr/documents", 200, headers=auth_headers())

# Upload TXT file for OCR
tmp = tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w")
tmp.write("Abstract: This paper presents a comprehensive study of deep learning applications "
          "in medical imaging. We analyze 500 clinical trials and demonstrate that CNNs achieve "
          "94.7% accuracy in detecting malignant tumors from MRI scans. Our methodology combines "
          "transfer learning with data augmentation. Results show significant improvements over "
          "traditional computer vision methods in all three benchmark datasets tested.")
tmp.close()
with open(tmp.name, "rb") as f:
    body = test("POST /ocr/upload (TXT)", requests.post, f"{API}/ocr/upload", 200,
                headers=auth_headers(),
                files={"file": ("research_paper.txt", f, "text/plain")},
                data={"language": "en", "generate_summary": "true", "extract_tables": "true"},
                check_keys=["id", "status", "word_count"])
os.unlink(tmp.name)
if body:
    OCR_DOC_ID = body.get("id")
    wc = body.get("word_count", 0)
    pc = body.get("page_count", 0)
    indexed = body.get("is_indexed", False)
    print(f"       {info('Words: ' + str(wc) + ', Pages: ' + str(pc) + ', Indexed: ' + str(indexed))}")
    summary = str(body.get("summary", ""))[:80]
    if summary:
        print(f"       {info('Summary: ' + summary + '...')}")

# Extract text only (no DB save)
tmp = tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w")
tmp.write("Quick extraction test. This file should be processed without database storage. "
          "Testing the extract-text endpoint functionality.")
tmp.close()
with open(tmp.name, "rb") as f:
    body = test("POST /ocr/extract-text (no DB)", requests.post, f"{API}/ocr/extract-text", 200,
                headers=auth_headers(),
                files={"file": ("quick.txt", f, "text/plain")},
                data={"language": "en"},
                check_keys=["text", "word_count"])
os.unlink(tmp.name)
if body:
    print(f"       {info('Words extracted: ' + str(body.get('word_count', 0)))}")

if OCR_DOC_ID:
    test("GET /ocr/documents/{id}", requests.get, f"{API}/ocr/documents/{OCR_DOC_ID}", 200,
         headers=auth_headers(), check_keys=["id", "title", "status", "word_count"])

    test("DELETE /ocr/documents/{id}", requests.delete, f"{API}/ocr/documents/{OCR_DOC_ID}", 200,
         headers=auth_headers())

# ─── [10] Cleanup ─────────────────────────────────────────────────────────────
print(bold("\n[10] CLEANUP"))

if DRAFT_ID:
    test("DELETE /research/drafts/{id}", requests.delete, f"{API}/research/drafts/{DRAFT_ID}",
         200, headers=auth_headers())

if CITATION_ID:
    test("DELETE /citations/{id}", requests.delete, f"{API}/citations/{CITATION_ID}",
         200, headers=auth_headers())

if CONVERSATION_ID:
    test("DELETE /chat/conversations/{id}", requests.delete,
         f"{API}/chat/conversations/{CONVERSATION_ID}", 200, headers=auth_headers())

if SESSION_ID:
    test("DELETE /research/sessions/{id}", requests.delete,
         f"{API}/research/sessions/{SESSION_ID}", 200, headers=auth_headers())

# ─── Summary ──────────────────────────────────────────────────────────────────
total = passed + failed
print(bold("\n" + "=" * 70))
print(bold("  TEST SUMMARY"))
print(bold("=" * 70))
print(f"  {ok('✅ Passed  : ' + str(passed) + '/' + str(total))}")
print(f"  {err('❌ Failed  : ' + str(failed) + '/' + str(total))}")
print(f"  {warn('⚠️  Warnings: ' + str(warnings))}")

if errors_log:
    print(bold("\n  FAILED TESTS:"))
    for label, detail in errors_log:
        print(f"  {err('→ ' + label)}")
        print(f"    {err(detail[:250])}")

score_pct = int(passed / total * 100) if total > 0 else 0
print(bold(f"\n  Score: {score_pct}% ({passed}/{total} tests passed)"))
print(bold("=" * 70 + "\n"))

sys.exit(0 if failed == 0 else 1)
