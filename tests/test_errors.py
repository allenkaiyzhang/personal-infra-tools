from __future__ import annotations

from fastapi_message.errors import MessageError


def test_message_error_dict_does_not_include_payload_or_token():
    error = MessageError("bad", error_code="bad_request", request_id="rid")
    assert error.to_dict() == {"error": {"code": "bad_request", "message": "bad", "request_id": "rid"}}
