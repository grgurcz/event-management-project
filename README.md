# event-management-project

Project created using python and flask.


Installing requirements:
`pip install -r requirements.txt`

Running the application:
`python main.py`

Running tests:
`python test.py`

Notes:
- the application must be run at least once before testing, otherwise database tables won't exist
- database is cleared every time the application starts, to stop this just comment out line 233 of main.py: `db.drop_all()`
- there are no endpoints for managing users, events and organizations, some sample entries are created in the main function for showcase purposes


Examples of requests:

`curl localhost:5000/users`

`curl localhost:5000/users/1/events`

`curl localhost:5000/users/1/meetings`

`curl localhost:5000/users/1/invitations`

`curl -X POST   localhost:5000/users/2/invitations -H 'Content-Type: application/json' -d '{"invitation_id": 2, "response": "accept"}'`

`curl localhost:5000/organizations`

`curl localhost:5000/organizations/1/users`

`curl localhost:5000/organizations/1/events`

`curl localhost:5000/events`

`curl localhost:5000/events/1/participants`

`curl -X POST   http://localhost:5000/events/1/participants -H 'Content-Type: application/json' -d '{"user_id": 1}'`

`curl localhost:5000/events/1/meetings`

`curl -X POST   http://localhost:5000/events/1/meetings -H 'Content-Type: application/json' -d '{"start_time": "2023-03-22T15:30:00", "end_time": "2023-03-22T16:30:00", "invitee_ids": [1, 2]}'`

`curl localhost:5000/meetings`

`curl localhost:5000/meetings/1`

`curl localhost:500/meetings/1/invitations`
