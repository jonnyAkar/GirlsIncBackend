import json
import os
import collections
from flask import Flask, render_template, request, jsonify, g
from flask_cors import CORS
from flask_session import Session
from helpers.MySQLDatabaseHandler import MySQLDatabaseHandler
from sqlalchemy.sql import bindparam
from sqlalchemy import text
import re


# ROOT_PATH for linking with all your files.
# Feel free to use a config.py or settings.py with a global export variable
os.environ['ROOT_PATH'] = os.path.abspath(os.path.join("..", os.curdir))

# These are the DB credentials for your OWN MySQL
# Don't worry about the deployment credentials, those are fixed
# You can use a different DB name if you want to
MYSQL_USER = "root"
MYSQL_USER_PASSWORD = "Jonaccar96$"
MYSQL_PORT = 3306
MYSQL_DATABASE = "GirlsInc"

mysql_engine = MySQLDatabaseHandler(
    MYSQL_USER, MYSQL_USER_PASSWORD, MYSQL_PORT, MYSQL_DATABASE)

# Path to init.sql file. This file can be replaced with your own file for testing on localhost, but do NOT move the init.sql file
# mysql_engine.load_file_into_db()
db_path = os.path.join(os.environ['ROOT_PATH'],'init.sql')
mysql_engine.load_file_into_db(file_path = db_path)

app = Flask(__name__)

CORS(app)
#------------------------------ HELPERS ------------------------------

#helper to get schools
def get_schools():  
    # query
    query = "SELECT DISTINCT SchoolName FROM MonthlyResponses"  

    # Execute the query
    data = mysql_engine.query_selector(query)

    # Fetch 
    # Fetch school names and structure them as a list of dictionaries
    school_names = [{'label': row[0], 'value': row[0], 'disabled': False} for row in data.fetchall()]

    return school_names


#------------------------------ ROUTES ------------------------------
# Main endpoints
@app.route("/")
def home():
    return "home"

# Return the names of all the schools
@app.route('/schools')
def schools_route():  
    # query
    query = "SELECT DISTINCT SchoolName FROM MonthlyResponses"  

    # Execute the query
    data = mysql_engine.query_selector(query)

    # Fetch 
    # Fetch school names and structure them as a list of dictionaries
    school_names = [{'label': row[0], 'value': row[0], 'disabled': False} for row in data.fetchall()]

    return school_names

# Return the possible question
@app.route('/questions')
def get_questions():  
    data = ["YearsInGirlsInc", "SelfAwarenessRating", "RecommendToFriendRating", "EngagementRating"]

    # Fetch school names and structure them as a list of dictionaries
    questions = [{'label': row, 'value': row, 'disabled': False} for row in data]

    return questions

@app.route('/bar-data', methods=['GET','PUT'])
def handle_data():
    #Get method to retrieve data for the bar chart
    if request.method == 'GET':
        # Handle GET 
        arg = request.args.to_dict()

        #Get question HANDLE IF QUESTION IS EMPTY
        question = arg['question[label]']

        #Get selected schools
        query_schools = "SELECT school_name FROM SelectedSchools1 where is_selected = 1;"  
        selected_schools = mysql_engine.query_selector(query_schools).fetchall()
        selected_schools = [item[0] for item in selected_schools]
        selected_schools = " , ".join(f"'{s}'" for s in selected_schools)

        #HANDLE IF SELECTED SCHOOLS IS EMPTY
        query =' '.join((
            "SELECT Grade, AVG(" + question + ")",
            "FROM MonthlyResponses",
            "WHERE SchoolName IN (" + selected_schools + ")",
            "GROUP BY Grade",
            "ORDER BY Grade;"
        ))

        data = mysql_engine.query_selector(query).fetchall()        

        data = [{'label': key, 'value': float(score)} for key,score in data]
        
        return jsonify(data)

    #Update request to update the currently selected schools
    if request.method == 'PUT':
        selected_schools = []
        # Handle POST request logic
        data = request.get_json()
        json_schools = get_schools()
        schools = [item['value'] for item in json_schools]
        selected_schools = [item['value'] for item in data]

        for school in schools:
            is_selected = 0
            if school in selected_schools:
                is_selected = 1
            
            query = text(' '.join((
                "UPDATE SelectedSchools1",
                "SET is_selected = :var1",
                "WHERE school_name = :var2;"
            )))

            query = query.bindparams(var1=is_selected, var2=school)
            
            # Execute the query
            data = mysql_engine.query_selector(query)
        
        return jsonify({'message': 'This is a POST request', 'data': selected_schools})

    
if __name__ == '__main__':
    app.run()
