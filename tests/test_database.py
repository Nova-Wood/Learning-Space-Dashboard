"""Integration tests against an explicitly disposable local PostgreSQL database."""
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from urllib.parse import urlparse
import unittest
import uuid

URL = os.environ.get('TEST_DATABASE_URL')


@unittest.skipUnless(URL, 'Set TEST_DATABASE_URL to a disposable local *_test database')
class DatabaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import psycopg
        parsed = urlparse(URL)
        if parsed.hostname not in {'localhost','127.0.0.1','postgres'} or not parsed.path.endswith('_test'):
            raise RuntimeError('Database tests only run against a disposable local *_test database')
        cls.driver = psycopg
        cls.db = psycopg.connect(URL, autocommit=True)
        cls.db.execute("""do $$ begin
          if not exists(select 1 from pg_roles where rolname='anon') then create role anon; end if;
          if not exists(select 1 from pg_roles where rolname='authenticated') then create role authenticated; end if;
          if not exists(select 1 from pg_roles where rolname='service_role') then create role service_role bypassrls; end if;
        end $$;""")
        cls.migration = (Path(__file__).resolve().parents[1] / 'supabase/migrations/001_reliable_workspace.sql').read_text(encoding='utf-8')
        cls.db.execute(cls.migration)
        cls.db.execute(cls.migration)  # Re-applying must preserve compatibility.

    @classmethod
    def tearDownClass(cls): cls.db.close()

    def setUp(self):
        self.db.execute('truncate public.study_log, public.tasks, public.reading_plan, public.inspirations, public.daily_routines')
        self.db.execute('update public.current_status set is_working=false, session_id=null where id=1')

    def start(self, session=None, db=None):
        session = session or uuid.uuid4()
        (db or self.db).execute('select * from public.start_focus(%s,%s,%s,%s)', (session,'图书馆','文献阅读','上午')).fetchall()
        return session

    def finish(self, session, db=None):
        return (db or self.db).execute('select * from public.finish_focus(%s,%s,%s)', (session,'进展','开心')).fetchall()

    def test_atomic_finish_and_replay(self):
        session = self.start()
        self.db.execute("update public.current_status set start_time=to_char((clock_timestamp() at time zone 'Asia/Shanghai')-interval '1 hour','YYYY-MM-DD HH24:MI:SS') where id=1")
        first = self.finish(session)
        self.assertTrue(first)
        self.assertEqual(self.finish(session), first)
        self.assertFalse(self.db.execute('select is_working from current_status where id=1').fetchone()[0])

    def test_cross_midnight_split(self):
        session = self.start()
        self.db.execute("update current_status set start_time=to_char(date_trunc('day',clock_timestamp() at time zone 'Asia/Shanghai')-interval '1 hour','YYYY-MM-DD HH24:MI:SS') where id=1")
        self.finish(session)
        rows = self.db.execute('select date,duration from study_log order by date').fetchall()
        self.assertEqual(len(rows),2)
        self.assertAlmostEqual(rows[0][1],1.0)
        self.assertNotEqual(rows[0][0],rows[1][0])

    def test_failed_status_write_rolls_back_log(self):
        session = self.start()
        self.db.execute("""create or replace function public.test_fail_finish() returns trigger language plpgsql as $$
          begin if new.is_working=false then raise exception 'simulated write failure'; end if; return new; end $$;
          create trigger fail_finish before update on public.current_status for each row execute function public.test_fail_finish();""")
        try:
            with self.assertRaises(self.driver.Error): self.finish(session)
            self.assertEqual(self.db.execute('select count(*) from study_log').fetchone()[0],0)
            self.assertTrue(self.db.execute('select is_working from current_status').fetchone()[0])
        finally:
            self.db.execute('drop trigger fail_finish on public.current_status; drop function public.test_fail_finish()')

    def test_stale_finish_does_not_stop_new_session(self):
        old = self.start()
        self.finish(old)
        new = self.start()
        self.finish(old)
        self.assertEqual(self.db.execute('select session_id,is_working from current_status').fetchone(), (new,True))

    def test_concurrent_starts_only_one_wins(self):
        barrier = Barrier(2)
        def attempt(_):
            with self.driver.connect(URL, autocommit=True) as db:
                barrier.wait(timeout=10)
                try: self.start(db=db); return True
                except self.driver.Error: return False
        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual(sum(pool.map(attempt,range(2))),1)

    def test_concurrent_finish_logs_once(self):
        session = self.start()
        self.db.execute("update current_status set start_time=to_char((clock_timestamp() at time zone 'Asia/Shanghai')-interval '5 minutes','YYYY-MM-DD HH24:MI:SS')")
        barrier = Barrier(2)
        def attempt(_):
            with self.driver.connect(URL, autocommit=True) as db:
                barrier.wait(timeout=10)
                return self.finish(session,db)
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(attempt,range(2)))
        self.assertEqual(results[0],results[1])
        self.assertEqual(self.db.execute('select count(*) from study_log').fetchone()[0],len(results[0]))

    def test_anonymous_access_denied_service_role_allowed(self):
        for role in ['anon','authenticated']:
            self.db.execute('set role '+role)
            try:
                with self.assertRaises(self.driver.errors.InsufficientPrivilege): self.db.execute('select * from study_log')
                with self.assertRaises(self.driver.errors.InsufficientPrivilege): self.start()
            finally: self.db.execute('reset role')
        self.db.execute('set role service_role')
        try: self.start()
        finally: self.db.execute('reset role')

    def test_habit_upsert_keeps_one_row(self):
        for value in [False,True]:
            self.db.execute("insert into daily_routines(date,breakfast) values('2026-09-24',%s) on conflict(date) do update set breakfast=excluded.breakfast",(value,))
        self.assertEqual(self.db.execute('select date,breakfast from daily_routines').fetchall(), [('2026-09-24',True)])

    def test_migration_preserves_existing_data(self):
        self.db.execute("insert into inspirations(create_time,content,category) values('2026-09-24 12:00','保留的想法','想法')")
        self.db.execute(self.migration)
        self.assertEqual(self.db.execute('select content from inspirations').fetchone()[0],'保留的想法')

    def test_legacy_habit_table_without_id(self):
        self.db.execute('alter table daily_routines drop column id')
        self.db.execute("insert into daily_routines(date,breakfast) values('2026-09-24',true)")
        self.db.execute(self.migration)
        self.assertEqual(self.db.execute('select date,breakfast from daily_routines order by id').fetchall(), [('2026-09-24',True)])
