import unittest
from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock
from space.repository import Repository, StorageError


class Query:
    def __init__(self, data, cap=2):
        self.data, self.cap = data, cap
        self.filters = []
    def select(self, *args): return self
    def order(self, *args, **kwargs): return self
    def eq(self, key, val): self.filters.append(('eq', key, val)); return self
    def gte(self, key, val): self.filters.append(('gte', key, val)); return self
    def lt(self, key, val): self.filters.append(('lt', key, val)); return self
    def range(self, start, end): self.start, self.end = start, end; return self
    def execute(self):
        data = self.data
        for op, key, val in self.filters:
            data = [r for r in data if {'eq':r[key] == val, 'gte':r[key] >= val, 'lt':r[key] < val}[op]]
        return SimpleNamespace(data=data[self.start:min(self.end+1, self.start+self.cap)])


class RepositoryTests(unittest.TestCase):
    def test_pagination_with_api_cap_smaller_than_page_size(self):
        data = [{'id':n} for n in range(1003)]
        repo = Repository(SimpleNamespace(table=lambda _: Query(data, cap=73)))
        self.assertEqual(repo.rows('study_log'), data)

    def test_month_query_excludes_last_year(self):
        data = [{'id':1,'date':'2025-09-24'}, {'id':2,'date':'2026-09-24'}, {'id':3,'date':'2026-10-01'}]
        repo = Repository(SimpleNamespace(table=lambda _: Query(data)))
        self.assertEqual(repo.month_data('study_log', date(2026,9,24)), [data[1]])

    def test_empty_singleton_is_actionable(self):
        repo = Repository(SimpleNamespace(table=lambda _: Query([])))
        with self.assertRaisesRegex(StorageError, '初始化'): repo.singleton('system_config')

    def test_api_errors_do_not_leak_details(self):
        query = MagicMock()
        query.execute.side_effect = RuntimeError('secret-token=abc')
        with self.assertRaises(StorageError) as context: Repository(None).execute(query)
        self.assertNotIn('abc', str(context.exception))

    def test_habits_upsert_unique_date(self):
        client = MagicMock()
        client.table.return_value.upsert.return_value.execute.return_value.data = []
        Repository(client).save_habits('2026-09-24', {'breakfast': True})
        payload = client.table.return_value.upsert.call_args
        self.assertEqual(payload.kwargs, {'on_conflict':'date'})
        self.assertEqual(payload.args[0]['date'], '2026-09-24')
        self.assertIs(payload.args[0]['dinner'], False)
