import cs50
import csv

from enum import IntEnum
from dataclasses import dataclass
import json

from jinja2.ext import Extension
from flask import Flask, jsonify, redirect, render_template, request

# Configure application
app = Flask(__name__)

# Reload templates when they are changed
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.jinja_env.add_extension('jinja2.ext.loopcontrols')

class Person(object):
    def __init__(self, fname=None, lname=None, age=None, country=None, place=None):
        self.fname = fname;
        self.lname = lname;
        self.age = age;
        self.country = country;
        self.place = place;
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__,
            sort_keys=True, indent=4)
    def createTable(self):
        return """teste"""

class Enum(IntEnum):
    FIRST_NAME = 0;
    LAST_NAME = 1;
    AGE = 2;
    COUNTRY = 3;

@app.after_request
def after_request(response):
    """Disable caching"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/", methods=["GET"])
def get_index():
    return redirect("/form")

@app.route("/form", methods=["GET"])
def get_form():
    return render_template("form.html")

@app.route("/form", methods=["POST"])
def post_form():
    errorExist = False
    errorMessage=""

    userNames = [  request.form['fname'],   #0 - FIRST NAME
                   request.form['lname']  ] #1 - LAST NAME

    userAge = request.form.get('agecheck')

    for names in userNames:
        if names == "":
            errorExist = True;
            errorMessage="Please provide your name.\n"
        if any(char.isdigit() for char in names):
            errorExist = True;
            errorMessage+="Do not input digits on your name."
            break

    if userAge != "under18" and userAge != "18over":
        errorExist = True;
        errorMessage+="Please provide your age."

    if errorExist:
        return render_error(errorMessage)
    else:
        return store(userNames, userAge, request.form['country'])

def store(userNames, userAge, userCountry):
    with open("survey.csv", "r+") as surveyFile:
        surveyReader = csv.reader(surveyFile, delimiter=",")

        # checks if it is the same person
        for row in surveyReader:
            if row is not None:
                if row[Enum.FIRST_NAME] == userNames[Enum.FIRST_NAME]:
                    if row[Enum.LAST_NAME] == userNames[Enum.LAST_NAME]:
                        if row[Enum.AGE] == userAge:
                            if row[Enum.COUNTRY] == userCountry:
                                return render_error("User already submitted form.")

        # if not, stores the user's data in the CVS file
        surveyWriter = csv.writer(surveyFile)
        surveyWriter.writerow([userNames[Enum.FIRST_NAME], userNames[Enum.LAST_NAME], userAge, userCountry])

    return redirect("/sheet")

@app.route("/sheet", methods=["GET"])
def get_sheet():
    place = 0
    persons = []
    with open("survey.csv", "r") as surveyFile:
        surveyReader = csv.reader(surveyFile, delimiter=",")

        for rows in surveyReader:
            persons.append(Person(rows[Enum.FIRST_NAME], rows[Enum.LAST_NAME],
                                     rows[Enum.AGE], rows[Enum.COUNTRY], place))
            place += 1

    return render_template("sheet.html", persons=persons, place=place)

def render_error(errorMessage):
    return render_template("error.html", message=errorMessage)