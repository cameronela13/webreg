# Cameron Ela, ceela@usc.edu
# DSCI 551, Spring 2024
# Viterbi Web Registration Application
# This file uses sqlite3 to create and populate a database

import sqlite3 as sl
import json

dbs = ["INFORMATION.db", "STUDENTS1.db", "STUDENTS2.db", "STUDENTS3.db", "STUDENTS4.db"]


# creates a database
# stmts: list of table creating statements
def create(db, stmts):
    conn = sl.connect(db)
    curs = conn.cursor()

    for stmt in stmts:
        curs.execute(stmt)

    conn.commit()
    conn.close()


# hash function for students
def hash_student(userID):
    id_len = len(userID)
    mod = id_len % 4
    if mod == 0:
        return "STUDENTS1.db"
    elif mod == 1:
        return "STUDENTS2.db"
    elif mod == 2:
        return "STUDENTS3.db"
    else:
        return "STUDENTS4.db"

# populate information db
def populate_info(db, data):
    conn = sl.connect(db)
    curs = conn.cursor()

    curs.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = curs.fetchall()
    table_names = [table[0] for table in tables]

    # insert data
    for table, file in zip(table_names, data):
        with open(file, "r") as infile:
            json_data = json.load(infile)
            for line in json_data:
                placeholders = ', '.join(['?'] * len(line))
                stmt = f"INSERT INTO {table} VALUES ({placeholders})"
                curs.execute(stmt, tuple(line.values()))

    conn.commit()
    conn.close()


# populate student dbs
def populate_student(db, data):
    conn = sl.connect(db)
    curs = conn.cursor()

    curs.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = curs.fetchall()
    table_names = [table[0] for table in tables]

    # insert data
    for table, file in zip(table_names, data):
        with open(file, "r") as infile:
            json_data = json.load(infile)
            for line in json_data:
                # checks hash values for data entry
                if hash_student(line["userID"]) == db:
                    placeholders = ', '.join(['?'] * len(line))
                    stmt = f"INSERT INTO {table} VALUES ({placeholders})"
                    curs.execute(stmt, tuple(line.values()))

    conn.commit()
    conn.close()


def main():
    # table statements for information db
    courses = "CREATE TABLE IF NOT EXISTS courses (courseID VARCHAR(20) PRIMARY KEY, cname VARCHAR(50) NOT NULL, " \
              "credits INT CHECK (credits BETWEEN 1 AND 4), " \
              "dept VARCHAR(20) REFERENCES programs(dept) ON DELETE CASCADE ON UPDATE CASCADE)"
    programs = "CREATE TABLE IF NOT EXISTS programs (programID VARCHAR(50) PRIMARY KEY, dept VARCHAR(20))"
    admins = "CREATE TABLE IF NOT EXISTS admins (adminID VARCHAR(20) PRIMARY KEY, password VARCHAR(20) NOT NULL, " \
             "fname VARCHAR(20) NOT NULL, lname VARCHAR(20) NOT NULL)"
    info_tables = [courses, programs, admins]
    info_data = ["Data/courses.json", "Data/programs.json", "Data/admins.json"]

    # table statements for student dbs
    students = "CREATE TABLE IF NOT EXISTS students (userID VARCHAR(20) PRIMARY KEY, " \
               "password VARCHAR(20) NOT NULL, fname VARCHAR(20) NOT NULL, lname VARCHAR(20) NOT NULL, " \
               "units_completed INT NOT NULL, major VARCHAR(50))"
    crs_enr = "CREATE TABLE IF NOT EXISTS coursesEnrolled (courseID VARCHAR(20), " \
              "userID VARCHAR(20) REFERENCES students(userID) ON DELETE CASCADE ON UPDATE CASCADE, " \
              "semester CHAR(2) NOT NULL, year INT NOT NULL, PRIMARY KEY (courseID, userID))"
    crs_cmplt = "CREATE TABLE IF NOT EXISTS coursesCompleted (courseID VARCHAR(20), " \
                "userID VARCHAR(20) REFERENCES students(userID) ON DELETE CASCADE ON UPDATE CASCADE, " \
                "semester CHAR(2) NOT NULL, year INT NOT NULL, PRIMARY KEY (courseID, userID))"
    student_tables = [students, crs_enr, crs_cmplt]
    student_data = ["Data/students.json", "Data/crs_enr.json", "Data/crs_cmplt.json"]

    # create databases
    for db in dbs:
        if db != dbs[0]:
            create(db, student_tables)
        else:
            create(db, info_tables)

    # populate databases
    for db in dbs:
        if db != dbs[0]:
            populate_student(db, student_data)
        else:
            populate_info(db, info_data)


if __name__ == "__main__":
    main()
