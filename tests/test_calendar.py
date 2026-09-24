import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock
import requests
from space.domain import TZ
from space.calendar_client import CalendarClient, CalendarError


def response(status, data):
    value = MagicMock(status_code=status)
    value.json.return_value = data
    return value


class CalendarTests(unittest.TestCase):
    def setUp(self):
        self.transport = MagicMock()
        self.transport.post.return_value = response(200, {'access_token':'private-token','expires_in':3600})
        self.client = CalendarClient({'client_id':'id','client_secret':'secret','refresh_token':'refresh',
                                      'calendar_id':'someone@example.com'}, self.transport)
        self.start = datetime(2026,9,24,9,tzinfo=TZ)
        self.end = self.start+timedelta(hours=1)

    def test_all_pages_and_cancelled_items(self):
        self.transport.request.side_effect = [response(200, {'items':[{'id':'1'}], 'nextPageToken':'next'}),
                                               response(200, {'items':[{'id':'2'},{'id':'3','status':'cancelled'}]})]
        self.assertEqual([r['id'] for r in self.client.events(self.start,self.end)], ['1','2'])
        params = self.transport.request.call_args.kwargs['params']
        self.assertEqual(params['pageToken'], 'next')
        self.assertEqual(params['singleEvents'], 'true')
        self.assertTrue(params['timeMin'].endswith('+08:00'))
        self.transport.post.assert_called_once()

    def test_retry_unauthorized_refreshes_token(self):
        self.transport.request.side_effect = [response(401,{}), response(200,{'items':[]})]
        self.assertEqual(self.client.events(self.start,self.end), [])
        self.assertEqual(self.transport.post.call_count,2)

    def test_duplicate_creation_uses_existing_event(self):
        event = {'id':'abcd','extendedProperties':{'private':{'source':'learning-space'}}}
        self.transport.request.side_effect = [response(409,{}), response(200,event)]
        self.assertEqual(self.client.create_event('abcd','阅读',self.start,self.end),event)
        first = self.transport.request.call_args_list[0]
        self.assertEqual(first.args[0], 'POST')
        self.assertEqual(first.kwargs['json']['id'], 'abcd')
        self.assertNotIn('attendees', first.kwargs['json'])

    def test_readonly_and_invalid_dates_never_write(self):
        with self.assertRaises(ValueError): self.client.create_event('id','阅读',self.end,self.start)
        self.client.readonly=True
        with self.assertRaises(CalendarError): self.client.create_event('id','阅读',self.start,self.end)
        self.transport.request.assert_not_called()

    def test_revoked_grant_is_safe(self):
        self.transport.post.return_value = response(400, {'error':'invalid_grant','private':'secret'})
        with self.assertRaises(CalendarError) as context: self.client.events(self.start,self.end)
        self.assertNotIn('secret',str(context.exception))

    def test_network_failure_is_retryable(self):
        self.transport.request.side_effect = requests.Timeout()
        with self.assertRaisesRegex(CalendarError,'重试'): self.client.create_event('id','阅读',self.start,self.end)
