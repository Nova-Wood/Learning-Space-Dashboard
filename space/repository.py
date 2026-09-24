"""Server-only Supabase access. Pagination never assumes the API's row cap."""
from .domain import HABITS, month_bounds


class StorageError(RuntimeError):
    pass


class Repository:
    PAGE_SIZE = 200

    def __init__(self, client):
        self.client = client

    def execute(self, query):
        try:
            return query.execute().data or []
        except Exception as exc:
            # Do not expose credentials, SQL or private payloads through API errors.
            raise StorageError("数据暂时无法保存或读取。请稍后重试；首次部署请检查数据库迁移与服务端密钥。") from exc

    def rows(self, table, filters=(), order="id", desc=False, page=None):
        result, offset = [], (page or 0) * self.PAGE_SIZE
        while True:
            query = self.client.table(table).select("*")
            for operation, column, value in filters:
                query = getattr(query, operation)(column, value)
            batch = self.execute(query.order(order, desc=desc).range(offset, offset + self.PAGE_SIZE - 1))
            result.extend(batch)
            # An API row cap may be lower than PAGE_SIZE: continue until empty.
            if page is not None or not batch:
                return result
            offset += len(batch)

    def singleton(self, table):
        rows = self.rows(table, [("eq", "id", 1)])
        if not rows:
            raise StorageError("初始化记录缺失，请先执行仓库中的数据库迁移。")
        return rows[0]

    def month_data(self, table, day):
        first, following = month_bounds(day)
        return self.rows(table, [("gte", "date", first), ("lt", "date", following)])

    def day_ideas(self, day):
        from datetime import timedelta
        return self.rows("inspirations", [("gte", "create_time", day.isoformat()),
                                         ("lt", "create_time", (day + timedelta(days=1)).isoformat())])

    def insert(self, table, values):
        return self.execute(self.client.table(table).insert(values))

    def update(self, table, row_id, values):
        rows = self.execute(self.client.table(table).update(values).eq("id", row_id))
        if not rows:
            raise StorageError("这条记录已变化或不存在，请刷新后重试。")
        return rows

    def delete(self, table, row_id):
        return self.execute(self.client.table(table).delete().eq("id", row_id))

    def save_habits(self, day, values):
        payload = {"date": day, **{key: bool(values.get(key)) for key in HABITS}}
        return self.execute(self.client.table("daily_routines").upsert(payload, on_conflict="date"))

    def start_focus(self, session_id, location, task, period):
        return self.execute(self.client.rpc("start_focus", {"p_session_id": session_id,
                            "p_location": location, "p_task_type": task, "p_period": period}))

    def finish_focus(self, session_id, details, mood):
        return self.execute(self.client.rpc("finish_focus", {"p_session_id": session_id,
                            "p_details": details, "p_mood": mood}))
