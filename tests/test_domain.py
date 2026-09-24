import unittest
from datetime import date, datetime
from space.domain import (TZ, month_bounds, event_span, overlapping_events, markdown_report,
                          required_text, safe_html, safe_google_link, duration_hours, valid_duration)


class DomainTests(unittest.TestCase):
    def test_invalid_legacy_durations_are_excluded_and_flagged(self):
        for value in [-7.98, float('nan'), float('inf'), None, 'bad']:
            self.assertFalse(valid_duration(value))
            self.assertEqual(duration_hours(value), 0)
        logs = [{'date':'2026-04-03','duration':-7.98}, {'date':'2026-04-03','duration':1.5}]
        report = markdown_report('2026-04-03', logs, [], [])
        self.assertIn('1.50 小时', report)
        self.assertIn('时长异常，未计入统计', report)
        self.assertEqual(logs[0]['duration'], -7.98)

    def test_month_bounds_keep_year_and_rollover(self):
        self.assertEqual(month_bounds(date(2026, 12, 15)), ('2026-12-01', '2027-01-01'))
        self.assertEqual(month_bounds(date(2024, 2, 29)), ('2024-02-01', '2024-03-01'))

    def test_empty_values_rejected(self):
        for text in ['', '   ', '\n']:
            with self.assertRaises(ValueError): required_text(text, '标题')
        self.assertEqual(required_text(' a ', '标题'), 'a')

    def test_markup_and_link_validation(self):
        self.assertEqual(safe_html('<script>'), '&lt;script&gt;')
        self.assertIsNone(safe_google_link('javascript:alert(1)'))
        self.assertIsNone(safe_google_link('https://calendar.google.com.evil.example/event'))
        self.assertEqual(safe_google_link('https://calendar.google.com/event'), 'https://calendar.google.com/event')

    def test_all_day_exclusive_end(self):
        event = {'start': {'date': '2026-09-24'}, 'end': {'date': '2026-09-25'}}
        start, end, all_day = event_span(event)
        self.assertTrue(all_day)
        self.assertEqual((end-start).total_seconds(), 86400)
        self.assertFalse(overlapping_events([event], end, end.replace(hour=1)))

    def test_timezone_and_conflicts(self):
        event = {'start': {'dateTime': '2026-09-24T01:00:00Z'}, 'end': {'dateTime': '2026-09-24T02:00:00Z'}}
        self.assertEqual(event_span(event)[0].hour, 9)
        start = datetime(2026, 9, 24, 9, 30, tzinfo=TZ)
        end = datetime(2026, 9, 24, 10, 30, tzinfo=TZ)
        self.assertEqual(len(overlapping_events([event], start, end)), 1)
        self.assertFalse(overlapping_events([{**event, 'transparency': 'transparent'}], start, end))
        self.assertFalse(overlapping_events([{**event, 'status': 'cancelled'}], start, end))

    def test_report_empty_database_and_day_filter(self):
        report = markdown_report('2026-09-24', [], [], [])
        self.assertIn('0.00', report)
        logs = [{'date':'2025-09-24','duration':9}, {'date':'2026-09-24','duration':2,'task_type':'阅读'}]
        self.assertIn('2.00 小时', markdown_report('2026-09-24', logs, [], []))
        self.assertNotIn('9.00', markdown_report('2026-09-24', logs, [], []))
