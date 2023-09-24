from flask import Flask, request, jsonify, session
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask_restful import Api, Resource
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from sqlalchemy import MetaData
from models import User



app = Flask(__name__)
app.secret_key = b'Y\xf1Xz\x00\xad|eQ\x80t \xca\x1a\x10K'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json.compact = False

metadata = MetaData(naming_convention={
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
})
db = SQLAlchemy(metadata=metadata)

migrate = Migrate(app, db)
db.init_app(app)

bcrypt = Bcrypt(app)

api = Api(app)



class Signup(Resource):
    def post(self):
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        bio = data.get('bio')
        image_url = data.get('image_url')

        try:
            user = User(username=username, password=password, bio=bio, image_url=image_url)
            db.session.add(user)
            db.session.commit()
            session['user_id'] = user.id
            return jsonify(
                user_id=user.id,
                username=user.username,
                image_url=user.image_url,
                bio=user.bio
            ), 201
        except IntegrityError:
            db.session.rollback()
            return jsonify(message='Username already exists'), 422


class CheckSession(Resource):
    def get(self):
        user_id = session.get('user_id')
        if user_id:
            user = User.query.get(user_id)
            if user:
                return jsonify(
                    user_id=user.id,
                    username=user.username,
                    image_url=user.image_url,
                    bio=user.bio
                ), 200
        return jsonify(error='Unauthorized'), 401


class Login(Resource):
    def post(self):
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            return jsonify(
                user_id=user.id,
                username=user.username,
                image_url=user.image_url,
                bio=user.bio
            ), 200
        return jsonify(error='Unauthorized'), 401


class Logout(Resource):
    def delete(self):
        if 'user_id' in session:
            session.pop('user_id', None)
            return '', 204
        return jsonify(error='Unauthorized'), 401


class RecipeIndex(Resource):
    def get(self):
        user_id = session.get('user_id')
        if user_id:
            recipes = Recipe.query.filter_by(user_id=user_id).all()
            recipe_list = []
            for recipe in recipes:
                recipe_list.append({
                    'title': recipe.title,
                    'instructions': recipe.instructions,
                    'minutes_to_complete': recipe.minutes_to_complete,
                    'user': {
                        'user_id': user_id,
                        'username': User.query.get(user_id).username,
                        'image_url': User.query.get(user_id).image_url,
                        'bio': User.query.get(user_id).bio
                    }
                })
            return jsonify(recipes=recipe_list), 200
        return jsonify(error='Unauthorized'), 401

    def post(self):
        user_id = session.get('user_id')
        if user_id:
            data = request.get_json()
            title = data.get('title')
            instructions = data.get('instructions')
            minutes_to_complete = data.get('minutes_to_complete')
            try:
                recipe = Recipe(
                    user_id=user_id,
                    title=title,
                    instructions=instructions,
                    minutes_to_complete=minutes_to_complete
                )
                db.session.add(recipe)
                db.session.commit()
                return jsonify(
                    title=recipe.title,
                    instructions=recipe.instructions,
                    minutes_to_complete=recipe.minutes_to_complete,
                    user={
                        'user_id': user_id,
                        'username': User.query.get(user_id).username,
                        'image_url': User.query.get(user_id).image_url,
                        'bio': User.query.get(user_id).bio
                    }
                ), 201
            except IntegrityError:
                db.session.rollback()
                return jsonify(error='Recipe data is not valid'), 422
        return jsonify(error='Unauthorized'), 401



api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')

if __name__ == '__main__':
    app.run(port=5555, debug=True)

