"""Append evaluation events without overwriting existing evidence."""

import json
import os
from datetime import datetime, timezone


class EvaluationJournal:
    def __init__(self, path):
        # Exclusive creation prevents accidental reuse of an earlier journal.
        self.handle = path.open("x", encoding="utf-8", newline="\n")

    def append(self, event_type, **fields):
        event = {
            "event_type": event_type,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "fields": fields,
        }
        # Serialize before writing so serialization failures write no fragment.
        line = json.dumps(event, ensure_ascii=False, allow_nan=False)
        self.handle.write(line + "\n")
        self.handle.flush()
        os.fsync(self.handle.fileno())

    def close(self):
        self.handle.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()