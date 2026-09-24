"""Pure date, validation and export logic; no UI or network dependencies."""
from datetime import date, datetime, time, timedelta, timezone
from html import escape
import math

TZ = timezone(timedelta(hours=8))
PERIODS = ["上午", "下午", "晚上", "深夜"]
PRIORITIES = ["🚀 重要且紧急", "📅 重要不紧急", "⚡ 紧急不重要", "☁️ 不重要不紧急"]
HABITS = {"breakfast": "早餐", "lunch": "午餐", "dinner": "晚餐", "early_sleep": "早睡", "early_wake": "早起"}


def now():
    return datetime.now(TZ)


def month_bounds(day):
    first = day.replace(day=1)
    following = (first + timedelta(days=32)).replace(day=1)
    return first.isoformat(), following.isoformat()


def required_text(value, label, limit=500):
    value = value.strip()
    if not value:
        raise ValueError(f"请填写{label}。")
    if len(value) > limit:
        raise ValueError(f"{label}请控制在 {limit} 字以内。")
    return value


def safe_html(value):
    return escape(str(value or ""), quote=True)


def valid_duration(value):
    try:
        hours = float(value)
    except (TypeError, ValueError, OverflowError):
        return False
    return math.isfinite(hours) and hours >= 0


def duration_hours(value):
    """Exclude invalid legacy values without rewriting the original record."""
    return float(value) if valid_duration(value) else 0.0


def safe_google_link(value):
    from urllib.parse import urlparse
    parsed = urlparse(value or "")
    return value if parsed.scheme == "https" and parsed.hostname in {"www.google.com", "calendar.google.com"} else None


def event_span(event):
    """Google all-day end dates are exclusive; timed values include offsets."""
    start, end = event["start"], event["end"]
    if "date" in start:
        return (datetime.combine(date.fromisoformat(start["date"]), time.min, TZ),
                datetime.combine(date.fromisoformat(end["date"]), time.min, TZ), True)
    return (datetime.fromisoformat(start["dateTime"].replace("Z", "+00:00")).astimezone(TZ),
            datetime.fromisoformat(end["dateTime"].replace("Z", "+00:00")).astimezone(TZ), False)


def overlapping_events(events, start, end):
    return [event for event in events
            if event.get("status") != "cancelled" and event.get("transparency") != "transparent"
            and event_span(event)[0] < end and start < event_span(event)[1]]


def markdown_report(day, logs, routines, inspirations):
    routine = next((r for r in routines if r["date"] == day), {})
    today_logs = [row for row in logs if row["date"] == day]
    text = [f"# 科研日报 | {day}", "", "## 习惯打卡"]
    text.extend(f"- {'✅' if routine.get(key) else '⬜'} {label}" for key, label in HABITS.items())
    total = sum(duration_hours(row.get("duration")) for row in today_logs)
    text += ["", f"## 专注记录 · {total:.2f} 小时"]
    for row in today_logs:
        hours = f"{duration_hours(row.get('duration')):.2f}h" if valid_duration(row.get('duration')) else "时长异常，未计入统计"
        text.append(f"- **{row.get('task_type', '')}** · {row.get('period', '')} · {hours}\n  {row.get('details') or '未填写备注'} {row.get('mood') or ''}")
    if not today_logs:
        text.append("- 今天还没有完成的专注记录。")
    text += ["", "## 灵感捕捉"]
    today_ideas = [row for row in inspirations if str(row.get("create_time", "")).startswith(day)]
    text.extend(f"- [{row.get('category', '')}] {row.get('content', '')}" for row in today_ideas)
    if not today_ideas:
        text.append("- 今天还没有灵感记录。")
    return "\n".join(text) + "\n"
