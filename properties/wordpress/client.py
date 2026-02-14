# properties/wordpress/client.py
import base64
import requests
from django.conf import settings

class WordPressError(Exception):
    pass

class WordPressClient:
    def __init__(self):
        self.base_url = settings.WP_BASE_URL.rstrip("/")
        self.user = settings.WP_USER
        self.app_password = settings.WP_APP_PASSWORD
        self.timeout = getattr(settings, "WP_TIMEOUT", 30)

        # ✅ REUSAR CONEXIONES HTTP (keep-alive)
        self.session = requests.Session()

    def _headers(self):
        token = base64.b64encode(
            f"{self.user}:{self.app_password}".encode("utf-8")
        ).decode("utf-8")
        return {
            "Authorization": f"Basic {token}",
            "Accept": "application/json",
        }

    def _json_headers(self):
        return {**self._headers(), "Content-Type": "application/json"}

    def _url(self, path: str) -> str:
        if not path.startswith("/"):
            path = "/" + path
        return self.base_url + path

    def request(self, method: str, path: str, **kwargs):
        url = self._url(path)

        # ✅ usar session
        resp = self.session.request(method, url, timeout=self.timeout, **kwargs)

        try:
            data = resp.json()
        except Exception:
            data = resp.text

        if resp.status_code >= 400:
            raise WordPressError(f"WP {resp.status_code} {method} {url} -> {data}")
        return data

    def get(self, path: str, params=None, headers=None):
        return self.request("GET", path, params=params, headers=headers or self._headers())

    def post(self, path: str, json=None, headers=None):
        return self.request("POST", path, json=json, headers=headers or self._json_headers())

    def put(self, path: str, json=None, headers=None):
        return self.request("PUT", path, json=json, headers=headers or self._json_headers())

    def delete(self, path: str, params=None, headers=None):
        return self.request("DELETE", path, params=params, headers=headers or self._headers())

    # --- CPT property ---
    def get_property(self, wp_post_id: int):
        return self.get(f"/wp-json/wp/v2/properties/{wp_post_id}")

    def create_property(self, payload: dict):
        return self.post("/wp-json/wp/v2/properties", json=payload)

    def update_property(self, wp_post_id: int, payload: dict):
        return self.put(f"/wp-json/wp/v2/properties/{wp_post_id}", json=payload)

    def delete_property(self, wp_post_id: int, force: bool = True):
        params = {"force": "true" if force else "false"}
        return self.delete(f"/wp-json/wp/v2/properties/{wp_post_id}", params=params)

    def me(self):
        return self.get("/wp-json/wp/v2/users/me")

    # --- Taxonomy helpers ---
    def list_terms(self, taxonomy: str, search: str, per_page: int = 100):
        return self.get(f"/wp-json/wp/v2/{taxonomy}", params={"search": search, "per_page": per_page})

    def create_term(self, taxonomy: str, name: str, slug: str | None = None):
        payload = {"name": name}
        if slug:
            payload["slug"] = slug
        return self.post(f"/wp-json/wp/v2/{taxonomy}", json=payload)

    # --- Media upload ---
    def upload_media(self, filename: str, content_bytes: bytes, content_type: str):
        url = self._url("/wp-json/wp/v2/media")
        headers = {
            **self._headers(),
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": content_type,
        }

        # ✅ usar session
        resp = self.session.post(url, headers=headers, data=content_bytes, timeout=self.timeout)

        try:
            data = resp.json()
        except Exception:
            data = resp.text
        if resp.status_code >= 400:
            raise WordPressError(f"WP {resp.status_code} POST {url} -> {data}")
        return data

    # --- Media helpers ---
    def get_media(self, media_id: int):
        return self.get(f"/wp-json/wp/v2/media/{media_id}")

    def delete_media(self, media_id: int, force: bool = True):
        params = {"force": "true" if force else "false"}
        return self.delete(f"/wp-json/wp/v2/media/{media_id}", params=params)

    def import_media_from_url(self, url: str):
        return self.post("/wp-json/propify/v1/media-from-url", json={"url": url})