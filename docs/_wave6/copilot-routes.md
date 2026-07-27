# Copilot Routes — Ready to Apply

Add these routes to `services\bff-api\src\bff_api\routes.py`.

---

## 1. DELETE /v1/copilot/conversations (Delete All)

**Place after** the existing `DELETE /v1/copilot/conversations/{conversation_id}` route.

```python
@app.delete("/v1/copilot/conversations", status_code=204)
async def delete_all_copilot_conversations(request: Request):
    owner = _owner(request)
    _copilot().delete_all_conversations(owner=owner)
```

---

## 2. GET /v1/copilot/glossary/online (Glossary Online Fallback)

**Place after** the existing `GET /v1/copilot/glossary` route.

```python
@app.get("/v1/copilot/glossary/online")
async def copilot_glossary_online(
    request: Request,
    q: str = Query(default="", min_length=1),
    language: str | None = Query(default=None),
):
    return _copilot().glossary_online_fallback(query=q, language=language)
```

---

## Notes

- Both routes delegate to one-liner calls on `CopilotAdapter` (already implemented in `copilot_adapter.py`).
- `_copilot()` and `_owner(request)` are existing helpers in `routes.py`.
- `Query` is already imported from `fastapi` in `routes.py`.
- The delete-all returns 204 (no body), matching the pattern of the single-delete route.
