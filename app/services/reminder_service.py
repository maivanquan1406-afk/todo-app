from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional
import json
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.core.config import logger, settings
from app.core.exceptions import EmailError
from app.services.todo_service import service as todo_service
from app.services.password_reset_service import send_email

try:
    _LOCAL_TIMEZONE = ZoneInfo(settings.APP_TIMEZONE)
except ZoneInfoNotFoundError:
    logger.warning("APP_TIMEZONE '%s' is invalid; falling back to UTC", settings.APP_TIMEZONE)
    _LOCAL_TIMEZONE = timezone.utc


class ReminderScheduler:
    def __init__(self) -> None:
        self._task: Optional[asyncio.Task] = None
        self._running = False
        self._interval = max(15, settings.REMINDER_CHECK_INTERVAL_SECONDS)
        self._lead_minutes = max(1, settings.REMINDER_LEAD_MINUTES)
        self._grace_minutes = max(0, settings.REMINDER_GRACE_PERIOD_MINUTES)
        self._max_lead_minutes = max(self._lead_minutes, settings.REMINDER_MAX_LEAD_MINUTES)

    def start(self) -> None:
        if not settings.REMINDER_ENABLED:
            logger.info("Reminder scheduler disabled via config")
            return
        if not self._smtp_ready():
            logger.warning("Skipping reminder scheduler because SMTP is not fully configured")
            return
        if self._task:
            return
        self._running = True
        loop = asyncio.get_event_loop()
        self._task = loop.create_task(self._run_loop())
        logger.info(
            "Reminder scheduler started (lead=%s min, interval=%s s)",
            self._lead_minutes,
            self._interval,
        )

    async def stop(self) -> None:
        self._running = False
        if not self._task:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        finally:
            self._task = None
            logger.info("Reminder scheduler stopped")

    async def _run_loop(self) -> None:
        while self._running:
            try:
                await asyncio.to_thread(self._process_once)
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Reminder scheduler tick failed")
            await asyncio.sleep(self._interval)

    def _process_once(self) -> None:
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(minutes=self._grace_minutes)
        window_end = now + timedelta(minutes=self._max_lead_minutes)
        rows = todo_service.get_due_soon_without_reminder(window_start, window_end)
        logger.debug(
            "Reminder scan window %s - %s, matches=%s",
            window_start.isoformat(),
            window_end.isoformat(),
            len(rows),
        )
        pending: list[tuple] = []
        for todo, email in rows:
            due_dt = self._coerce_utc(todo.due_date)
            if not due_dt:
                continue
            lead_minutes = self._lead_minutes
            if todo.tags:
                lead_minutes = self._extract_lead_override(todo.tags, default=lead_minutes)
            delta_minutes = (due_dt - now).total_seconds() / 60
            if delta_minutes < -self._grace_minutes:
                continue
            if delta_minutes > lead_minutes:
                continue
            pending.append((todo, email, lead_minutes))
        if not pending:
            return
        logger.info("Sending %s reminder email(s)", len(pending))
        sent_ids: list[int] = []
        for todo, email, lead_minutes in pending:
            try:
                send_email(
                    to_email=email,
                    subject=f"{settings.APP_NAME} - Nhắc nhở công việc sắp đến hạn",
                    body=self._build_email_body(todo, lead_minutes),
                )
            except EmailError:
                logger.warning("Failed to send reminder email for todo %s", todo.id, exc_info=True)
                continue
            sent_ids.append(todo.id)
        if sent_ids:
            todo_service.mark_reminders_sent(sent_ids, datetime.now(timezone.utc))

    def _build_email_body(self, todo, lead_minutes: int) -> str:
        due_display = self._format_due(todo.due_date)
        description = (todo.description or "").strip()
        lines = [
            "Xin chào,",
            "",
            f"Công việc \"{todo.title}\" chuẩn bị đến hạn lúc {due_display} (nhắc trước {lead_minutes} phút).",
        ]
        if description:
            lines.extend(["", "Ghi chú:", description])
        lines.extend(
            [
                "",
                "Bạn có thể mở ứng dụng để cập nhật trạng thái hoặc hoàn thành công việc.",
                f"-- {settings.APP_NAME}",
            ]
        )
        return "\n".join(lines)

    def _format_due(self, due: Optional[datetime]) -> str:
        if not due:
            return "không xác định"
        target = self._coerce_utc(due)
        if target is None:
            return "không xác định"
        return target.astimezone(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")

    def _smtp_ready(self) -> bool:
        return bool(
            settings.SMTP_HOST
            and settings.SMTP_USERNAME
            and settings.SMTP_PASSWORD
        )

    def _extract_lead_override(self, raw_tags: str, default: int) -> int:
        try:
            data = json.loads(raw_tags)
        except json.JSONDecodeError:
            return default
        value = data.get("reminder_minutes") if isinstance(data, dict) else None
        if isinstance(value, (int, float)) and value > 0:
            minutes = int(value)
            minutes = max(1, minutes)
            minutes = min(minutes, settings.REMINDER_MAX_LEAD_MINUTES)
            return minutes
        return default

    def _coerce_utc(self, value: Optional[datetime]) -> Optional[datetime]:
        if value is None:
            return None
        if value.tzinfo is None:
            localized = value.replace(tzinfo=_LOCAL_TIMEZONE)
        else:
            localized = value
        return localized.astimezone(timezone.utc)


reminder_scheduler = ReminderScheduler()
