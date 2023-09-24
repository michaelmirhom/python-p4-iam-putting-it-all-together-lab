from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy_serializer import SerializerMixin
from sqlalchemy.orm import validates
from config import db, bcrypt

class User(db.Model, SerializerMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    _password_hash = db.Column(db.String(128), nullable=False)
    image_url = db.Column(db.String(255))
    bio = db.Column(db.String(255))

    recipes = db.relationship('Recipe', backref='user', lazy=True)

    def __init__(self, username, password, image_url=None, bio=None):
        self.username = username
        self.set_password(password)
        self.image_url = image_url
        self.bio = bio

    @hybrid_property
    def password_hash(self):
        raise AttributeError("Password hash is not readable")

    def set_password(self, password):
        self._password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self._password_hash, password)

    @validates('username')
    def validate_username(self, key, value):
        if User.query.filter(User.username == value).first() is not None:
            raise ValueError("Username already exists.")
        return value

class Recipe(db.Model, SerializerMixin):
    __tablename__ = 'recipes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    instructions = db.Column(db.String(1000), nullable=False)
    minutes_to_complete = db.Column(db.Integer, nullable=False)

    @validates('title')
    def validate_title(self, key, value):
        if not value:
            raise ValueError("Title must be present.")
        return value

    @validates('instructions')
    def validate_instructions(self, key, value):
        if not value or len(value) < 50:
            raise ValueError("Instructions must be present and at least 50 characters long.")
        return value
