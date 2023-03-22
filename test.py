import unittest
import json
from main import app


class TestAPI(unittest.TestCase):
    
    def setUp(self):
        app.testing = True
        self.client = app.test_client()

    def test_get_users(self):
        response = self.client.get('/users')
        self.assertEqual(response.status_code, 200)
        users = json.loads(response.data)
        self.assertTrue(isinstance(users, list))
        self.assertTrue(len(users) > 0)

    def test_get_attended_events(self):
        response = self.client.get('/users/1/events')
        self.assertEqual(response.status_code, 200)
        events = json.loads(response.data)
        self.assertTrue(isinstance(events, list))

    def test_get_user_meetings(self):
        response = self.client.get('/users/1/meetings')
        self.assertEqual(response.status_code, 200)
        meetings = json.loads(response.data)
        self.assertTrue(isinstance(meetings, list))

    def test_get_user_invitations(self):
        response = self.client.get('/users/1/invitations')
        self.assertEqual(response.status_code, 200)
        invitations = json.loads(response.data)
        self.assertTrue(isinstance(invitations, list))

    def test_create_and_respond_to_invitation(self):
        response_add_user_to_event = self.client.post('/events/1/participants', json={'user_id': 1, })
        self.assertEqual(response_add_user_to_event.status_code, 200)
        response_add_user2_to_event = self.client.post('/events/1/participants', json={'user_id': 2, })
        self.assertEqual(response_add_user2_to_event.status_code, 200)

        response_create_meeting = self.client.post('events/1/meetings',
                                                   json={
                                                    'start_time': '2023-03-22T14:30:00',
                                                    'end_time': '2023-03-22T16:30:00',
                                                    'invitee_ids': [1, 2]
                                                   })
        
        self.assertEqual(response_create_meeting.status_code, 200)
        
        response_get_meeting = self.client.get('meetings/1')
        self.assertEqual(response_get_meeting.status_code, 200)
        meeting = json.loads(response_get_meeting.data)
        self.assertEqual(meeting['scheduled'], False)

        response_user1 = self.client.post('users/1/invitations', json={'invitation_id': 1, 'response': 'accept'})
        self.assertEqual(response_user1.status_code, 200)
        response_user2 = self.client.post('users/2/invitations', json={'invitation_id': 2, 'response': 'accept'})
        self.assertEqual(response_user2.status_code, 200)

        response_get_updated_meeting = self.client.get('meetings/1')
        self.assertEqual(response_get_updated_meeting.status_code, 200)
        updated_meeting = json.loads(response_get_updated_meeting.data)
        self.assertEqual(updated_meeting['scheduled'], True)




if __name__ == '__main__':
    unittest.main()
