"""Operational commands: ``python -m app.cli {purge,create-user,export-openapi,warmup}``."""

from __future__ import annotations

import argparse
import json
import sys


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="app.cli")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("purge", help="apply the retention policy now")
    cu = sub.add_parser("create-user", help="create a user + personal workspace")
    cu.add_argument("--email", required=True)
    cu.add_argument("--password", required=True)
    cu.add_argument("--name")
    oa = sub.add_parser("export-openapi", help="write the OpenAPI document")
    oa.add_argument("--out", default="-")
    sub.add_parser("warmup", help="download/load OCR models")
    args = ap.parse_args(argv)

    if args.cmd == "purge":
        from app.services.retention import purge

        print(json.dumps(purge()))
    elif args.cmd == "create-user":
        from app.db import get_sessionmaker
        from app.models import Membership, User, Workspace
        from app.security import hash_password

        with get_sessionmaker()() as db:
            u = User(email=args.email.lower(), password_hash=hash_password(args.password), display_name=args.name)
            db.add(u)
            db.flush()
            ws = Workspace(name=f"{args.name or args.email}'s workspace", owner_id=u.id)
            db.add(ws)
            db.flush()
            db.add(Membership(workspace_id=ws.id, user_id=u.id, role="owner"))
            db.commit()
            print(json.dumps({"user_id": str(u.id), "workspace_id": str(ws.id)}))
    elif args.cmd == "export-openapi":
        from app.main import app

        doc = json.dumps(app.openapi(), indent=2, ensure_ascii=False)
        if args.out == "-":
            sys.stdout.write(doc)
        else:
            open(args.out, "w", encoding="utf-8").write(doc)
    elif args.cmd == "warmup":
        from app.ocr_runtime import get_engine

        eng = get_engine()
        getattr(eng.provider, "warmup", lambda: None)()
        print(json.dumps([m.model_dump() for m in eng.provider.models()]))


if __name__ == "__main__":
    main()
