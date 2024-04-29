# Cameron Ela, ceela@usc.edu
# DSCI 551, Spring 2024
# Viterbi Web Registration Application
# This file uses flask API to display the application's web interface.

import os
from flask import Flask, redirect, render_template, request, session, url_for
from create_db import hash_student
import db_actions as dba
import sqlite3 as sl

app = Flask(__name__)
dbs = ["INFORMATION.db", "STUDENTS1", "STUDENTS2", "STUDENTS3", "STUDENTS4"]


# home page
@app.route("/")
def home():
    if "student" not in session and "admin" not in session:
        return render_template("login.html")

    if "student" in session:
        student = session["student"]
        fname = session["fname"] = student[1]
        option_text = ["You can add or remove a course", "from your course bin."]
        options = {
            "Adding": "Add to Course Bin",
            "Removing": "Remove from Course Bin",
        }
        return render_template("home.html", option_text=option_text, options=options, fname=fname)

    admin = session["admin"]
    fname = session["fname"] = admin[1]
    options = {
        "catalog": "Add to Course Catalog",
        "move_courses": "Move Courses",
        "add_student": "Add New Student",
        "remove_student": "Remove Student"
    }
    return render_template("home.html", options=options, option_text="", fname=fname)


# login
@app.route('/login', methods=["POST"])
def login():
    # requesting login info
    userID = request.form["userID"]
    pwd = request.form["pwd"]

    # hash to find possible student db
    hash_val = hash_student(userID)
    conn = sl.connect(hash_val)
    curs = conn.cursor()
    stmt_std = "SELECT `userID`, `password` FROM students WHERE `userID` = ? and `password` = ?"
    std_credential = curs.execute(stmt_std, (userID, pwd,)).fetchone()
    conn.close()

    # if student credential not empty
    if std_credential:
        session["login"] = True
        session["db"] = hash_val
        session["userID"] = userID

        # get session information
        session["student"], session["enrolled"], session["completed"] = \
            dba.get_student(session["db"], session["userID"])
        session["avail_courses"] = dba.get_available_courses(userID, session["db"])
        session["fname"] = session["student"][1]

        return redirect(url_for("home"))

    conn = sl.connect(dbs[0])
    curs = conn.cursor()
    stmt = "SELECT `adminID`, `password` FROM admins WHERE `adminID` = ? and `password` = ?"
    admin_credential = curs.execute(stmt, (userID, pwd,)).fetchone()
    conn.close()

    # if admin credential not empty
    if admin_credential:
        session["login"] = True
        session["adminID"] = userID

        # get session information
        admin = dba.get_admin(session["adminID"])
        session["admin"] = admin
        return redirect(url_for("home"))

    return render_template("login.html")  # change name kwarg later


# choose an action for student/admin
@app.route('/action', methods=["POST"])
def action():
    # error check for not selecting options
    if "data_request" not in session:
        try:
            session["data_request"] = request.form["data_request"]
        except:
            return redirect(url_for("home"))

    if "student" in session:
        fname = session["fname"]
        student = session["student"]
        userID = session["userID"]
        data_request = session["data_request"]
        avail_courses = session["avail_courses"]
        cmplt_courses = session["completed"]
        enr_courses = session["enrolled"]
        template = ""

        if data_request == "Adding":
            template = "adding_courses.html"
        else:
            template = "removing_courses.html"

        return render_template(template, data_request=data_request, fname=fname, student=student,
                               userID=userID, cmplt_courses=cmplt_courses, enr_courses=enr_courses,
                               avail_courses=avail_courses)

    fname = session["fname"]
    admin = session["admin"]
    adminID = session["adminID"]
    data_request = session["data_request"]
    courses = dba.get_all_courses()
    template = ""
    action_text = ""
    # add to course catalog
    if data_request == "catalog":
        template = "course_catalog.html"
        action_text = "Add to Course Catalog"
        return render_template(template, data_request=data_request, fname=fname, action_text=action_text, admin=admin,
                               adminID=adminID, courses=courses)
    # add a student
    elif data_request == "add_student":
        template = "add_student.html"
        action_text = "Add Student"
    # remove a student
    elif data_request == "remove_student":
        action_text = "Remove a Student"
        template = "remove_student.html"
    # move courses from enrolled to completed
    else:
        action_text = "Search for a Student"
        template = "search_student.html"
    return render_template(template, data_request=data_request, fname=fname, action_text=action_text, admin=admin,
                           adminID=adminID)


# enroll in a course
@app.route('/enroll', methods=["POST"])
def enroll():
    courseID = ""
    try:
        courseID = request.form["courseID"]
    except:
        return redirect(url_for("action"))

    userID = session["userID"]
    db = hash_student(userID)
    dba.enroll(userID, courseID, "SU", 2024)

    # update session information
    session["student"], session["enrolled"], session["completed"] = \
        dba.get_student(db, session["userID"])
    session["avail_courses"] = dba.get_available_courses(userID, session["db"])
    data_request = session["data_request"]
    student = session["student"]
    fname = student[1]
    cmplt_courses = session["completed"]
    enr_courses = session["enrolled"]
    avail_courses = session["avail_courses"]

    return render_template("adding_courses.html", data_request=data_request, fname=fname, student=student,
                           userID=userID, cmplt_courses=cmplt_courses, enr_courses=enr_courses,
                           avail_courses=avail_courses)


# disenroll a course
@app.route('/disenroll', methods=["POST"])
def disenroll():
    courseID = ""
    try:
        courseID = request.form["courseID"]
    except:
        return redirect(url_for("action"))

    userID = session["userID"]
    dba.disenroll(userID, courseID)

    # update session information
    session["student"], session["enrolled"], session["completed"] = \
        dba.get_student(session["db"], session["userID"])
    session["avail_courses"] = dba.get_available_courses(userID, session["db"])
    data_request = session["data_request"]
    student = session["student"]
    fname = student[1]
    cmplt_courses = session["completed"]
    enr_courses = session["enrolled"]
    avail_courses = session["avail_courses"]

    return render_template("removing_courses.html", data_request=data_request, fname=fname, student=student,
                           userID=userID, cmplt_courses=cmplt_courses, enr_courses=enr_courses,
                           avail_courses=avail_courses)


# add to course catalog
@app.route("/add_to_catalog", methods=["POST"])
def add_to_catalog():
    data_request = session["data_request"]
    fname = session["fname"]
    action_text = "Add to Course Catalog"
    admin = session["admin"]
    adminID = session["adminID"]
    courses = dba.get_all_courses()

    courseID = request.form["courseID"].strip()
    cname = request.form["cname"].strip()
    credits = request.form["credits"].strip()
    dept = request.form["dept"].strip()
    new_course = [courseID, cname, credits, dept]

    for attr in new_course:
        # check for empty field
        if attr.isspace():
            return render_template("course_catalog.html", data_request=data_request, fname=fname,
                                   action_text=action_text, admin=admin, adminID=adminID, courses=courses)

        # checking for duplicate course
        if attr == courseID:
            ids = [row[0] for row in courses]
            if courseID in ids:
                return render_template("course_catalog.html", data_request=data_request, fname=fname,
                                       action_text=action_text, admin=admin, adminID=adminID, courses=courses)

        # check that credits is an int
        if attr == credits:
            try:
                credits = int(credits)
            except:
                return render_template("course_catalog.html", data_request=data_request, fname=fname,
                                       action_text=action_text, admin=admin, adminID=adminID, courses=courses)

    dba.add_course(new_course[0], new_course[1], new_course[2], new_course[3])
    courses = dba.get_all_courses()

    return render_template("course_catalog.html", data_request=data_request, fname=fname, action_text=action_text,
                           admin=admin, adminID=adminID, courses=courses)


# search for a student
@app.route("/search_student", methods=["POST"])
def search_student():
    admin = session["admin"]
    adminID = session["adminID"]
    fname = session["fname"]
    data_request = session["data_request"]
    action_text = "Search for a Student"
    userID = request.form["userID"]
    db = hash_student(userID)
    # no student found
    student, enr_courses, cmplt_courses = dba.get_student(db, userID)
    if not student:
        return render_template("search_student.html", data_request=data_request, fname=fname, action_text=action_text,
                               admin=admin, adminID=adminID)

    action_text = "Move from Enrolled to Completed"

    return render_template("admin_view_student.html", action_text=action_text, admin=admin, fname=fname,
                           adminID=adminID, userID=userID, student=student, enr_courses=enr_courses,
                           cmplt_courses=cmplt_courses)


# move course from enrolled to completed
@app.route("/move_course", methods=["POST"])
def move_course():
    admin = session["admin"]
    fname = session["fname"]
    adminID = session["adminID"]
    action_text = "Move from Enrolled to Completed"
    userID = request.form["userID"]
    db = hash_student(userID)
    student, enr_courses, cmplt_courses = dba.get_student(db, userID)
    courseID = ""

    # tests for empty information
    try:
        courseID = request.form["courseID"]
    except:
        return render_template("admin_view_student.html", action_text=action_text, admin=admin, fname=fname,
                               adminID=adminID, userID=userID, student=student, enr_courses=enr_courses,
                               cmplt_courses=cmplt_courses)

    # move course
    dba.move_course(userID, courseID)
    student, enr_courses, cmplt_courses = dba.get_student(db, userID)

    return render_template("admin_view_student.html", action_text=action_text, admin=admin, fname=fname,
                           adminID=adminID, userID=userID, student=student, enr_courses=enr_courses,
                           cmplt_courses=cmplt_courses)


# add a new student
@app.route("/add_student", methods=["POST"])
def add_student():
    # template info
    action_text = "Add Student"
    data_request = session["data_request"]
    admin = session["admin"]
    adminID = session["adminID"]
    admin_fname = session["fname"]

    # requested info
    userID = request.form["userID"].strip()
    pwd = request.form["pwd"].strip()
    lname = request.form["lname"].strip()
    fname = request.form["fname"].strip()
    major = request.form["major"].strip()

    # check if anything is blank
    student = [userID, pwd, lname, fname, major]
    for attr in student:
        if attr.isspace():
            return render_template("add_student.html", data_request=data_request, fname=admin_fname,
                                   action_text=action_text, admin=admin,
                                   adminID=adminID)
    # add student
    db = hash_student(userID)
    dba.add_student(db, userID, pwd, lname, fname, major)

    return render_template("add_student.html", data_request=data_request, fname=admin_fname, action_text=action_text,
                           admin=admin,
                           adminID=adminID)


# remove student
@app.route("/remove_student", methods=["POST"])
def remove_student():
    action_text = "Remove a Student"
    admin = session["admin"]
    fname = session["fname"]
    adminID = session["adminID"]
    data_request = session["data_request"]

    # check if field is empty
    userID = request.form["userID"].strip()
    if userID.isspace():
        return render_template("remove_student.html", data_request=data_request, fname=fname, action_text=action_text,
                               admin=admin, adminID=adminID)
    # attempt to remove student
    db = hash_student(userID)
    dba.remove_student(db, userID)

    return render_template("remove_student.html", data_request=data_request, fname=fname, action_text=action_text,
                           admin=admin, adminID=adminID)


# return home
@app.route("/back", methods=["POST"])
def back():
    del session["data_request"]
    return redirect(url_for("home"))


# logout
@app.route('/logout', methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("back"))


@app.route('/<path:path>')
def catch_all(path):
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(debug=True)
