import json
from urllib.request import Request, urlopen

from .models import TrafficResult


class DittoClient:
    """Minimal Eclipse Ditto HTTP adapter for junction twin features."""

    def __init__(self, base_url: str, username: str = "ditto", password: str = "ditto", policy_id: str = "traffic:policy") -> None:
        self.base_url = base_url.rstrip("/")
        self.auth = (username, password)
        self.policy_id = policy_id

    def update_junction(self, result: TrafficResult) -> None:
        junction_id = result.reading.junction_id
        payload = json.dumps(self._thing_payload(junction_id, result.to_dict())).encode()
        self._request("PUT", f"/api/2/things/traffic:{junction_id}", payload)

    def create_junction(self, junction_id: str) -> None:
        payload = json.dumps(self._thing_payload(junction_id, {"junction_id": junction_id, "status": "UNKNOWN"})).encode()
        self._request("PUT", f"/api/2/things/traffic:{junction_id}", payload)

    def _thing_payload(self, junction_id: str, properties: dict) -> dict:
        return {
            "policyId": self.policy_id,
            "attributes": {"junction_id": junction_id, "type": "traffic-junction"},
            "features": {"state": {"properties": properties}},
        }

    def get_junction(self, junction_id: str) -> dict:
        response = self._request("GET", f"/api/2/things/traffic:{junction_id}/features/state/properties")
        return json.loads(response)

    def _request(self, method: str, path: str, body: bytes | None = None) -> bytes:
        request = Request(self.base_url + path, data=body, method=method)
        request.add_header("Content-Type", "application/json")
        request.add_header("Accept", "application/json")
        request.add_header("Authorization", "Basic " + self._basic_auth())
        with urlopen(request, timeout=10) as response:
            return response.read()

    def _basic_auth(self) -> str:
        import base64

        credentials = f"{self.auth[0]}:{self.auth[1]}".encode()
        return base64.b64encode(credentials).decode()