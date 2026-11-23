"""Vercel entrypoint for the same SLL review flow used by the local server."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from hmac import compare_digest
from io import BytesIO
import json
import os
import re
from secrets import randbits, token_hex
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

from flask import Flask, Response, request

from app import Handler

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 240_000
COOKIE = "sll_workspace"
BLOB_API = "https://vercel.com/api/blob"


class StorageUnavailable(Exception):
    pass


class BlobHistory:
    def __init__(self, workspace_id):
        self.prefix = f"sll/reviews/{workspace_id}/"

    def read_json(self, url, *, body=None, headers=None):
        token = os.getenv("BLOB_READ_WRITE_TOKEN", "")
        if not token:
            raise StorageUnavailable()
        req = Request(url, data=body, method="GET" if body is None else "PUT", headers={
            "Authorization": f"Bearer {token}",
            "x-api-version": "13",
            **(headers or {}),
        })
        try:
            with urlopen(req, timeout=10) as response:
                return json.load(response)
        except HTTPError as error:
            if error.code == 404 and urlsplit(url).hostname.endswith(".private.blob.vercel-storage.com"):
                raise ValueError("找不到此工作階段的版本。") from None
            raise StorageUnavailable() from None
        except (URLError, TimeoutError, ValueError):
            raise StorageUnavailable() from None

    def save(self, data, parent):
        version = randbits(63) or 1
        created = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        body = json.dumps({"created": created, "parent": parent, "data": data}, ensure_ascii=False).encode()
        params = urlencode({"pathname": f"{self.prefix}{version}.json"})
        self.read_json(f"{BLOB_API}/?{params}", body=body, headers={
            "Content-Type": "application/json",
            "x-content-type": "application/json",
            "x-vercel-blob-access": "private",
            "x-add-random-suffix": "0",
            "x-allow-overwrite": "0",
        })
        return version

    def load(self, version):
        token = os.getenv("BLOB_READ_WRITE_TOKEN", "")
        store_id = token.split("_")[3] if len(token.split("_")) > 3 else ""
        if not re.fullmatch(r"[A-Za-z0-9]+", store_id):
            raise StorageUnavailable()
        path = f"{self.prefix}{version}.json"
        item = self.read_json(f"https://{store_id}.private.blob.vercel-storage.com/{path}?cache=0")
        return item["parent"], item["created"], item["data"]

    def history(self):
        items = []
        query = {"prefix": self.prefix, "limit": 100}
        while True:
            result = self.read_json(f"{BLOB_API}/?{urlencode(query)}")
            items.extend(result["blobs"])
            if not result.get("hasMore") or not result.get("cursor"):
                break
            query["cursor"] = result["cursor"]
        items.sort(key=lambda item: item["uploadedAt"], reverse=True)
        versions = [int(item["pathname"].rsplit("/", 1)[-1].removesuffix(".json")) for item in items]
        with ThreadPoolExecutor(max_workers=8) as pool:
            snapshots = pool.map(self.load, versions)
            return [(version, snapshot[2]) for version, snapshot in zip(versions, snapshots)]


class CloudRequest(Handler):
    trial_required = True

    def __init__(self, storage):
        self.storage = storage
        self.path = request.full_path.removesuffix("?")
        self.headers = request.headers
        self.rfile = BytesIO(request.get_data()) if request.method == "POST" else BytesIO()
        self.wfile = BytesIO()
        self.response_headers = {}

    def send_response(self, code, message=None):
        self.status = code

    def send_header(self, key, value):
        self.response_headers[key] = value

    def end_headers(self):
        pass

    def save_snapshot(self, data, parent):
        return self.storage.save(data, parent)

    def load_snapshot(self, case_id):
        return self.storage.load(case_id)

    def history(self):
        return self.storage.history()

    def authorize_live(self, args):
        configured = os.getenv("SLL_TRIAL_CODE", "").encode()
        submitted = args.get("trial_code", "").encode()
        if not configured or not compare_digest(configured, submitted):
            raise ValueError("試用碼不正確或實際模型尚未啟用。可返回使用 [MOCK MODE]。")


@app.get("/")
@app.get("/history")
@app.get("/export")
@app.post("/run")
@app.post("/review")
def review_flow():
    workspace = request.cookies.get(COOKIE, "")
    new_workspace = re.fullmatch(r"[0-9a-f]{48}", workspace) is None
    if new_workspace:
        workspace = token_hex(24)
    handler = CloudRequest(BlobHistory(workspace))
    try:
        if request.method == "POST":
            handler.do_POST()
        else:
            handler.do_GET()
    except StorageUnavailable:
        handler.page("<p>覆核紀錄服務目前無法使用，請稍後再試。</p>", 503)
    response = Response(handler.wfile.getvalue(), status=handler.status, headers=handler.response_headers)
    response.headers["Cache-Control"] = "private, no-store"
    response.headers["Referrer-Policy"] = "no-referrer"
    if new_workspace:
        response.set_cookie(COOKIE, workspace, secure=bool(os.getenv("VERCEL")), httponly=True,
                            samesite="Lax", max_age=60 * 60 * 24 * 90)
    return response
