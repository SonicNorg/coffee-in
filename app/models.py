from flask_user import UserMixin

from app import db


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120, collation='NOCASE'), index=True, unique=True)
    email = db.Column(db.String(120, collation='NOCASE'), index=True, unique=True)
    password = db.Column(db.String(128))
    active = db.Column(db.Boolean())
    email_confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary='user_roles')

    def __repr__(self):
        return '<User {} - {}>'.format(self.username, self.email)

    def set_password(self, password):
        self.password = password


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), unique=True)

    def __repr__(self):
        return '<Role {}>'.format(self.name)


# Связь юзеров с ролями
class UserRoles(db.Model):
    __tablename__ = 'user_roles'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'))
    role_id = db.Column(db.Integer(), db.ForeignKey('roles.id', ondelete='CASCADE'))

