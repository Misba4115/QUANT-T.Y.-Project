"""Reproducible, signed dashboard PDF and chart PNG exports."""
from __future__ import annotations

import hashlib
import io
import json
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from jose import JWTError, jwt
from PIL import Image, ImageDraw, ImageFont

from core.config import get_settings
from services.dashboard_aggregator import DashboardAggregator


def _money(value: Any) -> str:
    return f"INR {float(value or 0):,.2f}"


def _pdf_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _simple_pdf(lines: list[str]) -> bytes:
    commands = ["BT", "/F1 11 Tf", "50 790 Td", "14 TL"]
    for index, line in enumerate(lines):
        if index:
            commands.append("T*")
        commands.append(f"({_pdf_escape(line[:110])}) Tj")
    commands.append("ET")
    stream = "\n".join(commands).encode("latin-1", errors="replace")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    output = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{index} 0 obj\n".encode() + obj + b"\nendobj\n")
    xref = len(output)
    output.extend(f"xref\n0 {len(objects)+1}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode())
    output.extend(f"trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode())
    return bytes(output)


class ReportExportService:
    def __init__(self, db: Any):
        self.db = db
        self.settings = get_settings()
        self.signing_secret = self.settings.export_signing_secret or self.settings.jwt_secret_key

    def request(self, user_id: str, *, format: str, params: dict[str, Any]) -> dict[str, Any]:
        result = DashboardAggregator(self.db).aggregate(
            user_id, params.get("time_period", "1y"), params.get("date_from"), params.get("date_to")
        )
        export_id = str(uuid4())
        expiry = datetime.now(timezone.utc) + timedelta(minutes=5)
        stored_params = json.loads(json.dumps(
            {**params, "snapshot": result, "generated_at": datetime.now(timezone.utc).isoformat()},
            default=str,
        ))
        self.db.table("report_exports").insert(
            {
                "report_export_id": export_id, "user_id": user_id, "format": format,
                "status": "processing", "params": stored_params, "expires_at": expiry.isoformat(),
            }
        ).execute()
        token = jwt.encode(
            {"sub": user_id, "export_id": export_id, "exp": expiry},
            self.signing_secret, algorithm=self.settings.jwt_algorithm,
        )
        return {"report_export_id": export_id, "download_token": token, "expires_at": expiry.isoformat()}

    def render(self, user_id: str, export_id: str, token: str) -> tuple[str, str, bytes]:
        try:
            claims = jwt.decode(token, self.signing_secret, algorithms=[self.settings.jwt_algorithm])
        except JWTError as exc:
            raise ValueError("Export token is invalid or expired") from exc
        if claims.get("sub") != user_id or claims.get("export_id") != export_id:
            raise ValueError("Export token does not match this user or report")
        rows = self.db.table("report_exports").select("*").eq("report_export_id", export_id).eq(
            "user_id", user_id
        ).limit(1).execute().data or []
        if not rows:
            raise ValueError("Export not found")
        row, params = rows[0], rows[0]["params"]
        if datetime.fromisoformat(str(row["expires_at"]).replace("Z", "+00:00")) <= datetime.now(timezone.utc):
            self.db.table("report_exports").update({"status": "expired"}).eq("report_export_id", export_id).execute()
            raise ValueError("Export has expired")
        result = params["snapshot"]
        if row["format"] == "pdf":
            content, media, filename = self._pdf(result, params), "application/pdf", f"quant-dashboard-{export_id[:8]}.pdf"
        else:
            content, media, filename = self._png(result, params), "image/png", f"quant-chart-{export_id[:8]}.png"
        digest = hashlib.sha256(content).hexdigest()
        self.db.table("report_exports").update(
            {"status": "completed", "content_hash": digest, "completed_at": datetime.now(timezone.utc).isoformat()}
        ).eq("report_export_id", export_id).eq("user_id", user_id).execute()
        return filename, media, content

    @staticmethod
    def _pdf(result: dict[str, Any], params: dict[str, Any]) -> bytes:
        lines = [
            "QUANT - Verified Financial Report",
            f"Generated: {params['generated_at']}", f"Data as of: {result['data_as_of']}",
            f"Period: {params.get('time_period', '1y')}", f"Net worth: {_money(result['net_worth'])}",
            f"Valuation coverage: {float(result['valuation_coverage'])*100:.1f}% ({result['valuation_status']})",
            f"Current-month surplus: {_money(result['surplus'])}", "", "Allocation",
        ]
        lines.extend(f"- {item['name']}: {item['value']:.2f}% ({_money(item.get('amount'))})" for item in result["asset_allocation"])
        lines.extend(["", "Top holdings"])
        lines.extend(
            f"- {item['instrument']} | {item['type']} | {_money(item['current_value'])} | {item.get('price_source') or item['valuation_status']}"
            for item in result["top_holdings"]
        )
        lines.extend(["", "Sources and warnings", json.dumps(result.get("source_status") or {}, sort_keys=True)])
        if result["valuation_status"] != "market_valued":
            lines.append("Warning: some values use recorded cost basis because current prices are unavailable.")
        return _simple_pdf(lines)

    @staticmethod
    def _png(result: dict[str, Any], params: dict[str, Any]) -> bytes:
        image = Image.new("RGB", (1200, 700), "#f8fafc")
        draw, font = ImageDraw.Draw(image), ImageFont.load_default()
        draw.text((50, 35), "QUANT Portfolio History", fill="#0f172a", font=font)
        draw.text((50, 58), f"Period: {params.get('time_period', '1y')} | Data as of: {result['data_as_of']}", fill="#475569", font=font)
        history = result.get("portfolio_history") or []
        left, top, right, bottom = 70, 110, 1150, 590
        draw.rectangle((left, top, right, bottom), outline="#cbd5e1", width=2)
        if len(history) >= 2:
            values = [float(item["value"]) for item in history]
            low, high = min(values), max(values)
            span = max(high - low, 1.0)
            points = [
                (left + index * (right-left)/(len(values)-1), bottom - (value-low)/span*(bottom-top))
                for index, value in enumerate(values)
            ]
            draw.line(points, fill="#2563eb", width=4)
            draw.text((left, bottom+18), str(history[0]["month"]), fill="#475569", font=font)
            draw.text((right-90, bottom+18), str(history[-1]["month"]), fill="#475569", font=font)
        else:
            draw.text((430, 340), "Insufficient recorded snapshot history", fill="#64748b", font=font)
        draw.text((50, 650), f"Valuation coverage: {float(result['valuation_coverage'])*100:.1f}% | {result['valuation_status']}", fill="#475569", font=font)
        output = io.BytesIO()
        image.save(output, format="PNG", optimize=True)
        return output.getvalue()
