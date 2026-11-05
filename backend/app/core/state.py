"""Process-wide runtime state shared between startup and the API routes."""

warmup_state: dict = {"status": "pending", "records": None, "error": None}
