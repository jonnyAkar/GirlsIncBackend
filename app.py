import json
import os
import collections
from flask import Flask, render_template, request, jsonify, g
from flask_cors import CORS
import sqlite3
import pandas as pd
import nbformat
import csv
from nbconvert.preprocessors import ExecutePreprocessor


"""
#Run jupyter notebook
current_directory = os.getcwd()

os.chdir(os.path.dirname('./Notebook Work/Attendance.ipynb'))

with open('Attendance.ipynb') as ff:
    nb_in = nbformat.read(ff, nbformat.NO_CONVERT)
    
ep = ExecutePreprocessor(timeout=600, kernel_name='python3')
nb_out = ep.preprocess(nb_in)

os.chdir(current_directory)
"""

conn = sqlite3.connect('GirlsInc.db')

cursor = conn.cursor()

#create monthly responses table
data_file_path = './Notebook Work/May-Oct_cleaned_data.csv' 
df = pd.read_csv(data_file_path)
df.to_sql('MonthlyResponses', conn, if_exists='replace', index=False)

#create selected schools table
data_file_path = './Notebook Work/SelectedSchools.csv' 
df = pd.read_csv(data_file_path)
df.to_sql('SelectedSchools', conn, if_exists='replace', index=False)

#create attendance table
data_file_path = './Notebook Work/attendance_cleaned.csv' 
df = pd.read_csv(data_file_path)
df.to_sql('Attendance', conn, if_exists='replace', index=False)

conn.commit()
cursor.close()
conn.close()

app = Flask(__name__)

#------------------------------ HELPERS ------------------------------

#helper to get schools
def get_schools():  
    conn = sqlite3.connect('GirlsInc.db')  # Replace with your database file path

    # Create a cursor object to execute SQL queries
    cursor = conn.cursor()

    # query
    query = 'SELECT DISTINCT "School Name" FROM MonthlyResponses'

    # Execute the query
    cursor.execute(query)

    # Fetch all rows from the result set
    result = cursor.fetchall()
    result = [item[0] for item in result]
    # Close the cursor and the database connection
    cursor.close()
    conn.close()

    return result

#helper to get dates until today
def get_dates():  
    conn = sqlite3.connect('GirlsInc.db')  # Replace with your database file path

    # Create a cursor object to execute SQL queries
    cursor = conn.cursor()

    # query
    query = 'SELECT DISTINCT "School Name" FROM MonthlyResponses'

    # Execute the query
    cursor.execute(query)

    # Fetch all rows from the result set
    result = cursor.fetchall()
    result = [item[0] for item in result]
    # Close the cursor and the database connection
    cursor.close()
    conn.close()

    return result

#Load dates till today
def load_dates_from_csv():
    dates = []
    filepath = './Notebook Work/daysTillToday.csv' 
    try:
        # Open the CSV file
        with open(filepath, newline='') as csvfile:
            reader = csv.reader(csvfile)
            
            # Iterate over each row in the csv
            for row in reader:
                # Assuming dates are in the first column of the CSV
                if row:  # check if the row is not empty
                    date = row[0]
                    dates.append(date)  # Add the date to our list
    except FileNotFoundError:
        print(f"File not found: {filepath}")

    return dates

def load_json(filepath):
    """Load a JSON file and return a dictionary."""
    try:
        with open(filepath, 'r') as file:
            data = json.load(file)
            return data
    except FileNotFoundError as e:
        print(f"Error: {filepath} not found")
        return {}  # Return empty dictionary or handle it accordingly
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return {}




#------------------------------ ROUTES ------------------------------


# Main endpoints
@app.route("/")
def home():
    return "Home"

#------------------------------ GETTERS ------------------------------

# Return the names of all the schools
@app.route('/schools')
def schools_route(): 
    conn = sqlite3.connect('GirlsInc.db') 

    # Create a cursor object to execute SQL queries
    cursor = conn.cursor()
     
    # query
    query = 'SELECT DISTINCT "School Name" FROM MonthlyResponses'  

    #Execute 
    cursor.execute(query)

    # Fetch all rows from the result set
    result = cursor.fetchall()

    # Close the cursor and the database connection
    cursor.close()
    conn.close()
    
    # Fetch school names and structure them as a list of dictionaries
    school_names = [{'label': row[0], 'value': row[0], 'disabled': False} for row in result]

    return school_names


# Return the possible question
@app.route('/questions')
def get_questions():  
    data = ["YearsInGirlsInc", 
            "SelfAwarenessRating",
            "RecommendToFriendRating", 
            "EngagementRating"]

    # Fetch school names and structure them as a list of dictionaries
    questions = [{'label': row, 'value': row, 'disabled': False} for row in data]

    return questions

#return all the girls in a school
@app.route('/girls', methods=['GET'])
def get_girls():
    result = []
    arg = request.args.to_dict()
    if (arg != {}):
        school = arg['value']

        conn = sqlite3.connect('GirlsInc.db') 
        
        # Create a cursor object to execute SQL queries
        cursor = conn.cursor()
        
        # query
        query = ' '.join((
            'SELECT "First Name", "Last Name"',
            "FROM 'MonthlyResponses'",
            'WHERE "School Name" =' + "'" + school + "'"
        ))

        #Execute 
        cursor.execute(query)

        # Fetch all rows from the result set
        data = cursor.fetchall()    
        # Close the cursor and the database connection
        cursor.close()
        conn.close()

        result = [{'label': first + " " + last, 'value': first + " " + last, 'disabled': False} 
                  for first,last in data]

    return result

#------------------------------ GRAPH1 ------------------------------

@app.route('/graph1', methods=['GET','PUT'])
def handle_data():
    #Get method to retrieve data for the bar chart
    if request.method == 'GET':
        # Handle GET 
        arg = request.args.to_dict()

        #Get question HANDLE IF QUESTION IS EMPTY
        question = arg['question[label]']

        conn = sqlite3.connect('GirlsInc.db') 

        # Create a cursor object to execute SQL queries
        cursor = conn.cursor()
        query = "SELECT * FROM SelectedSchools"

        #Get selected schools
        query_schools = 'SELECT "school_name" FROM SelectedSchools where is_selected = 1;'  
        selected_schools = cursor.execute(query_schools).fetchall()
        selected_schools = [item[0] for item in selected_schools]
        selected_schools = " , ".join(f"'{s}'" for s in selected_schools)

        #HANDLE IF SELECTED SCHOOLS IS EMPTY
        query =' '.join((
            "SELECT Grade, AVG(" + question + "), COUNT(*)",
            "FROM MonthlyResponses",
            'WHERE "School Name" IN (' + selected_schools + ")",
            "GROUP BY Grade",
            "ORDER BY Grade;"
        ))

        data = cursor.execute(query).fetchall()

        # Close the cursor and the database connection
        cursor.close()
        conn.close()

        data = [{'label': key, 'value': float(score), 'num':count} for key,score,count in data]
                
        return jsonify(data)

    #Update request to update the currently selected schools
    if request.method == 'PUT':
        selected_schools = []
        # Handle POST request logic
        data = request.get_json()
        schools = get_schools()
        selected_schools = [item['value'] for item in data]

        conn = sqlite3.connect('GirlsInc.db') 
        cursor = conn.cursor()
        for school in schools:
            is_selected = 0
            if school in selected_schools:
                is_selected = 1

            query = ' '.join((
                "UPDATE SelectedSchools",
                "SET is_selected = " + str(is_selected),
                "WHERE school_name = '" + school + "';"
            ))
            
            # Execute the query
            data = cursor.execute(query)

        cursor.close()
        conn.commit()
        conn.close()

        return jsonify({'message': 'This is a POST request', 'data': selected_schools})
    

#------------------------------ GRAPH3 ------------------------------
#Get data for school attendance
@app.route('/graph3', methods=['GET'])
def get_data():

    days = load_dates_from_csv()  

    school_dict = load_json('./Notebook Work/school_daily_attendance.json')

    data = {
        'days': days,
        'datasets': [
            {
            'school': 'Kipp',
            'data': school_dict['Kipp'],
            },
            {
            'school': 'Beacon',
            'data': school_dict['Beacon'],
            },
            {
            'school': 'Santa Clara',
            'data': school_dict['Santa Clara'],
            },{
            'school': 'Hive',
            'data': school_dict['Hive'],
            },{
            'school': 'Pine Lake',
            'data': school_dict['Pine Lake'],
            }
        ]
    }
    return data

