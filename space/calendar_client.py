"""Google Calendar OAuth integration; tokens stay on the Streamlit server."""
import time
from threading import Lock
from urllib.parse import quote
import requests
from .domain import required_text


class CalendarError(RuntimeError):
    pass


class CalendarClient:
    def __init__(self, config, transport=None):
        self.config = dict(config)
        self.transport = transport or requests.Session()
        self.token = None
        self.expires = 0
        self.lock = Lock()
        self.readonly = bool(self.config.get("readonly", False))
        calendar_id = self.config.get("calendar_id", "primary")
        self.url = f"https://www.googleapis.com/calendar/v3/calendars/{quote(calendar_id, safe='')}/events"

    def access_token(self):
        with self.lock:
            if self.token and time.monotonic() < self.expires:
                return self.token
            try:
                response = self.transport.post("https://oauth2.googleapis.com/token", data={
                    "client_id": self.config["client_id"], "client_secret": self.config["client_secret"],
                    "refresh_token": self.config["refresh_token"], "grant_type": "refresh_token"}, timeout=20)
                if response.status_code != 200:
                    raise CalendarError("Google 授权已失效或配置不正确，请重新连接日历。")
                data = response.json()
                self.token = data["access_token"]
                self.expires = time.monotonic() + max(0, int(data.get("expires_in", 3600)) - 60)
                return self.token
            except (requests.RequestException, KeyError, ValueError) as exc:
                raise CalendarError("暂时无法连接 Google，请检查网络和日历配置。") from exc

    def request(self, method, path="", **kwargs):
        for attempt in range(2):
            token = self.access_token()
            try:
                response = self.transport.request(method, self.url + path,
                    headers={"Authorization": f"Bearer {token}"}, timeout=20, **kwargs)
            except requests.RequestException as exc:
                raise CalendarError("日历连接中断。若正在创建日程，请保持当前页面并重试，系统会避免重复创建。") from exc
            if response.status_code == 401 and attempt == 0:
                with self.lock:
                    self.token = None
                continue
            if response.status_code == 409:
                return None
            if response.status_code == 403:
                raise CalendarError("当前授权无权执行此操作，请检查日历权限或 Google API 配额。")
            if response.status_code >= 400:
                raise CalendarError("日历请求失败，请检查日历编号或稍后重试。")
            return response.json()
        raise CalendarError("Google 授权已过期，请重新连接。")

    def events(self, start, end):
        params = {"timeMin": start.isoformat(), "timeMax": end.isoformat(), "singleEvents": "true",
                  "orderBy": "startTime", "showDeleted": "false", "maxResults": 250, "timeZone": "Asia/Shanghai"}
        result = []
        while True:
            data = self.request("GET", params=dict(params))
            result.extend(row for row in data.get("items", []) if row.get("status") != "cancelled")
            token = data.get("nextPageToken")
            if not token:
                return result
            params["pageToken"] = token

    def create_event(self, event_id, title, start, end, description=""):
        if self.readonly:
            raise CalendarError("当前日历为只读模式。")
        title = required_text(title, "日程标题", 200)
        if start.tzinfo is None or end.tzinfo is None or end <= start:
            raise ValueError("结束时间必须晚于开始时间，并包含时区。")
        if len(description) > 5000:
            raise ValueError("日程备注请控制在 5000 字以内。")
        body = {"id": event_id, "summary": title, "description": description,
                "start": {"dateTime": start.isoformat(), "timeZone": "Asia/Shanghai"},
                "end": {"dateTime": end.isoformat(), "timeZone": "Asia/Shanghai"},
                "extendedProperties": {"private": {"source": "learning-space"}}}
        data = self.request("POST", json=body, params={"sendUpdates": "none"})
        # Same ID survives retries, including an ambiguous response after a write.
        if data is None:
            data = self.request("GET", "/" + quote(event_id, safe=""))
            if data.get("status") == "cancelled":
                raise CalendarError("这条日程已在 Google 日历删除，请刷新页面后重新安排。")
            expected = body["extendedProperties"]["private"]
            if data.get("extendedProperties", {}).get("private") != expected:
                raise CalendarError("日程编号冲突，请刷新页面后重试。")
        return data
