import json
from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, field_validator

class AuditEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    appointment_id: int
    actor_id: str
    actor_role: str
    action: str
    before_state: Optional[Dict[str, Any]] = None
    after_state: Optional[Dict[str, Any]] = None
    created_at: datetime

    @field_validator("before_state", "after_state", mode="before")
    @classmethod
    def parse_json_state(cls, v: Any) -> Optional[Dict[str, Any]]:
        if v is None:
            return None
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return None
        if isinstance(v, dict):
            return v
        return None
