# Cameron Ela, ceela@usc.edu
# DSCI 551, Spring 2024
# Viterbi Web Registration Application
# This file uses sqlite3 to perform database actions on an SQLite databse

import sqlite3 as sl
from create_db import hash_student

dbs = ["INFORMATION.db", "STUDENTS1", "STUDENTS2", "STUDENTS3", "STUDENTS4"]


# get all courses from information db
def get_all_courses():
    conn = sl.connect(dbs[0])
    curs = conn.cursor()
    stmt = "SELECT * FROM courses ORDER BY courseID"
    courses = curs.execute(stmt).fetchall()
    conn.close()

    return courses


# get courses available to a student (not enrolled or completed)
def get_available_courses(userID, db_std):
    courses = get_all_courses()
    conn = sl.connect(db_std)
    curs = conn.cursor()

    # get courses enrolled for a student
    stmt_enr = "SELECT `courseID` FROM coursesEnrolled WHERE `userID` = ?"
    unavailable = curs.execute(stmt_enr, (userID,)).fetchall()
    # get courses completed for a student
    stmt_cmplt = "SELECT `courseID` FROM coursesCompleted WHERE `userID` = ?"
    # list of courses that should not appear in courses available to student
    unavailable = unavailable + curs.execute(stmt_cmplt, (userID,)).fetchall()

    courses_copy = [list(row) for row in courses]
    unavailable_ids = [str(row[0]) for row in unavailable]
    # list of course available to a student
    filtered_courses = [course for course in courses_copy if course[0] not in unavailable_ids]

    conn.close()

    return filtered_courses


# get student, courses enrolled, courses completed from student db
def get_student(db_std, userID):
    # get student info
    conn_std = sl.connect(db_std)
    curs_std = conn_std.cursor()
    stmt_std = "SELECT `lname`, `fname`, `units_completed`, `major` FROM students WHERE `userID` = ?"
    student = curs_std.execute(stmt_std, (userID,)).fetchone()

    # get courses enrolled
    conn_info = sl.connect(dbs[0])
    curs_info = conn_info.cursor()
    stmt_enr = "SELECT `courseID`, `semester`, `year` FROM coursesEnrolled " \
               "WHERE `userID` = ? ORDER BY `year`, `semester`, `courseID`"
    enr_result = curs_std.execute(stmt_enr, (userID,)).fetchall()
    enr_ids = [row[0] for row in enr_result]
    # get course names for courses enrolled
    placeholders = ','.join(['?'] * len(enr_ids))
    stmt_crs = f"SELECT `courseID`, `cname` FROM courses WHERE `courseID` IN ({placeholders})"
    crs_result = curs_info.execute(stmt_crs, enr_ids).fetchall()
    # add course names to courses enrolled
    enrolled = [list(row) for row in enr_result]
    for i in range(len(enr_ids)):
        for name in crs_result:
            if name[0] == enr_ids[i]:
                enrolled[i].insert(1, name[1])

    # get courses completed
    stmt_cmplt = "SELECT `courseID`, `semester`, `year` FROM coursesCompleted " \
                 "WHERE `userID` = ? ORDER BY `year`, `semester`, `courseID`"
    cmplt_result = curs_std.execute(stmt_cmplt, (userID,)).fetchall()
    cmplt_ids = [row[0] for row in cmplt_result]
    # get course names of courses completed
    placeholders = ','.join(['?'] * len(cmplt_ids))
    stmt_crs = f"SELECT `courseID`, `cname` FROM courses WHERE `courseID` IN ({placeholders})"
    crs_result = curs_info.execute(stmt_crs, cmplt_ids).fetchall()
    # add course names to courses completed
    completed = [list(row) for row in cmplt_result]
    for i in range(len(cmplt_ids)):
        for name in crs_result:
            if name[0] == cmplt_ids[i]:
                completed[i].insert(1, name[1])
                break

    conn_info.close()
    conn_std.close()

    return student, enrolled, completed


# get admin from information database
def get_admin(adminID):
    conn = sl.connect(dbs[0])
    curs = conn.cursor()
    stmt = "SELECT `lname`, `fname` FROM admins WHERE `adminID` = ?"
    admin = curs.execute(stmt, (adminID,)).fetchone()
    conn.close()

    return admin


# add course to information database
def add_course(courseID, cname, credits, dept):
    conn = sl.connect(dbs[0])
    curs = conn.cursor()

    stmt = "INSERT INTO courses values(?, ?, ?, ?)"
    curs.execute(stmt, (courseID, cname, credits, dept,))

    conn.commit()
    conn.close()


# move course from enrolled to completed
def move_course(userID, courseID):
    db = hash_student(userID)
    conn_std = sl.connect(db)
    curs_std = conn_std.cursor()
    conn_info = sl.connect(dbs[0])
    curs_info = conn_info.cursor()

    # insert course into coursesCompleted
    stmt_enr = "SELECT * FROM coursesEnrolled WHERE `courseID` = ?"
    course = curs_std.execute(stmt_enr, (courseID,)).fetchone()
    stmt_cmplt = "INSERT INTO coursesCompleted VALUES(?, ?, ?, ?)"
    curs_std.execute(stmt_cmplt, (course[0], course[1], course[2], course[3]))

    # add credits to student
    crs_cred = "SELECT `credits` FROM courses WHERE `courseID` = ?"
    old_cred = "SELECT `units_completed` FROM students WHERE `userID` = ?"
    new_cred = int(curs_std.execute(old_cred, (userID,)).fetchone()[0]) \
               + int(curs_info.execute(crs_cred, (courseID,)).fetchone()[0])
    stmt_credits = "UPDATE students SET `units_completed` = ? WHERE `userID` = ?"
    curs_std.execute(stmt_credits, (new_cred, userID,))

    # remove course from coursesEnrolled
    remove_stmt = "DELETE FROM coursesEnrolled WHERE `courseID` = ? AND `userID` = ?"
    curs_std.execute(remove_stmt, (courseID, userID))

    conn_info.close()
    conn_std.commit()
    conn_std.close()


# enroll in course
def enroll(userID, courseID, term, year):
    db = hash_student(userID)
    conn = sl.connect(db)
    curs = conn.cursor()
    stmt = "INSERT INTO coursesEnrolled VALUES(?, ?, ?, ?)"
    curs.execute(stmt, (courseID, userID, term, year))

    conn.commit()
    conn.close()


# disenroll a course
def disenroll(userID, courseID):
    db = hash_student(userID)
    conn = sl.connect(db)
    curs = conn.cursor()

    stmt = "DELETE FROM coursesEnrolled WHERE `courseID` = ? AND `userID` = ?"
    curs.execute(stmt, (courseID, userID))

    conn.commit()
    conn.close()


# add a student to a database
def add_student(db, userID, pwd, lname, fname, major):
    # check if userID exists
    conn_std = sl.connect(db)
    curs_std = conn_std.cursor()
    stmt_userID = "SELECT `userID` FROM students WHERE `userID` = ?"
    query = curs_std.execute(stmt_userID, (userID,)).fetchone()
    # if userID already exists
    if query:
        conn_std.close()
        return

    conn_info = sl.connect(dbs[0])
    curs_info = conn_info.cursor()
    # check if major exists
    stmt_major = "SELECT `programID` FROM programs"
    programs = [row[0] for row in curs_info.execute(stmt_major).fetchall()]
    major = major.strip()

    if major not in programs:
        conn_std.close()
        conn_info.close()
        return

    # input new student
    stmt_student = "INSERT INTO students VALUES(?, ?, ?, ?, ?, ?)"
    curs_std.execute(stmt_student, (userID, pwd, lname, fname, 0, major))

    conn_std.commit()
    conn_std.close()
    conn_info.close()


# remove student from database
def remove_student(db, userID):
    # check if userID exists
    conn = sl.connect(db)
    curs = conn.cursor()
    stmt_userID = "SELECT `userID` FROM students WHERE `userID` = ?"
    query = curs.execute(stmt_userID, (userID,)).fetchone()
    # if userID doesn't exist
    if not query:
        conn.close()
        return 1

    cmplt_delete = "DELETE FROM coursesCompleted WHERE `userID` = ?"
    curs.execute(cmplt_delete, (userID,))
    enr_delete = "DELETE FROM coursesEnrolled WHERE `userID` = ?"
    curs.execute(enr_delete, (userID,))
    std_delete = "DELETE FROM students WHERE `userID` = ?"
    curs.execute(std_delete, (userID,))

    conn.commit()
    conn.close()

    return 0
