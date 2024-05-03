from flask import Flask, request, jsonify, render_template, url_for, redirect, flash
import pymongo
from pymongo import MongoClient
from bson import ObjectId, json_util
import hashlib
from datetime import datetime
import logging

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
import requests 
import re
from urllib.parse import unquote
import folium
import math


# Setup basic configuration for logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')



backEndMG = Flask(__name__)



#login-mySQL(user info)
backEndMG.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////home/ubuntu/final_project_551/apartment_data/query/database.db'
backEndMG.config['SECRET_KEY'] = 'thisisasecretkey'

sql_db = SQLAlchemy(backEndMG)
bcrypt = Bcrypt(backEndMG)
backEndMG.app_context().push()


login_manager = LoginManager()
login_manager.init_app(backEndMG)
login_manager.login_view = 'login'



# MongoDB connection setup (apartment + activity info)
client = MongoClient(host="localhost", port=27017)
db = client['finalProject_db']  


#user-login
@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))


class Users(sql_db.Model, UserMixin):
    id = sql_db.Column(sql_db.Integer, primary_key=True)
    username = sql_db.Column(sql_db.String(20), nullable=False, unique=True)
    password = sql_db.Column(sql_db.String(30), nullable=False)


class RegisterForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField('Register')

    def validate_username(self, username):
        existing_user_username = Users.query.filter_by(username=username.data).first()
        if existing_user_username:
            raise ValidationError('That username already exists. Please choose a different one.')


class LoginForm(FlaskForm):
    username = StringField(validators=[
                           InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})

    password = PasswordField(validators=[
                             InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})

    submit = SubmitField('Login')

@backEndMG.route('/')
def home():
    return render_template('home.html')


#login
@backEndMG.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(username=form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('dashboard'))
    return render_template('login.html', form=form)

@backEndMG.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    #response = requests.get('http://localhost:5000/apartments')
    #return redirect('http://13.57.199.139:5000/')
    apartments_list = list(db['partments'].find().sort([('Rating', pymongo.DESCENDING)]))
    return render_template('webpage.html', user=current_user)

#logout
@backEndMG.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

#register
@backEndMG.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = Users(username=form.username.data, password=hashed_password)
        sql_db.session.add(new_user)
        sql_db.session.commit()
        flash('Account created successfully!', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)




#initialize

def get_apartment_collection(name):
    """Get the MongoDB collection based on the normalized first letter of the apartment name."""
    normalized_name = name.strip().lower()
    if not normalized_name:  # Check if the name is empty or became empty after normalization
        raise ValueError("The provided name is invalid or unsupported for collection determination.")
    
    if normalized_name[0] in 'abcd':
        return db['apartments_even_1']
    elif normalized_name[0] in 'efgh':
        return db['apartments_odd_1']
    elif normalized_name[0] in 'ijkl':
        return db['apartments_even_2']
    else:
        return db['apartments_odd_2']


def get_collection_by_type(collection_type):
    if collection_type in ['user', 'Apt_comment', 'comment', 'rating']:
        return db[collection_type]
    raise ValueError("Invalid collection type")

def update_user_activity(user_id, activity_type, activity_object, activity_id=None):
    user_collection = get_collection_by_type('user')

    # Check if the activity already exists to avoid duplicating it
    existing_activity = user_collection.find_one({
        'user_id': user_id,
        f'{activity_type}_ids': {'$elemMatch': {'activity_object': activity_object}}
    })

    if existing_activity:
        activity_id = existing_activity['_id']
    else:
        # Only generate a new ObjectId if we need to add a new activity
        activity_id = activity_id or str(ObjectId())

    activity_field = f'{activity_type}_ids'

    # Upsert the activity_id into the user's document
    update_result = user_collection.update_one(
        {'user_id': user_id},
        {'$addToSet': {activity_field: {'id': activity_id, 'activity_object': activity_object}}},
        upsert=True
    )

    # Log activity update
    if update_result.modified_count > 0 or update_result.upserted_id:
        logging.info(f"Activity {activity_id} recorded for user: {user_id}, type: {activity_type}, object: {activity_object}")
    else:
        logging.warning(f"No document was updated or inserted for user_id: {user_id}")

    return activity_id

def calculate_distance(geocode1, geocode2):
    # Calculate Euclidean distance
    return math.sqrt((geocode1[0] - geocode2[0]) ** 2 + (geocode1[1] - geocode2[1]) ** 2)

center_location = [34.0211385, -118.2893204]  # location of USC

def safe_cast(val, to_type, default=None):
    try:
        return to_type(val)
    except (ValueError, TypeError):
        return default


@backEndMG.route('/apartments', methods=['GET'])
def list_apartments():
    apartments_list = []

    # Create a map centered around an example location
    m = folium.Map(location=[34.0211385,-118.2893204], tiles='https://mt.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',attr='default', zoom_start=12)

    # get frontend_para
    search_query = request.args.get('search', '').strip().lower()

    query = {}
    if search_query:
        regex_search = {'$regex': f'^.*{search_query}.*$', '$options': 'i'}
        query = {'$or': [{'Name': regex_search}, {'Address': regex_search}]}

    # Query all possible sets based on hash logic
    collection_names = ['apartments_even_1', 'apartments_even_2', 'apartments_odd_1', 'apartments_odd_2']

    for collection_name in collection_names:
        apartments = db[collection_name].find(query)
        for apartment in apartments:
            apartment_name = apartment['_id']
            top_comment = db['comment'].find_one({'apartment_name': apartment_name}, sort=[('likes', -1)])
            top_comment_text = top_comment['text'] if top_comment else "No comments yet"

            tags = apartment.get('Tags', [])
            if not isinstance(tags, list):
                tags = ['No tags']

            rating_avg = apartment.get('Rating', {}).get('avg', 'No ratings yet')
            rating_num = apartment.get('Rating', {}).get('num', 0)
            if isinstance(rating_avg, (int, float)):
                rating_avg_formatted = f"{rating_avg:.1f}"
            else:
                rating_avg_formatted = "No ratings yet"

            apartment.update({
                'top_comment': top_comment_text,
                'Rating': f"Average Rating: {rating_avg_formatted}, Number of Ratings: {rating_num}",
                'rating_value': float(rating_avg) if isinstance(rating_avg, (int, float)) else 0,
                'Price': apartment.get('Price', 'Not available'),
                'Tags': tags,
                'Address': apartment.get('Address', 'Address not available')
            })

           # Ensure geocode is a flat list with latitude and longitude
            geo_code = apartment['geocode'] if isinstance(apartment['geocode'], list) and len(apartment['geocode']) == 2 else [34.0211385, -118.2893204]

            # Add markers to the map
            folium.Marker(
                location=geo_code,
                popup=f"{apartment['Name']} - {apartment['Address']}",
                tooltip=f"Click for more info"
            ).add_to(m)

            # Calculate distance from the center and add it to the apartment info
            geocode = apartment.get('geocode', center_location)
            apartment['distance'] = calculate_distance(geocode, center_location)

            apartments_list.append(apartment)

    # Sort apartments by descending average rating
    sort_by = request.args.get('sort_by', 'rating')  # 'rating', 'price' or 'distance'
    order = request.args.get('order', 'desc')  # 'asc' 或 'desc'
    
    # ranking
    if sort_by == 'price':
        apartments_list.sort(key=lambda x: safe_cast(x.get('Price', '').replace(',', '').strip('$'), float, default=0), reverse=(order == 'desc'))

    elif sort_by == 'distance':
        apartments_list.sort(key=lambda x: safe_cast(x.get('distance', float('inf')), float, default=float('inf')), reverse=(order == 'desc'))

    else:  # rating by default
        apartments_list.sort(key=lambda x: safe_cast(x.get('rating_value', 0), float, default=0), reverse=(order == 'desc'))

    # Convert map to HTML string
    map_html = m._repr_html_()  # or use m.save('path_to_save.html') if you want to save the map

    return jsonify({
        'apartments': apartments_list,
        'map_html': map_html
    }), 200


@backEndMG.route('/apartment/<path:apartment_name>')
def apartment_detail(apartment_name):
    # URL decoding apartment name
    decoded_name = unquote(apartment_name)
    #get collection
    collection = get_apartment_collection(decoded_name)
    
    # search apartment name
    apartment = collection.find_one({'Name': decoded_name})
    if apartment:
        # get info
        comments = list(db['comment'].find({'apartment_name': decoded_name}).sort([('likes', -1), ('dislikes', 1)]))
        
        tags = apartment.get('Tags', [])
        rating_avg = apartment.get('Rating', {}).get('avg', 'No ratings yet')
        rating_num = apartment.get('Rating', {}).get('num', 0)
        if isinstance(rating_avg, (int, float)):
            rating_avg = f"{rating_avg:.1f}"

        # updating & listing info
        apartment.update({
            'comments': comments,  # 添加所有按喜欢数排序的评论
            'Rating': f"Average Rating: {rating_avg}, Number of Ratings: {rating_num}",
            'Price': apartment.get('Price', 'Not available'),
            'Tags': tags,
            'Address': apartment.get('Address', 'Address not available')
        })

        # apartment_detail.html
        return render_template('apartment_detail.html', apartment=apartment)
    else:
        return "Apartment not found", 404

######user's behaviour######

@backEndMG.route('/rating', methods=['POST'])
def add_rating():
    try:
        rating = request.json
        apartment_name = rating['apartment_name']
        score = int(rating['score'])

        # Get collections
        rating_collection = get_collection_by_type('rating')
        apartment_collection = get_apartment_collection(apartment_name)
        apartment_data = apartment_collection.find_one({'_id': apartment_name})

        # Check if the user has already rated the apartment
        existing_rating = rating_collection.find_one({'apartment_name': apartment_name, 'user_id': current_user.id})
        
        if existing_rating:
            old_score = existing_rating['score']
            activity_id = existing_rating['_id']  # Use existing rating ID
            rating_collection.update_one(
                {'apartment_name': apartment_name, 'user_id': current_user.id},
                {'$set': {'score': score}}
            )
        else:
            # If it's a new rating, create a new activity_id for this rating
            activity_id = str(ObjectId())
            rating_collection.update_one(
                {'apartment_name': apartment_name, 'user_id': current_user.id},
                {'$set': {'score': score, '_id': activity_id}},
                upsert=True
            )
            old_score = 0

        existing_avg = apartment_data.get('Rating', {}).get('avg', 0)
        existing_num = apartment_data.get('Rating', {}).get('num', 0)
        
        # Calculate total score considering the old score
        total_score = (existing_avg*existing_num) - old_score + score
        num_ratings = existing_num if old_score != 0 else existing_num + 1

        # Calculate new average
        avg_rating = total_score / num_ratings if num_ratings > 0 else 0

        # Update apartment rating info
        apartment_collection.update_one(
            {'_id': apartment_name},
            {'$set': {'Rating': {'avg': avg_rating, 'num': num_ratings}}},
            upsert=True
        )

        # Update user activity with a specific activity ID
        update_user_activity(current_user.id, 'rating', apartment_name, activity_id)
        
        logging.info(f"Rating updated successfully for apartment: {apartment_name} by user: {current_user.id}")
        return jsonify({'message': 'Rating updated successfully'}), 201

    except Exception as e:
        logging.exception("Exception occurred while updating rating")
        return jsonify({'error': str(e)}), 500




@backEndMG.route('/comment', methods=['POST'])
@login_required
def add_comment():
    comment = request.json
    comment_id = str(ObjectId())
    # Add the current user's ID to the comment data
    comment['comment_id'] = comment_id
    comment['user_id'] = current_user.id  # Ensure current_user is loaded with Flask-Login

    comment_collection = get_collection_by_type('comment')
    comment_collection.insert_one(comment)

    # Update user activity, assuming function handles this appropriately
    update_user_activity(current_user.id, 'comment', comment_id)

    return jsonify({'message': 'Comment added successfully', 'comment_id': comment_id}), 201



@backEndMG.route('/comment/delete/<comment_id>', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment_collection = get_collection_by_type('comment')
    user_collection = get_collection_by_type('user')

    # get comment data
    comment = comment_collection.find_one({'comment_id': comment_id})
    if not comment:
        return jsonify({'error': 'Comment not found'}), 404

    # delete confirmation
    if str(comment['user_id']) != str(current_user.id):
        return jsonify({'error': 'You are not authorized to delete this comment'}), 403

    result = comment_collection.delete_one({'comment_id': comment_id})

    # delete relavent like & dislike records
    update_result = user_collection.update_many(
        {},
        {
            '$pull': {
                'comment_ids':{'activity_object': comment_id},
                'like_ids': {'activity_object': comment_id},
                'dislike_ids': {'activity_object': comment_id}
            }
        }
    )

    if result.deleted_count == 0:
        return jsonify({'error': 'Failed to delete comment'}), 500

    return jsonify({'message': 'Comment deleted successfully'}), 200




@backEndMG.route('/comment/like', methods=['POST'])
def like_comment():
    data = request.json
    comment_id = data['comment_id']
    user_id = current_user.id  # Assume current_user is already available

    comment_collection = get_collection_by_type('comment')
    comment = comment_collection.find_one({'comment_id': comment_id})

    # Check if user has already liked or disliked this comment
    if user_id in comment.get('like_ids', []):
        return jsonify({'message': 'You have already liked this comment'}), 200
    if user_id in comment.get('dislike_ids', []):
        # Remove dislike if present
        comment_collection.update_one({'comment_id': comment_id}, {
            '$pull': {'dislike_ids': user_id},
            '$inc': {'dislikes': -1}
        })

    # Add like
    result = comment_collection.update_one({'comment_id': comment_id}, {
        '$addToSet': {'like_ids': user_id},
        '$inc': {'likes': 1}
    })

    if result.modified_count == 0:
        return jsonify({'message': 'Failed to like the comment'}), 400

    update_user_activity(user_id, 'like', comment_id)
    return jsonify({'message': 'Comment liked successfully'}), 200

@backEndMG.route('/comment/dislike', methods=['POST'])
def dislike_comment():
    data = request.json
    comment_id = data['comment_id']
    user_id = current_user.id  # Assume current_user is already available

    comment_collection = get_collection_by_type('comment')
    comment = comment_collection.find_one({'comment_id': comment_id})

    # Check if user has already disliked or liked this comment
    if user_id in comment.get('dislike_ids', []):
        return jsonify({'message': 'You have already disliked this comment'}), 200
    if user_id in comment.get('like_ids', []):
        # Remove like if present
        comment_collection.update_one({'comment_id': comment_id}, {
            '$pull': {'like_ids': user_id},
            '$inc': {'likes': -1}
        })

    # Add dislike
    result = comment_collection.update_one({'comment_id': comment_id}, {
        '$addToSet': {'dislike_ids': user_id},
        '$inc': {'dislikes': 1}
    })

    if result.modified_count == 0:
        return jsonify({'message': 'Failed to dislike the comment'}), 400

    update_user_activity(user_id, 'dislike', comment_id)
    return jsonify({'message': 'Comment disliked successfully'}), 200


if __name__ == '__main__':
    backEndMG.run(debug=True, host='0.0.0.0')
