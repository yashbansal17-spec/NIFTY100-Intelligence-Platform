from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from api.main import app


def export_openapi_and_postman() -> dict[str, str]:
    """Export OpenAPI JSON and a simple Postman collection."""
    docs_dir = PROJECT_ROOT / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    openapi = app.openapi()
    openapi_path = docs_dir / "openapi.json"
    openapi_path.write_text(json.dumps(openapi, indent=2), encoding="utf-8")
    items = []
    for path, methods in openapi.get("paths", {}).items():
        for method in methods:
            if method.upper() not in {"GET", "POST", "PUT", "DELETE", "PATCH"}:
                continue
            items.append(
                {
                    "name": f"{method.upper()} {path}",
                    "request": {
                        "method": method.upper(),
                        "header": [],
                        "url": {
                            "raw": f"http://localhost:8000{path}",
                            "protocol": "http",
                            "host": ["localhost"],
                            "port": "8000",
                            "path": [part for part in path.strip("/").split("/") if part],
                        },
                    },
                }
            )
    collection = {
        "info": {
            "name": "NIFTY100 Sprint 6 API",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "item": items,
    }
    postman_path = docs_dir / "postman_collection.json"
    postman_path.write_text(json.dumps(collection, indent=2), encoding="utf-8")
    return {"openapi": str(openapi_path), "postman": str(postman_path)}


def main() -> None:
    paths = export_openapi_and_postman()
    for key, value in paths.items():
        print(f"{key}={value}")


if __name__ == "__main__":
    main()
