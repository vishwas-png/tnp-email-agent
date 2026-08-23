# TNP Email Agent - Project Notes

## Project Overview
(write what this project does in 2-3 lines)

## Architecture Decisions
(write why you chose LangGraph, FastAPI, Groq, serverless etc)

## Stage 0 - Design
### LangGraph Nodes
(describe each node and what it does)
### Pydantic Schemas
(describe each schema and why it exists)
### DB Schema
(describe tables and relationships)

## Stage 1 - Gmail API Setup
### OAuth2 Flow
(explain access token vs refresh token in your own words)
### token.json vs credentials.json
(explain what each file is and why both exist)
### Scopes
(explain what gmail.readonly scope means and why we chose it)
### Two-Call Gmail API Design
(explain why Gmail splits list and get into two calls)

## Bug Fixes
## Bug Fix: Empty Email Body for HTML Emails

### Problem
Emails with formatted content (bold, links) returned empty body.

### Root Cause
Gmail sends emails in two formats inside nested parts:
- multipart/alternative (container)
    - text/plain
    - text/html

Original code only searched top-level parts, never looked inside 
nested multipart containers.

### Fix
Replaced linear loop with recursive `extract_body()` function that 
searches through nested parts at any depth.

### Priority Order
1. text/plain preferred (clean, no tags)
2. text/html fallback (strip tags with BeautifulSoup)
3. Empty string if neither found

### Concepts Learned
- Email multipart structure
- Recursive functions for tree traversal
- Python tuple unpacking
- Falsy values in Python (empty string = False)
- `.get('key', default)` for safe dictionary access

## Concepts Learned
(running list of new things you understood during build)