# import requests
# import json
# from config import config
# from typing import Optional, Dict, Any, Generator

# class APIClient:
#     def __init__(self, api_key: Optional[str] = None):
#         self.api_key = api_key or config.API_KEY
#         self.timeout = 30 # seconds
#         self.stream_timeout = 60 # seconds

#     def _get_headers(self) -> Dict[str, str]:
#         headers = {}
#         if self.api_key:
#             headers["Authorization"] = f"Bearer {self.api_key}"
#         return headers

#     def chat(self, query: str, session_id: Optional[str] = None, options: Dict[str, Any] = None) -> Dict[str, Any]:
#         """
#         Send a chat message to the RAG backend.
#         """
#         payload = {
#             "query": query,
#             "session_id": session_id,
#             **(options or {})
#         }
#         try:
#             response = requests.post(
#                 config.get_chat_url(), 
#                 json=payload, 
#                 headers=self._get_headers(),
#                 timeout=self.timeout
#             )
#             response.raise_for_status()
#             return response.json()
#         except requests.exceptions.Timeout:
#             return {"error": "Request timed out"}
#         except requests.exceptions.RequestException as e:
#             return {"error": str(e)}

#     def chat_stream(self, query: str, session_id: Optional[str] = None, options: Dict[str, Any] = None) -> Generator[Dict[str, Any], None, None]:
#         """
#         Stream chat responses from the RAG backend.
#         Yields chunks of data: {"content": ...} or {"session_id": ...} or {"error": ...}
#         """
#         payload = {
#             "query": query,
#             "session_id": session_id,
#             **(options or {})
#         }
#         try:
#             with requests.post(
#                 config.get_chat_stream_url(), 
#                 json=payload, 
#                 stream=True, 
#                 headers=self._get_headers(),
#                 timeout=self.stream_timeout
#             ) as response:
#                 response.raise_for_status()
                
#                 # Extract session_id from headers if available
#                 session_id_header = response.headers.get("X-Session-ID")
#                 if session_id_header:
#                     yield {"session_id": session_id_header}
                    
#                 # Iterate over lines for SSE-style JSON
#                 for line in response.iter_lines():
#                     if line:
#                         try:
#                             decoded = line.decode("utf-8")
#                             data = json.loads(decoded)
#                             yield data
#                         except json.JSONDecodeError:
#                             # Fallback for raw text if any
#                             yield {"content": decoded}
                        
#         except requests.exceptions.Timeout:
#              yield {"error": "Stream connection timed out"}
#         except requests.exceptions.RequestException as e:
#             yield {"error": str(e)}

#     def ingest_file(self, file_obj, category: str = "Uncategorized") -> Dict[str, Any]:
#         """
#         Upload a file for ingestion.
#         """
#         # Note: requests takes 'files' which usually don't need Content-Type header manually set for the part,
#         # but we might need to handle auth. Request headers update automatically for Authorization.
#         files = {"file": (file_obj.name, file_obj, file_obj.type)}
#         data = {"category": category}
#         try:
#             response = requests.post(
#                 config.get_ingest_url(), 
#                 files=files, 
#                 data=data,
#                 headers=self._get_headers(),
#                 timeout=self.timeout
#             )
#             response.raise_for_status()
#             return response.json()
#         except requests.exceptions.Timeout:
#             return {"error": "Ingestion timed out"}
#         except requests.exceptions.RequestException as e:
#             return {"error": str(e)}

# api_client = APIClient()












import json
from typing import Any, Dict, Generator, Optional

import requests

from config import config


class APIClient:
    """HTTP client used by the Streamlit frontend to call the FastAPI backend."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or getattr(config, "API_KEY", None)
        self.timeout = 30
        self.stream_timeout = 60

    def _get_headers(self) -> Dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    @staticmethod
    def _error_message(response: requests.Response) -> str:
        """Prefer the backend's JSON detail message when available."""
        try:
            body = response.json()
            if isinstance(body, dict):
                return str(body.get("detail") or body.get("error") or body)
        except ValueError:
            pass
        return response.text or f"HTTP {response.status_code}"

    def chat(
        self,
        query: str,
        session_id: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        payload = {"query": query, "session_id": session_id, **(options or {})}
        try:
            response = requests.post(
                config.get_chat_url(),
                json=payload,
                headers=self._get_headers(),
                timeout=self.timeout,
            )
            if not response.ok:
                return {"error": self._error_message(response)}
            try:
                return response.json()
            except ValueError:
                return {"error": "Backend returned invalid JSON."}
        except requests.exceptions.Timeout:
            return {"error": "Request timed out."}
        except requests.exceptions.RequestException as exc:
            return {"error": str(exc)}

    def chat_stream(
        self,
        query: str,
        session_id: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """Yield JSON packets from JSON-lines or Server-Sent Events responses."""
        payload = {"query": query, "session_id": session_id, **(options or {})}
        try:
            with requests.post(
                config.get_chat_stream_url(),
                json=payload,
                stream=True,
                headers={**self._get_headers(), "Accept": "text/event-stream, application/x-ndjson, application/json"},
                timeout=(10, self.stream_timeout),
            ) as response:
                if not response.ok:
                    yield {"error": self._error_message(response)}
                    return

                session_id_header = response.headers.get("X-Session-ID")
                if session_id_header:
                    yield {"session_id": session_id_header}

                for line in response.iter_lines(decode_unicode=True):
                    if not line:
                        continue

                    decoded = line.strip()
                    # Ignore SSE comments and event/id/retry metadata lines.
                    if decoded.startswith(":"):
                        continue
                    if decoded.startswith(("event:", "id:", "retry:")):
                        continue
                    if decoded.startswith("data:"):
                        decoded = decoded[5:].strip()
                    if not decoded:
                        continue
                    if decoded == "[DONE]":
                        break

                    try:
                        packet = json.loads(decoded)
                    except json.JSONDecodeError:
                        # Preserve plain-text streaming backends as a fallback.
                        yield {"content": decoded}
                        continue

                    if isinstance(packet, dict):
                        yield packet
                    else:
                        yield {"content": str(packet)}

        except requests.exceptions.Timeout:
            yield {"error": "Stream connection timed out."}
        except requests.exceptions.RequestException as exc:
            yield {"error": str(exc)}

    def ingest_file(self, file_obj, category: str = "Uncategorized") -> Dict[str, Any]:
        """Upload one file and return either the backend response or an error."""
        filename = getattr(file_obj, "name", "upload.bin")
        content_type = getattr(file_obj, "type", None) or "application/octet-stream"
        files = {"file": (filename, file_obj, content_type)}
        data = {"category": category}

        try:
            response = requests.post(
                config.get_ingest_url(),
                files=files,
                data=data,
                headers=self._get_headers(),
                timeout=self.timeout,
            )
            if not response.ok:
                return {"error": self._error_message(response)}
            try:
                return response.json()
            except ValueError:
                return {"error": "Backend returned invalid JSON after upload."}
        except requests.exceptions.Timeout:
            return {"error": "Ingestion timed out."}
        except requests.exceptions.RequestException as exc:
            return {"error": str(exc)}


api_client = APIClient()
