#!/usr/bin/env python3
"""IntelAlloc image generation/editing CLI for the Codex skill."""

from __future__ import annotations

import argparse
import base64
import dataclasses
import datetime as _dt
import json
import mimetypes
import os
import pathlib
import platform
import random
import re
import ssl
import sys
import tempfile
import time
import urllib.error
import urllib.request
import uuid
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


DEFAULT_GENERATIONS_ENDPOINT = "https://backend.intelalloc.com/v1/images/generations"
DEFAULT_EDITS_ENDPOINT = "https://backend.intelalloc.com/v1/images/edits"
DEFAULT_MODEL = "gpt-image-2"
DEFAULT_SIZE = "2048x1152"
DEFAULT_QUALITY = "medium"
CODEX_CLI_VERSION = "0.77.0"
OUTPUT_FORMAT = "png"
PARTIAL_IMAGES = 2
BACKGROUND = "auto"
MAX_INPUT_IMAGES = 16
MAX_RETRY_COUNT = 2
REQUEST_TIMEOUT_SECONDS = 60 * 60
HISTORY_LIMIT = 100
UPLOAD_OPTIMIZE_MAX_EDGE = 2048
UPLOAD_OPTIMIZE_JPEG_QUALITY = 85
UPLOAD_OPTIMIZE_MIN_BYTES = 512 * 1024

SUPPORTED_SIZES = {
    "1536x1024",
    "1024x1536",
    "1024x1024",
    "2048x1152",
    "1152x2048",
    "2048x2048",
    "3840x2160",
    "2160x3840",
}
SUPPORTED_QUALITIES = {"low", "medium", "high"}
SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


@dataclasses.dataclass
class UploadImage:
    source_path: pathlib.Path
    upload_path: pathlib.Path
    filename: str
    content_type: str
    optimized: bool
    original_bytes: int
    upload_bytes: int
    cleanup: bool = False


def normalized_arch(machine: Optional[str] = None) -> str:
    value = (machine or platform.machine() or "").lower()
    if value in {"amd64", "x86_64"}:
        return "x86_64"
    if value in {"arm64", "aarch64"}:
        return "arm64"
    return value or "unknown"


def collect_platform_info() -> Dict[str, str]:
    return {
        "system": platform.system() or "",
        "release": platform.release() or "",
        "version": platform.version() or "",
        "machine": platform.machine() or "",
        "python": sys.version.split()[0],
    }


def build_default_user_agent(info: Optional[Dict[str, str]] = None) -> str:
    info = info or collect_platform_info()
    system = info.get("system") or platform.system() or "Unknown"
    release = info.get("release") or platform.release() or ""
    version = info.get("version") or platform.version() or ""
    arch = normalized_arch(info.get("machine"))
    if system == "Windows":
        os_label = "Windows " + (version or release or "unknown")
        terminal = "WindowsTerminal"
    elif system == "Darwin":
        os_label = "macOS " + (release or version or "unknown")
        terminal = "Terminal"
    elif system == "Linux":
        os_label = "Linux " + (release or version or "unknown")
        terminal = "Terminal"
    else:
        os_label = system + ((" " + (release or version)) if (release or version) else "")
        terminal = "Terminal"
    return "codex_cli_rs/{0} ({1}; {2}) {3}".format(CODEX_CLI_VERSION, os_label, arch, terminal)


class CliError(Exception):
    """Expected user-facing CLI error."""


class ApiResponseError(Exception):
    """API response error whose body should be shown to the user verbatim."""

    def __init__(self, body: str, status: Optional[int] = None):
        super().__init__(body)
        self.body = body
        self.status = status


def config_dir() -> pathlib.Path:
    return pathlib.Path.home() / ".codex" / "intelalloc-image"


def config_path() -> pathlib.Path:
    return config_dir() / "config.json"


def history_path() -> pathlib.Path:
    return config_dir() / "history.json"


def now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def monotonic_seconds() -> float:
    return time.perf_counter()


def load_json(path: pathlib.Path, fallback: Any) -> Any:
    if not path.exists():
        return fallback
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return fallback


def save_json_private(path: pathlib.Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, path)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def load_config() -> Dict[str, Any]:
    cfg = load_json(config_path(), {})
    if not isinstance(cfg, dict):
        return {}
    return cfg


def mask_key(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return value[:2] + "***"
    return value[:4] + "..." + value[-4:]


def normalize_size(value: Optional[str]) -> str:
    value = (value or DEFAULT_SIZE).strip()
    if value not in SUPPORTED_SIZES:
        raise CliError(
            "Unsupported size: {0}. Supported sizes: {1}".format(
                value, ", ".join(sorted(SUPPORTED_SIZES))
            )
        )
    return value


def normalize_quality(value: Optional[str]) -> str:
    value = (value or DEFAULT_QUALITY).strip()
    if value not in SUPPORTED_QUALITIES:
        raise CliError(
            "Unsupported quality: {0}. Supported qualities: {1}".format(
                value, ", ".join(sorted(SUPPORTED_QUALITIES))
            )
        )
    return value


def resolve_settings(args: argparse.Namespace, require_key: bool) -> Dict[str, str]:
    cfg = load_config()
    api_key = getattr(args, "api_key", None) or os.environ.get("INTELALLOC_API_KEY") or cfg.get("api_key") or ""
    settings = {
        "api_key": str(api_key).strip(),
        "endpoint": str(getattr(args, "endpoint", None) or cfg.get("endpoint") or DEFAULT_GENERATIONS_ENDPOINT).strip(),
        "edits_endpoint": str(
            getattr(args, "edits_endpoint", None) or cfg.get("edits_endpoint") or DEFAULT_EDITS_ENDPOINT
        ).strip(),
        "model": str(getattr(args, "model", None) or cfg.get("model") or DEFAULT_MODEL).strip(),
        "user_agent": str(getattr(args, "user_agent", None) or cfg.get("user_agent") or build_default_user_agent()).strip(),
        "default_size": normalize_size(getattr(args, "size", None) or cfg.get("default_size") or DEFAULT_SIZE),
        "default_quality": normalize_quality(
            getattr(args, "quality", None) or cfg.get("default_quality") or DEFAULT_QUALITY
        ),
    }
    if require_key and not settings["api_key"]:
        raise CliError(
            "IntelAlloc API key is not configured. Run: python scripts/intelalloc_image.py configure --api-key <key>"
        )
    if not settings["endpoint"]:
        settings["endpoint"] = DEFAULT_GENERATIONS_ENDPOINT
    if not settings["edits_endpoint"]:
        settings["edits_endpoint"] = DEFAULT_EDITS_ENDPOINT
    if not settings["model"]:
        settings["model"] = DEFAULT_MODEL
    if not settings["user_agent"]:
        settings["user_agent"] = build_default_user_agent()
    return settings


def renderable_path(path: pathlib.Path) -> str:
    return path.resolve().as_posix()


def ensure_parent(path: pathlib.Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def save_image(path: pathlib.Path, image_bytes: bytes) -> pathlib.Path:
    if not image_bytes:
        raise CliError("No image bytes were returned by the API.")
    ensure_parent(path)
    with path.open("wb") as f:
        f.write(image_bytes)
    return path.resolve()


def response_error_text(response: urllib.error.HTTPError) -> str:
    try:
        raw = response.read().decode("utf-8", errors="replace")
    except Exception:
        raw = ""
    if not raw:
        return str(response)
    return raw


def is_retryable_exception(exc: BaseException) -> bool:
    if isinstance(exc, urllib.error.HTTPError):
        return exc.code in {408, 409, 425, 429, 500, 503, 504, 524}
    if isinstance(exc, (urllib.error.URLError, TimeoutError, ssl.SSLError, ConnectionError)):
        return True
    if isinstance(exc, CliError):
        msg = str(exc).lower()
        return "upstream" in msg or "stream disconnected" in msg or "temporarily" in msg
    return False


def retry_delay(attempt: int) -> float:
    return min(8.0, 1.0 * (2 ** max(0, attempt - 1))) + random.random() * 0.25


def request_with_retries(fn):
    last_exc: Optional[BaseException] = None
    for attempt in range(MAX_RETRY_COUNT + 1):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 - user-facing CLI wraps expected network errors
            last_exc = exc
            if attempt >= MAX_RETRY_COUNT or not is_retryable_exception(exc):
                break
            print("RETRY={0}/{1} reason={2}".format(attempt + 1, MAX_RETRY_COUNT, str(exc)), file=sys.stderr)
            time.sleep(retry_delay(attempt + 1))
    if isinstance(last_exc, ApiResponseError):
        raise last_exc
    if isinstance(last_exc, CliError):
        raise last_exc
    if isinstance(last_exc, urllib.error.HTTPError):
        raise ApiResponseError(response_error_text(last_exc), status=last_exc.code)
    raise CliError(str(last_exc) if last_exc else "Request failed.")


def timed_api_request(fn):
    started_at = now_iso()
    started = monotonic_seconds()
    print("REQUEST_STARTED_AT=" + started_at, file=sys.stderr)
    try:
        return request_with_retries(fn)
    finally:
        finished_at = now_iso()
        elapsed = monotonic_seconds() - started
        print("REQUEST_FINISHED_AT=" + finished_at, file=sys.stderr)
        print("REQUEST_ELAPSED_SECONDS={0:.3f}".format(elapsed), file=sys.stderr)


def open_request(req: urllib.request.Request):
    return urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_SECONDS)


def request_headers(settings: Dict[str, str], content_type: str, accept: str = "text/event-stream") -> Dict[str, str]:
    return {
        "Authorization": "Bearer " + settings["api_key"],
        "Content-Type": content_type,
        "Accept": accept,
        "Cache-Control": "no-cache",
        "User-Agent": settings["user_agent"],
    }


def build_generation_body(prompt: str, settings: Dict[str, str], stream: bool = True) -> bytes:
    body = {
        "model": settings["model"],
        "prompt": prompt,
        "n": 1,
        "size": settings["default_size"],
        "quality": settings["default_quality"],
        "output_format": OUTPUT_FORMAT,
        "stream": stream,
        "partial_images": PARTIAL_IMAGES,
        "background": BACKGROUND,
    }
    return json.dumps(body, ensure_ascii=False).encode("utf-8")


def request_generation(prompt: str, settings: Dict[str, str]) -> bytes:
    def once() -> bytes:
        body = build_generation_body(prompt, settings, stream=True)
        req = urllib.request.Request(
            settings["endpoint"],
            data=body,
            method="POST",
            headers=request_headers(settings, "application/json; charset=utf-8"),
        )
        with open_request(req) as response:
            return read_image_response(response)

    return timed_api_request(once)


def guess_mime(path: pathlib.Path) -> str:
    mime = mimetypes.guess_type(str(path))[0]
    return mime or "application/octet-stream"


def maybe_optimize_image(path: pathlib.Path, force: bool) -> UploadImage:
    original_bytes = path.stat().st_size
    original = UploadImage(
        source_path=path,
        upload_path=path,
        filename=path.name,
        content_type=guess_mime(path),
        optimized=False,
        original_bytes=original_bytes,
        upload_bytes=original_bytes,
    )
    if not force and original_bytes < UPLOAD_OPTIMIZE_MIN_BYTES:
        return original
    try:
        from PIL import Image, ImageOps  # type: ignore
    except Exception:
        return original
    try:
        with Image.open(path) as img:
            img = ImageOps.exif_transpose(img)
            resample = getattr(getattr(Image, "Resampling", Image), "LANCZOS", getattr(Image, "BICUBIC", 3))
            img.thumbnail((UPLOAD_OPTIMIZE_MAX_EDGE, UPLOAD_OPTIMIZE_MAX_EDGE), resample)
            if img.mode in {"RGBA", "LA"}:
                background = Image.new("RGB", img.size, (255, 255, 255))
                alpha = img.getchannel("A") if img.mode == "RGBA" else img.getchannel(1)
                background.paste(img.convert("RGB"), mask=alpha)
                img = background
            else:
                img = img.convert("RGB")
            tmp = tempfile.NamedTemporaryFile(prefix="intelalloc-upload-", suffix=".jpg", delete=False)
            tmp_path = pathlib.Path(tmp.name)
            tmp.close()
            try:
                img.save(tmp_path, "JPEG", quality=UPLOAD_OPTIMIZE_JPEG_QUALITY, optimize=True)
            except Exception:
                tmp_path.unlink(missing_ok=True)
                return original
        upload_bytes = tmp_path.stat().st_size
        if upload_bytes >= original_bytes:
            tmp_path.unlink(missing_ok=True)
            return original
        return UploadImage(
            source_path=path,
            upload_path=tmp_path,
            filename=path.with_suffix(".jpg").name,
            content_type="image/jpeg",
            optimized=True,
            original_bytes=original_bytes,
            upload_bytes=upload_bytes,
            cleanup=True,
        )
    except Exception:
        return original


def prepare_upload_images(inputs: Sequence[pathlib.Path]) -> List[UploadImage]:
    force = len(inputs) > 1
    uploads = [maybe_optimize_image(path, force=force) for path in inputs]
    optimized_count = sum(1 for item in uploads if item.optimized)
    total_original = sum(item.original_bytes for item in uploads)
    total_upload = sum(item.upload_bytes for item in uploads)
    if uploads:
        print(
            "UPLOAD_IMAGES={0} OPTIMIZED={1} ORIGINAL_BYTES={2} UPLOAD_BYTES={3}".format(
                len(uploads), optimized_count, total_original, total_upload
            ),
            file=sys.stderr,
        )
        if len(inputs) > 1 and optimized_count == 0:
            print("UPLOAD_OPTIMIZATION=skipped_or_unavailable", file=sys.stderr)
    return uploads


def cleanup_upload_images(uploads: Sequence[UploadImage]) -> None:
    for item in uploads:
        if item.cleanup:
            try:
                item.upload_path.unlink(missing_ok=True)
            except OSError:
                pass


def write_field(parts: List[bytes], boundary: str, name: str, value: str) -> None:
    parts.append(("--" + boundary + "\r\n").encode("utf-8"))
    parts.append(('Content-Disposition: form-data; name="{0}"\r\n\r\n'.format(name)).encode("utf-8"))
    parts.append(str(value).encode("utf-8"))
    parts.append(b"\r\n")


def write_file(parts: List[bytes], boundary: str, name: str, upload: UploadImage) -> None:
    parts.append(("--" + boundary + "\r\n").encode("utf-8"))
    parts.append(
        (
            'Content-Disposition: form-data; name="{0}"; filename="{1}"\r\n'
            "Content-Type: {2}\r\n\r\n"
        ).format(name, upload.filename.replace('"', ""), upload.content_type).encode("utf-8")
    )
    with upload.upload_path.open("rb") as f:
        parts.append(f.read())
    parts.append(b"\r\n")


def build_multipart(prompt: str, uploads: Sequence[UploadImage], settings: Dict[str, str]) -> Tuple[bytes, str]:
    boundary = "----IntelAllocImage" + uuid.uuid4().hex
    parts: List[bytes] = []
    write_field(parts, boundary, "model", settings["model"])
    write_field(parts, boundary, "prompt", prompt)
    write_field(parts, boundary, "n", "1")
    write_field(parts, boundary, "size", settings["default_size"])
    write_field(parts, boundary, "quality", settings["default_quality"])
    write_field(parts, boundary, "output_format", OUTPUT_FORMAT)
    write_field(parts, boundary, "stream", "true")
    write_field(parts, boundary, "partial_images", str(PARTIAL_IMAGES))
    write_field(parts, boundary, "background", BACKGROUND)
    for upload in uploads:
        write_file(parts, boundary, "image[]", upload)
    parts.append(("--" + boundary + "--\r\n").encode("utf-8"))
    return b"".join(parts), boundary


def request_edit(prompt: str, inputs: Sequence[pathlib.Path], settings: Dict[str, str]) -> bytes:
    if not inputs:
        raise CliError("Edit requires at least one input image.")
    if len(inputs) > MAX_INPUT_IMAGES:
        raise CliError("Edit supports at most {0} input images; got {1}.".format(MAX_INPUT_IMAGES, len(inputs)))
    uploads = prepare_upload_images(inputs)

    def once() -> bytes:
        body, boundary = build_multipart(prompt, uploads, settings)
        req = urllib.request.Request(
            settings["edits_endpoint"],
            data=body,
            method="POST",
            headers=request_headers(settings, "multipart/form-data; boundary=" + boundary),
        )
        with open_request(req) as response:
            return read_image_response(response)

    try:
        return timed_api_request(once)
    finally:
        cleanup_upload_images(uploads)


def read_image_response(response) -> bytes:
    content_type = response.headers.get("Content-Type", "")
    raw = response.read()
    text = raw.decode("utf-8", errors="replace")
    if "text/event-stream" in content_type.lower() or looks_like_event_stream(text):
        return read_streamed_image(text)
    return read_image_from_json(text)


def looks_like_event_stream(text: str) -> bool:
    trimmed = (text or "").lstrip()
    return trimmed.startswith("event:") or trimmed.startswith("data:")


def read_streamed_image(text: str) -> bytes:
    event_lines: List[str] = []
    for line in text.splitlines():
        if line == "":
            b64 = process_event_data("\n".join(event_lines))
            event_lines = []
            if b64:
                return decode_base64_image(b64)
            continue
        if line.lower().startswith("data:"):
            event_lines.append(line[5:].lstrip())
    b64 = process_event_data("\n".join(event_lines))
    if b64:
        return decode_base64_image(b64)
    raise CliError("Stream ended without a final image.")


def process_event_data(data_text: str) -> Optional[str]:
    data_text = (data_text or "").strip()
    if not data_text or data_text == "[DONE]":
        return None
    try:
        payload = json.loads(data_text)
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    event_type = str(payload.get("type") or "")
    if "failed" in event_type.lower() or "error" in event_type.lower():
        raise ApiResponseError(data_text)
    b64 = extract_base64(payload)
    if "partial" in event_type.lower():
        return None
    if b64 and (not event_type or "complete" in event_type.lower() or "completed" in event_type.lower()):
        return b64
    if b64 and not event_type:
        return b64
    return None


def read_image_from_json(text: str) -> bytes:
    try:
        payload = json.loads(text)
    except Exception as exc:
        raise CliError("Response was not valid JSON and not an event stream: " + str(exc)) from exc
    b64 = extract_base64(payload)
    if not b64:
        if isinstance(payload, dict) and ("error" in payload or "message" in payload or "detail" in payload):
            raise ApiResponseError(text)
        raise CliError("Response did not contain an image base64 field.")
    return decode_base64_image(b64)


def decode_base64_image(value: str) -> bytes:
    value = re.sub(r"^data:image/[^;]+;base64,", "", value.strip())
    try:
        return base64.b64decode(value, validate=False)
    except Exception as exc:
        raise CliError("Image base64 could not be decoded: " + str(exc)) from exc


def extract_base64(payload: Any) -> Optional[str]:
    if isinstance(payload, dict):
        for key in ("b64_json", "partial_image_b64", "image", "image_b64", "image_base64", "result"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value
        data = payload.get("data")
        if isinstance(data, list) and data:
            return extract_base64(data[0])
        if isinstance(data, dict):
            return extract_base64(data)
        output = payload.get("output")
        if isinstance(output, list):
            for item in output:
                found = extract_base64(item)
                if found:
                    return found
        content = payload.get("content")
        if isinstance(content, list):
            for item in content:
                found = extract_base64(item)
                if found:
                    return found
    return None


def extract_error_message(payload: Any) -> Optional[str]:
    if isinstance(payload, dict):
        for key in ("message", "detail"):
            value = payload.get(key)
            if value:
                return str(value)
        error = payload.get("error")
        if isinstance(error, dict):
            parts = []
            for key in ("code", "type", "message"):
                value = error.get(key)
                if value:
                    parts.append(str(value))
            if parts:
                return "\n".join(parts)
        if error:
            return str(error)
    return None


def collect_dir_images(path: pathlib.Path, recursive: bool) -> List[pathlib.Path]:
    if not path.exists() or not path.is_dir():
        raise CliError("Input directory does not exist: " + str(path))
    iterator: Iterable[pathlib.Path] = path.rglob("*") if recursive else path.iterdir()
    files = [
        p.resolve()
        for p in iterator
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
    ]
    return sorted(files, key=lambda p: str(p).lower())


def resolve_inputs(args: argparse.Namespace) -> List[pathlib.Path]:
    inputs: List[pathlib.Path] = []
    for value in getattr(args, "inputs", None) or []:
        path = pathlib.Path(value).expanduser()
        if not path.exists() or not path.is_file():
            raise CliError("Input image does not exist: " + str(path))
        inputs.append(path.resolve())
    if getattr(args, "input_dir", None):
        dir_images = collect_dir_images(pathlib.Path(args.input_dir).expanduser(), bool(getattr(args, "recursive", False)))
        limit = getattr(args, "limit", None)
        if limit is not None:
            dir_images = dir_images[:limit]
        inputs.extend(dir_images)
    if getattr(args, "from_last", False):
        last = get_last_output_path()
        if not last:
            raise CliError("No last output is recorded. Specify --input instead.")
        if not last.exists():
            raise CliError("Last output no longer exists: " + str(last))
        inputs.append(last.resolve())
    unique: List[pathlib.Path] = []
    seen = set()
    for path in inputs:
        key = os.path.normcase(str(path))
        if key not in seen:
            seen.add(key)
            unique.append(path)
    if len(unique) > MAX_INPUT_IMAGES:
        raise CliError(
            "Edit found {0} input images, but the maximum is {1}. Reduce inputs or pass --limit 16 for directory input.".format(
                len(unique), MAX_INPUT_IMAGES
            )
        )
    return unique


def get_last_output_path() -> Optional[pathlib.Path]:
    history = load_json(history_path(), {})
    if not isinstance(history, dict):
        return None
    value = history.get("last_output")
    if not value:
        return None
    return pathlib.Path(str(value)).expanduser()


def load_history() -> Dict[str, Any]:
    history = load_json(history_path(), {"last_output": "", "items": []})
    if not isinstance(history, dict):
        history = {"last_output": "", "items": []}
    if not isinstance(history.get("items"), list):
        history["items"] = []
    return history


def add_history(item: Dict[str, Any], outputs: Sequence[pathlib.Path]) -> None:
    history = load_history()
    items = history["items"]
    items.insert(0, item)
    del items[HISTORY_LIMIT:]
    if outputs:
        history["last_output"] = str(outputs[-1].resolve())
    save_json_private(history_path(), history)


def build_history_item(kind: str, prompt: str, size: str, quality: str, outputs: Sequence[pathlib.Path], inputs: Sequence[pathlib.Path]) -> Dict[str, Any]:
    return {
        "id": _dt.datetime.now().strftime("%Y%m%d-%H%M%S"),
        "type": kind,
        "prompt": prompt,
        "size": size,
        "quality": quality,
        "outputs": [str(p.resolve()) for p in outputs],
        "output": str(outputs[-1].resolve()) if outputs else "",
        "inputs": [str(p.resolve()) for p in inputs],
        "created_at": now_iso(),
    }


def print_saved(path: pathlib.Path) -> None:
    resolved = path.resolve()
    print("SAVED_IMAGE=" + str(resolved))
    print("DISPLAY_IMAGE=" + renderable_path(resolved))


def print_saved_many(paths: Sequence[pathlib.Path]) -> None:
    saved = [str(p.resolve()) for p in paths]
    display = [renderable_path(p) for p in paths]
    print("SAVED_IMAGES=" + json.dumps(saved, ensure_ascii=False))
    print("DISPLAY_IMAGES=" + json.dumps(display, ensure_ascii=False))


def print_request_options(settings: Dict[str, str]) -> None:
    print("REQUEST_SIZE=" + settings["default_size"], file=sys.stderr)
    print("REQUEST_QUALITY=" + settings["default_quality"], file=sys.stderr)
    print(
        "本次使用尺寸 {0}，质量 {1}。如需其他尺寸或质量，可以直接说明。".format(
            settings["default_size"], settings["default_quality"]
        ),
        file=sys.stderr,
    )


def initialized_config(api_key: str = "") -> Dict[str, Any]:
    info = collect_platform_info()
    return {
        "endpoint": DEFAULT_GENERATIONS_ENDPOINT,
        "edits_endpoint": DEFAULT_EDITS_ENDPOINT,
        "model": DEFAULT_MODEL,
        "default_size": DEFAULT_SIZE,
        "default_quality": DEFAULT_QUALITY,
        "user_agent": build_default_user_agent(info),
        "platform": info,
        "initialized_at": now_iso(),
        "api_key": api_key.strip(),
    }


def command_init(args: argparse.Namespace) -> int:
    existing = load_config()
    provided_key = (args.api_key or os.environ.get("INTELALLOC_API_KEY") or "").strip()
    existing_key = str(existing.get("api_key") or "").strip()
    api_key = provided_key or existing_key
    generated = initialized_config(api_key)

    if args.force:
        cfg = dict(existing)
        cfg.update(generated)
    else:
        cfg = dict(generated)
        cfg.update(existing)
        if provided_key:
            cfg["api_key"] = provided_key
        cfg.setdefault("platform", generated["platform"])
        cfg.setdefault("initialized_at", generated["initialized_at"])

    if args.dry_run:
        preview = dict(cfg)
        if preview.get("api_key"):
            preview["api_key"] = mask_key(str(preview["api_key"]))
        print(json.dumps(preview, ensure_ascii=False, indent=2))
        print("DRY_RUN=true")
    else:
        save_json_private(config_path(), cfg)
        print("CONFIG_PATH=" + str(config_path()))
        print("INITIALIZED=true")

    print("API_KEY_CONFIGURED=" + ("true" if cfg.get("api_key") else "false"))
    if not cfg.get("api_key"):
        print("API_KEY_MISSING=请运行 configure --api-key <key>，或重新运行 init --api-key <key>")
    print("USER_AGENT=" + str(cfg.get("user_agent") or ""))
    platform_info = cfg.get("platform") if isinstance(cfg.get("platform"), dict) else {}
    print("PLATFORM=" + json.dumps(platform_info, ensure_ascii=False, sort_keys=True))
    return 0


def command_configure(args: argparse.Namespace) -> int:
    cfg = load_config()
    if args.api_key is not None:
        cfg["api_key"] = args.api_key.strip()
    if args.default_size is not None:
        cfg["default_size"] = normalize_size(args.default_size)
    if args.default_quality is not None:
        cfg["default_quality"] = normalize_quality(args.default_quality)
    if args.endpoint is not None:
        cfg["endpoint"] = args.endpoint.strip() or DEFAULT_GENERATIONS_ENDPOINT
    if args.edits_endpoint is not None:
        cfg["edits_endpoint"] = args.edits_endpoint.strip() or DEFAULT_EDITS_ENDPOINT
    if args.model is not None:
        cfg["model"] = args.model.strip() or DEFAULT_MODEL
    if args.user_agent is not None:
        cfg["user_agent"] = args.user_agent.strip() or build_default_user_agent()
    cfg.setdefault("endpoint", DEFAULT_GENERATIONS_ENDPOINT)
    cfg.setdefault("edits_endpoint", DEFAULT_EDITS_ENDPOINT)
    cfg.setdefault("model", DEFAULT_MODEL)
    cfg.setdefault("user_agent", build_default_user_agent())
    cfg.setdefault("default_size", DEFAULT_SIZE)
    cfg.setdefault("default_quality", DEFAULT_QUALITY)
    save_json_private(config_path(), cfg)
    print("CONFIG_PATH=" + str(config_path()))
    print("API_KEY_CONFIGURED=" + ("true" if cfg.get("api_key") else "false"))
    print("DEFAULT_SIZE=" + cfg.get("default_size", DEFAULT_SIZE))
    print("DEFAULT_QUALITY=" + cfg.get("default_quality", DEFAULT_QUALITY))
    return 0


def command_show_config(args: argparse.Namespace) -> int:
    settings = resolve_settings(args, require_key=False)
    print("CONFIG_PATH=" + str(config_path()))
    print("API_KEY_CONFIGURED=" + ("true" if bool(settings["api_key"]) else "false"))
    print("API_KEY_MASKED=" + mask_key(settings["api_key"]))
    print("MODEL=" + settings["model"])
    print("USER_AGENT=" + settings["user_agent"])
    print("ENDPOINT=" + settings["endpoint"])
    print("EDITS_ENDPOINT=" + settings["edits_endpoint"])
    print("DEFAULT_SIZE=" + settings["default_size"])
    print("DEFAULT_QUALITY=" + settings["default_quality"])
    cfg = load_config()
    if cfg.get("initialized_at"):
        print("INITIALIZED_AT=" + str(cfg.get("initialized_at")))
    if isinstance(cfg.get("platform"), dict):
        print("PLATFORM=" + json.dumps(cfg["platform"], ensure_ascii=False, sort_keys=True))
    return 0


def command_generate(args: argparse.Namespace) -> int:
    settings = resolve_settings(args, require_key=True)
    prompt = require_prompt(args.prompt)
    output = pathlib.Path(args.output).expanduser()
    print_request_options(settings)
    image = request_generation(prompt, settings)
    saved = save_image(output, image)
    add_history(
        build_history_item("generate", prompt, settings["default_size"], settings["default_quality"], [saved], []),
        [saved],
    )
    print_saved(saved)
    return 0


def command_edit(args: argparse.Namespace) -> int:
    settings = resolve_settings(args, require_key=True)
    prompt = require_prompt(args.prompt)
    inputs = resolve_inputs(args)
    if not inputs:
        raise CliError("Edit requires --input, --input-dir, or --from-last.")
    output = pathlib.Path(args.output).expanduser()
    print_request_options(settings)
    image = request_edit(prompt, inputs, settings)
    saved = save_image(output, image)
    add_history(
        build_history_item("edit", prompt, settings["default_size"], settings["default_quality"], [saved], inputs),
        [saved],
    )
    print("INPUT_IMAGES=" + json.dumps([str(p) for p in inputs], ensure_ascii=False))
    print_saved(saved)
    return 0


def output_name_for(input_path: pathlib.Path, index: int) -> str:
    stem = input_path.stem or "image"
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", stem).strip("._") or "image"
    return "{0}-{1:03d}.png".format(safe, index)


def command_batch_edit(args: argparse.Namespace) -> int:
    settings = resolve_settings(args, require_key=True)
    prompt = require_prompt(args.prompt)
    input_dir = pathlib.Path(args.input_dir).expanduser()
    inputs = collect_dir_images(input_dir, bool(args.recursive))
    if args.limit is not None:
        inputs = inputs[: args.limit]
    if not inputs:
        raise CliError("No supported input images found in: " + str(input_dir))
    output_dir = pathlib.Path(args.output_dir).expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)
    print_request_options(settings)
    outputs: List[pathlib.Path] = []
    for index, input_path in enumerate(inputs, start=1):
        output = output_dir / output_name_for(input_path, index)
        image = request_edit(prompt, [input_path], settings)
        saved = save_image(output, image)
        outputs.append(saved)
        print("BATCH_ITEM={0}/{1} INPUT={2} OUTPUT={3}".format(index, len(inputs), input_path, saved), file=sys.stderr)
    add_history(
        build_history_item("batch-edit", prompt, settings["default_size"], settings["default_quality"], outputs, inputs),
        outputs,
    )
    print_saved_many(outputs)
    return 0


def command_last(args: argparse.Namespace) -> int:
    last = get_last_output_path()
    if not last:
        print("LAST_OUTPUT=")
        return 1
    print("LAST_OUTPUT=" + str(last))
    print("DISPLAY_IMAGE=" + renderable_path(last))
    print("EXISTS=" + ("true" if last.exists() else "false"))
    return 0 if last.exists() else 1


def command_history(args: argparse.Namespace) -> int:
    history = load_history()
    items = history.get("items", [])[: args.limit]
    print(json.dumps({"last_output": history.get("last_output", ""), "items": items}, ensure_ascii=False, indent=2))
    return 0


def require_prompt(prompt: Optional[str]) -> str:
    prompt = (prompt or "").strip()
    if not prompt:
        raise CliError("Prompt is required.")
    return prompt


def add_common_request_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--api-key", help=argparse.SUPPRESS)
    parser.add_argument("--endpoint", help=argparse.SUPPRESS)
    parser.add_argument("--edits-endpoint", help=argparse.SUPPRESS)
    parser.add_argument("--model", help=argparse.SUPPRESS)
    parser.add_argument("--user-agent", help="Override the HTTP User-Agent for this request.")
    parser.add_argument("--size", choices=sorted(SUPPORTED_SIZES), help="Override image size for this request.")
    parser.add_argument("--quality", choices=sorted(SUPPORTED_QUALITIES), help="Override image quality for this request.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate and edit images through the IntelAlloc API.")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init", help="Initialize local IntelAlloc skill config for this device.")
    p.add_argument("--api-key")
    p.add_argument("--force", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=command_init)

    p = sub.add_parser("configure", help="Save local API key and defaults.")
    p.add_argument("--api-key")
    p.add_argument("--default-size", choices=sorted(SUPPORTED_SIZES))
    p.add_argument("--default-quality", choices=sorted(SUPPORTED_QUALITIES))
    p.add_argument("--endpoint")
    p.add_argument("--edits-endpoint")
    p.add_argument("--model")
    p.add_argument("--user-agent")
    p.set_defaults(func=command_configure)

    p = sub.add_parser("show-config", help="Show resolved configuration without leaking the full API key.")
    add_common_request_options(p)
    p.set_defaults(func=command_show_config)

    p = sub.add_parser("generate", help="Generate one image from text.")
    add_common_request_options(p)
    p.add_argument("--prompt", required=True)
    p.add_argument("--output", required=True)
    p.set_defaults(func=command_generate)

    p = sub.add_parser("edit", help="Edit using one or more input images.")
    add_common_request_options(p)
    p.add_argument("--prompt", required=True)
    p.add_argument("--input", dest="inputs", action="append")
    p.add_argument("--input-dir")
    p.add_argument("--recursive", action="store_true")
    p.add_argument("--limit", type=int)
    p.add_argument("--from-last", action="store_true")
    p.add_argument("--output", required=True)
    p.set_defaults(func=command_edit)

    p = sub.add_parser("batch-edit", help="Edit every supported image in a directory.")
    add_common_request_options(p)
    p.add_argument("--prompt", required=True)
    p.add_argument("--input-dir", required=True)
    p.add_argument("--output-dir", required=True)
    p.add_argument("--recursive", action="store_true")
    p.add_argument("--limit", type=int)
    p.set_defaults(func=command_batch_edit)

    p = sub.add_parser("last", help="Show the most recent generated/edited output path.")
    p.set_defaults(func=command_last)

    p = sub.add_parser("history", help="Show recent generation/edit history.")
    p.add_argument("--limit", type=int, default=20)
    p.set_defaults(func=command_history)

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if getattr(args, "limit", None) is not None and args.limit <= 0:
            raise CliError("--limit must be positive.")
        return int(args.func(args))
    except ApiResponseError as exc:
        if exc.status is not None:
            print("HTTP {0}".format(exc.status), file=sys.stderr)
        print("接口返回错误如下：", file=sys.stderr)
        print(exc.body, file=sys.stderr)
        if exc.status == 502:
            print("建议稍后再试。", file=sys.stderr)
        return 2
    except CliError as exc:
        print("ERROR=" + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
