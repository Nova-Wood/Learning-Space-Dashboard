import os
from pathlib import Path
import unittest
from unittest.mock import patch
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / 'app.py')


def button(at, label): return next(b for b in at.button if b.label == label)
def input_by_label(elements, label): return next(e for e in elements if e.label == label)


class AppTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {'LEARNING_SPACE_DEMO':'1'})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.at = AppTest.from_file(APP, default_timeout=30).run()

    def page(self, name):
        self.at.sidebar.radio[0].set_value(name).run()
        self.assertFalse(self.at.exception)

    def test_all_pages_render(self):
        for page in ['今日概览','任务与日程','阅读与灵感','记录与统计','设置']:
            self.page(page)
            self.assertFalse(self.at.error)

    def test_focus_start_finish(self):
        button(self.at,'开始专注 →').click().run()
        self.assertTrue(self.at.session_state['demo_db']['current_status'][0]['is_working'])
        button(self.at,'完成这次专注').click().run()
        self.assertFalse(self.at.exception)
        self.assertFalse(self.at.session_state['demo_db']['current_status'][0]['is_working'])
        self.assertEqual(len(self.at.session_state['demo_db']['study_log']),8)

    def test_reading_draft_saved_without_completion(self):
        self.page('阅读与灵感')
        input_by_label(self.at.text_area,'阅读笔记').set_value('独立保存的新笔记')
        button(self.at,'保存笔记').click().run()
        row = self.at.session_state['demo_db']['reading_plan'][0]
        self.assertEqual(row['actual_done'],'独立保存的新笔记')
        self.assertEqual(row['status'],'阅读中')

    def test_task_complete_restore(self):
        self.page('任务与日程')
        self.at.button(key='done_1').click().run()
        self.assertFalse(self.at.exception)
        self.assertEqual(self.at.session_state['demo_db']['tasks'][0]['status'],'已完成')
        self.at.button(key='restore_task_1').click().run()
        self.assertEqual(self.at.session_state['demo_db']['tasks'][0]['status'],'待办')

    def test_calendar_creation(self):
        self.page('任务与日程')
        input_by_label(self.at.text_input,'日程标题').set_value('阅读安排')
        button(self.at,'添加到 Google 日历').click().run()
        self.assertFalse(self.at.exception)
        self.assertEqual(len(self.at.session_state['demo_events']),2)
        button(self.at,'添加到 Google 日历').click().run()
        self.assertFalse(self.at.exception)
        self.assertFalse(self.at.warning)
        self.assertEqual(len(self.at.session_state['demo_events']),2)

    def test_empty_title_rejected(self):
        self.page('任务与日程')
        button(self.at,'保存任务').click().run()
        self.assertFalse(self.at.exception)
        self.assertTrue(self.at.error)
        self.assertEqual(len(self.at.session_state['demo_db']['tasks']),3)

    def test_report_survives_rerun_with_empty_data(self):
        self.at.session_state['demo_db']['study_log'] = []
        self.at.session_state['demo_db']['daily_routines'] = []
        self.page('记录与统计')
        button(self.at,'生成 Markdown 日报').click().run()
        report = self.at.session_state['report']
        self.at.run()
        self.assertEqual(self.at.session_state['report'], report)
        self.assertFalse(self.at.exception)


class AuthTests(unittest.TestCase):
    def test_no_secrets_is_friendly(self):
        with patch.dict(os.environ, {'LEARNING_SPACE_DEMO':'0'}):
            at = AppTest.from_file(APP).run()
        self.assertFalse(at.exception)
        self.assertTrue(at.info)

    def test_legacy_url_key_never_logs_in(self):
        with patch.dict(os.environ, {'LEARNING_SPACE_DEMO':'0'}):
            at = AppTest.from_file(APP)
            at.secrets['APP_PASSWORD'] = 'test-only-password'
            at.query_params['key'] = 'test-only-password'
            at.run()
            self.assertFalse(at.exception)
            self.assertTrue(at.text_input)
            self.assertNotIn('auth', at.session_state)
            self.assertNotIn('key', at.query_params)
