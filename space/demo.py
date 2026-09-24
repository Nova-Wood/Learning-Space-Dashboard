"""Synthetic session-local preview: never reads secrets or contacts services."""
from copy import deepcopy
from datetime import datetime, timedelta
from .domain import now, TZ, month_bounds, event_span


class DemoRepository:
    def __init__(self, state):
        today = now().date()
        if "demo_db" not in state:
            state["demo_db"] = {
                "system_config": [{"id": 1, "system_name": "Novawood's Learning Space", "daily_motto": "让每一次专注，都慢慢生长。"}],
                "current_status": [{"id": 1, "is_working": False}],
                "daily_routines": [{"id": 1, "date": str(today), "breakfast": True, "lunch": True, "dinner": False, "early_sleep": False, "early_wake": True}],
                "study_log": [{"id": i+1, "date": str(today-timedelta(days=i)), "duration": 2.5+i%3*.75,
                    "task_type": "文献阅读", "period": "上午", "location": "图书馆", "details": "梳理研究框架，整理方法论笔记。", "mood": "😊 开心"} for i in range(7)],
                "tasks": [
                    {"id": 1, "task_name": "整理组会汇报的研究框架", "status": "待办", "deadline": str(today+timedelta(days=1)), "priority": "🚀 重要且紧急"},
                    {"id": 2, "task_name": "精读两篇空间分析文献", "status": "待办", "deadline": str(today+timedelta(days=3)), "priority": "📅 重要不紧急"},
                    {"id": 3, "task_name": "更新论文中的地图图例", "status": "待办", "deadline": str(today+timedelta(days=5)), "priority": "📅 重要不紧急"}],
                "reading_plan": [{"id": 1, "book_name": "空间分析方法 · 阅读笔记", "plan_content": "精读方法与讨论部分", "actual_done": "从问题出发，重新理解变量之间的关系。", "status": "阅读中"}],
                "inspirations": [{"id": 1, "create_time": now().strftime('%Y-%m-%d %H:%M'), "content": "也许可以把研究区域的日常观察，变成下一张地图的叙事线索。", "category": "🧠 科研Idea"}]}
        self.db = state["demo_db"]

    def rows(self, table, filters=(), order="id", desc=False, page=None):
        result = list(self.db[table])
        for op, column, value in filters:
            if op == "eq": result = [r for r in result if r.get(column) == value]
            if op == "gte": result = [r for r in result if r.get(column, "") >= value]
            if op == "lt": result = [r for r in result if r.get(column, "") < value]
        result.sort(key=lambda r: r.get(order) or "", reverse=desc)
        return deepcopy(result[page*200:(page+1)*200] if page is not None else result)

    def singleton(self, table): return deepcopy(self.db[table][0])

    def month_data(self, table, day):
        first, end = month_bounds(day)
        return self.rows(table, [("gte", "date", first), ("lt", "date", end)])

    def day_ideas(self, day):
        return self.rows("inspirations", [("gte", "create_time", str(day)), ("lt", "create_time", str(day+timedelta(days=1)))])

    def insert(self, table, values):
        row = {"id": max((r["id"] for r in self.db[table]), default=0)+1, **values}
        self.db[table].append(row)
        return [row]

    def update(self, table, row_id, values):
        for row in self.db[table]:
            if row["id"] == row_id:
                row.update(values)
                return [row]

    def delete(self, table, row_id):
        self.db[table] = [r for r in self.db[table] if r["id"] != row_id]

    def save_habits(self, day, values):
        row = next((r for r in self.db["daily_routines"] if r["date"] == day), None)
        if row: row.update(values)
        else: self.insert("daily_routines", {"date": day, **values})

    def start_focus(self, session_id, location, task, period):
        self.update("current_status", 1, {"is_working": True, "session_id": session_id, "location": location,
            "task_type": task, "period": period, "start_time": now().strftime('%Y-%m-%d %H:%M:%S')})

    def finish_focus(self, session_id, details, mood):
        row = self.singleton("current_status")
        start = datetime.strptime(row["start_time"], '%Y-%m-%d %H:%M:%S').replace(tzinfo=TZ)
        self.insert("study_log", {"date": str(now().date()), "period": row["period"], "task_type": row["task_type"],
            "location": row["location"], "duration": (now()-start).total_seconds()/3600, "details": details, "mood": mood})
        self.update("current_status", 1, {"is_working": False})


class DemoCalendar:
    readonly = False

    def __init__(self, state):
        self.state = state
        today = now().replace(hour=14, minute=0, second=0, microsecond=0)
        if "demo_events" not in state:
            state["demo_events"] = [{"id": "demo", "summary": "组会 · 本周研究进展", "start": {"dateTime": today.isoformat()},
                "end": {"dateTime": (today+timedelta(hours=1)).isoformat()}, "location": "研讨室"}]

    def events(self, start, end):
        return [e for e in self.state["demo_events"] if event_span(e)[0] < end and event_span(e)[1] > start]

    def create_event(self, event_id, title, start, end, description=""):
        row = {"id": event_id, "summary": title, "start": {"dateTime": start.isoformat()}, "end": {"dateTime": end.isoformat()}}
        if not any(e["id"] == event_id for e in self.state["demo_events"]): self.state["demo_events"].append(row)
        return row
