from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
app.app_context().push()


class Organization(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    organization = db.relationship('Organization', backref=db.backref('users'))

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    organization = db.relationship('Organization', backref=db.backref('events'))
    participants = db.relationship('User', secondary='event_participants', backref=db.backref('events'))

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Meeting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    event = db.relationship('Event', backref=db.backref('meetings'))
    participants = db.relationship('User', secondary='meeting_participants', backref=db.backref('meetings'))
    scheduled = db.Column(db.Boolean, default=False)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Invitation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('invitations'))
    meeting_id = db.Column(db.Integer, db.ForeignKey('meeting.id'), nullable=False)
    meeting = db.relationship('Meeting', backref=db.backref('invitations'))
    status = db.Column(db.Enum('pending', 'accepted', 'rejected'), default='pending')

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


event_participants = db.Table('event_participants',
    db.Column('event_id', db.Integer, db.ForeignKey('event.id')),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'))
)


meeting_participants = db.Table('meeting_participants',
    db.Column('meeting_id', db.Integer, db.ForeignKey('meeting.id')),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'))
)


@app.route('/users')
def get_users():
    users = User.query.all()
    return jsonify([user.as_dict() for user in users])


@app.route('/users/<int:user_id>/events')
def get_attended_events(user_id):
    user = User.query.get_or_404(user_id)
    events = user.events
    return jsonify([event.as_dict() for event in events])


@app.route('/users/<int:user_id>/meetings')
def get_user_meetings(user_id):
    user = User.query.get_or_404(user_id)
    meetings = user.meetings
    return jsonify([meeting.as_dict() for meeting in meetings])


@app.route('/users/<int:user_id>/invitations')
def get_user_invitations(user_id):
    user = User.query.get_or_404(user_id)
    invitations = user.invitations
    return jsonify([invitation.as_dict() for invitation in invitations])


@app.route('/users/<int:user_id>/invitations', methods=['POST'])
def respond_to_invitation(user_id):
    user = User.query.get_or_404(user_id)
    invitation_id = request.json['invitation_id']
    invitation = Invitation.query.get_or_404(invitation_id)

    response = request.json['response']
    if response == 'accept':
        invitation.status = 'accepted'
    elif response == 'reject':
        invitation.status = 'rejected'
    
    meeting = invitation.meeting
    all_accepted = True
    for invitation in meeting.invitations:
        if invitation.status != 'accepted':
            all_accepted = False
    
    if all_accepted:
        meeting.scheduled = True
    
    db.session.commit()

    return jsonify({'success': True})


@app.route('/organizations')
def get_organizations():
    organizations = Organization.query.all()
    return jsonify([organization.as_dict() for organization in organizations])


@app.route('/organizations/<int:org_id>/users')
def get_org_users(org_id):
    users = User.query.filter_by(organization_id=org_id).all()
    return jsonify([user.as_dict() for user in users])


@app.route('/organizations/<int:org_id>/events')
def get_events_by_organization(org_id):
    events = Event.query.filter_by(organization_id=org_id).all()
    return jsonify([event.as_dict() for event in events])


@app.route('/events')
def get_events():
    events = Event.query.all()
    return jsonify([event.as_dict() for event in events])


@app.route('/events/<int:event_id>/participants')
def get_event_participants(event_id):
    event = Event.query.get_or_404(event_id)
    participants = event.participants
    return jsonify([user.as_dict() for user in participants])


@app.route('/events/<int:event_id>/participants', methods=['POST'])
def add_participant(event_id):
    event = Event.query.get_or_404(event_id)
    user_id = request.json['user_id']
    user = User.query.get_or_404(user_id)
    event.participants.append(user)
    db.session.commit()
    return jsonify({'success': True})


@app.route('/events/<int:event_id>/meetings')
def get_meetings(event_id):
    event = Event.query.get_or_404(event_id)
    meetings = event.meetings
    return jsonify([meeting.as_dict() for meeting in meetings])


@app.route('/events/<int:event_id>/meetings', methods=['POST'])
def create_meeting(event_id):
    event = Event.query.get_or_404(event_id)
    timetable_clashing = False

    start_time = datetime.strptime(request.json['start_time'], '%Y-%m-%dT%H:%M:%S')
    end_time = datetime.strptime(request.json['end_time'], '%Y-%m-%dT%H:%M:%S')
    invitee_ids = request.json['invitee_ids']

    invitees = [User.query.get_or_404(invitee_id) for invitee_id in invitee_ids]
    new_meeting = Meeting(start_time=start_time, end_time=end_time, event=event, participants=invitees)
    
    for invitee in invitees:
        for meeting in invitee.meetings:
            if meeting.scheduled:
                if new_meeting.start_time <= meeting.start_time and new_meeting.end_time >= meeting.start_time \
                   or new_meeting.start_time >= meeting.start_time and new_meeting.end_time <= meeting.end_time \
                   or new_meeting.start_time <= meeting.end_time and new_meeting.end_time >= meeting.end_time:
                    timetable_clashing = True

    if timetable_clashing:
        return jsonify({'error': 'Meeting time clashes with an existing meeting'}), 400
    
    db.session.add(new_meeting)

    for invitee in invitees:
        new_invitation = Invitation(user=invitee, meeting=new_meeting)
        db.session.add(new_invitation)
    
    db.session.commit()

    return jsonify({'success': True})


@app.route('/meetings')
def get_all_meetings():
    meetings = Meeting.query.all()
    return jsonify([meeting.as_dict() for meeting in meetings])


@app.route('/meetings/<int:meeting_id>')
def get_meeting_status(meeting_id):
    meeting = Meeting.query.get_or_404(meeting_id)
    return jsonify(meeting.as_dict())


@app.route('/meetings/<int:meeting_id>/invitations')
def get_meeting_invites(meeting_id):
    meeting = Meeting.query.get_or_404(meeting_id)
    invitations = meeting.invitations
    return jsonify([invitation.as_dict() for invitation in invitations])


def main():
    db.drop_all()
    db.create_all()

    organization1 = Organization(name='Organization 1')
    db.session.add(organization1)

    user1 = User(name='User 1', organization=organization1)
    user2 = User(name='User 2', organization=organization1)
    db.session.add(user1)
    db.session.add(user2)

    event1 = Event(name='Event 1', organization=organization1)
    event2 = Event(name='Event 2', organization=organization1)
    db.session.add(event1)
    db.session.add(event2)

    organization2 = Organization(name='Organization 2')
    db.session.add(organization2)

    user3 = User(name='User 3', organization=organization2)
    user4 = User(name='User 4', organization=organization2)
    db.session.add(user3)
    db.session.add(user4)

    event3 = Event(name='Event 3', organization=organization2)
    event4 = Event(name='Event 4', organization=organization2)
    db.session.add(event3)
    db.session.add(event4)

    db.session.commit()
    
    app.run(debug=True)

if __name__ == '__main__':
    main()
