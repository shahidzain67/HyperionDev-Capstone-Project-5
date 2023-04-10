"""
Relational database storage system based on a mock design of HyperionDevs database
Commands specify data to be displayed, which can then be saved in json or xml format

"""

import sqlite3
import json
import xml.etree.ElementTree as ET
import re

# Read create_database file
try:
    with open("create_database.sql", "r") as sql_file:
        sql_script = sql_file.read()
    conn = sqlite3.connect("HyperionDev.db")
except sqlite3.Error:
    print("Please store your database as HyperionDev.db")
    quit()

# Initialise cursor and execute create_database file
cur = conn.cursor()
cur.executescript(sql_script)
conn.commit()


def usage_is_incorrect(input, num_args):
    if len(input) != num_args + 1:
        print(f"The {input[0]} command requires {num_args} arguments.")
        return True
    return False


def store_data_as_json(data, filename):
    # Convert SQL data into list of dictionaries
    keys = [description[0] for description in data.description]
    rows = [dict(zip(keys, row)) for row in data.fetchall()]

    # Write data to JSON file
    with open(filename, "w") as f:
        json.dump(rows, f, indent=4)


def store_data_as_xml(data, filename):
    # initialise the tree
    root = ET.Element("rows")

    # Convert SQL data into list of dictionaries
    keys = [description[0] for description in data.description]

    # Create XML elements by iterating over rows
    for row in data.fetchall():
        row_val = ET.SubElement(root, "row")
        for i in range(len(keys)):
            col_val = ET.SubElement(row_val, keys[i])
            col_val.text = str(row[i])

    # Write XML tree to file
    tree = ET.ElementTree(root)
    tree.write(filename, xml_declaration=True, encoding="utf-8", method="xml")


def offer_to_store(data):
    while True:
        print("Would you like to store this result?")
        choice = input("Y/[N]? : ").strip().lower()

        if choice == "y":
            filename = input("Specify filename. Must end in .xml or .json: ")
            ext = filename.split(".")[-1]
            if ext == "xml":
                store_data_as_xml(data, filename)
            elif ext == "json":
                store_data_as_json(data, filename)
            else:
                print("Invalid file extension. Please use .xml or .json")

        elif choice == "n":
            break

        else:
            print("Invalid choice")

        break


def remove_non_alphanumeric(string):
    regex = re.compile(r"[^a-zA-Z0-9\s]+")
    return regex.sub("", string)


usage = """
What would you like to do?

d - demo
vs <student_id>            - view subjects taken by a student
la <firstname> <surname>   - lookup address for a given firstname and surname
lr <student_id>            - list reviews for a given student_id
lc <teacher_id>            - list all courses taken by teacher_id
lnc                        - list all students who haven't completed their course
lf                         - list all students who have completed their course and achieved 30 or below
e                          - exit this program

Type your option here: """

print("Welcome to the data querying app!")

while True:
    print()
    # Get input from user
    user_input = input(usage).split(" ")
    print()

    # Parse user input into command and args
    command = user_input[0]
    if len(user_input) > 1:
        args = user_input[1:]

    if (
        command == "d"
    ):  # demo - a nice bit of code from me to you - this prints all student names and surnames :)
        data = cur.execute("SELECT * FROM Student")
        for _, firstname, surname, _, _ in data:
            print(f"{firstname} {surname}")

    elif command == "vs":  # view subjects by student_id
        if usage_is_incorrect(user_input, 1):
            continue
        student_id = args[0]

        # Run SQL query and store in data
        data = cur.execute("SELECT student_id, course_code FROM StudentCourse")

        # Run SQL query to find course names
        student_course = cur.execute(
            "SELECT Course.course_name FROM Course LEFT JOIN StudentCourse ON StudentCourse.course_code = Course.course_code WHERE StudentCourse.student_id = ?",
            (student_id,),
        )

        # Iterate through courses and print them to the console
        all_courses = student_course.fetchall()
        courses = []
        count = 0
        for item in all_courses:
            courses.append(remove_non_alphanumeric(str(all_courses[count])))
            count += 1
        print("Courses:")
        for i in range(len(all_courses)):
            print(courses[i])

        # Run command to store data
        offer_to_store(data)

    elif command == "la":  # list address by name and surname
        if usage_is_incorrect(user_input, 2):
            continue
        firstname, surname = args[0], args[1]
        data = None

        # Run SQL query and store in data
        data = cur.execute(
            "SELECT * FROM Address LEFT JOIN Student ON Student.address_id = Address.address_id WHERE Student.first_name = ? AND Student.last_name = ?",
            (firstname, surname),
        )
        # Run SQL query to find street and city
        address = cur.execute(
            "SELECT Address.street, Address.city FROM Address LEFT JOIN Student ON Student.address_id = Address.address_id WHERE Student.first_name = ? AND Student.last_name = ?",
            (firstname, surname),
        )

        # Print street and city on console
        street_city = (
            str(address.fetchmany())
            .replace("'", "")
            .replace("(", "")
            .replace(")", "")
            .replace("[", "")
            .replace("]", "")
        )
        print(f"Address: {street_city}")

        # Run command to store data
        offer_to_store(data)

    elif command == "lr":  # list reviews by student_id
        if usage_is_incorrect(user_input, 1):
            continue
        student_id = args[0]
        data = None

        # Run SQL query and store in data
        data = cur.execute(
            "SELECT * FROM Review LEFT JOIN StudentCourse ON StudentCourse.student_id = Review.student_id WHERE StudentCourse.student_id = ?",
            (student_id,),
        )

        # Run SQL query to find completeness, efficiency, style, documentation and review text
        review_data = cur.execute(
            "SELECT Review.completeness, Review.efficiency, Review.style, Review.documentation, Review.review_text FROM Review LEFT JOIN StudentCourse ON StudentCourse.student_id = Review.student_id WHERE StudentCourse.student_id = ?",
            (student_id,),
        )

        # Iterate through courses and print completeness, efficiency, style, documentation and review text to the console
        all_reviews = review_data.fetchall()
        reviews = []
        count = 0
        for item in all_reviews:
            review = remove_non_alphanumeric(str(all_reviews[count]))
            reviews.append(remove_non_alphanumeric(str(all_reviews[count])))
            count += 1

        for i in range(len(all_reviews)):
            print(
                f"Review {i+1}:\nCompleteness: {reviews[i][0]}\nEfficiency: {reviews[i][1]}\nStyle: {reviews[i][2]}\nDocumentation: {reviews[i][3]}\nNotes: {reviews[i][4]}\n\n"
            )

        # Run command to store data
        offer_to_store(data)

    elif command == "lc":  # list all courses given by teacher_id
        if usage_is_incorrect(user_input, 1):
            continue
        teacher_id = args[0]
        data = None

        # Run SQL query and store in data
        data = cur.execute(
            "SELECT * FROM Course LEFT JOIN Teacher ON Teacher.teacher_id = Course.teacher_id WHERE Teacher.teacher_id = ?",
            (teacher_id,),
        )

        # Run SQL query to find course name
        course_data = cur.execute(
            "SELECT Course.course_name FROM Course FULL JOIN Teacher ON Teacher.teacher_id = Course.teacher_id WHERE Course.teacher_id = ?",
            (teacher_id,),
        )

        # Iterate through courses and print course names
        all_courses = course_data.fetchall()
        courses = []
        count = 0
        for item in all_courses:
            course = remove_non_alphanumeric(str(all_courses[count]))
            courses.append(remove_non_alphanumeric(str(all_courses[count])))
            count += 1

        for i in range(len(all_courses)):
            print(f"Course {i+1}: {courses[i]}")

        # Run command to store data
        offer_to_store(data)

    elif command == "lnc":  # list all students who haven't completed their course
        data = None

        # Run SQL query and store in data
        data = cur.execute(
            "SELECT * FROM StudentCourse LEFT JOIN Student ON Student.student_id = StudentCourse.student_id WHERE StudentCourse.is_complete = ?",
            ("0"),
        )

        # Run SQL query to find student number, first name, last name, email address and course names
        student_data = cur.execute(
            "SELECT StudentCourse.student_id, Student.first_name, Student.last_name, Student.email, Course.course_name FROM StudentCourse LEFT JOIN Student ON Student.student_id = StudentCourse.student_id LEFT JOIN Course ON Course.course_code = StudentCourse.course_code WHERE StudentCourse.is_complete = ?",
            ("0"),
        )

        # Iterate through students and print student number, first name, last name, email address and course names
        all_students = student_data.fetchall()
        students = []
        count = 0
        for item in all_students:
            student_tuple = (
                str(all_students[count])
                .replace("(", "")
                .replace(")", "")
                .replace("'", "")
            )
            students.append(student_tuple.split(","))
            count += 1

        for i in range(len(all_students)):
            print(
                f"\nStudent number: {students[i][0]}\nFirst name: {students[i][1]}\nLast name: {students[i][2]}\nEmail: {students[i][3]}\nCourse name: {students[i][4]}"
            )

        # Run command to store data
        offer_to_store(data)

    elif (
        command == "lf"
    ):  # list all students who have completed their course and got a mark <= 30
        data = None

        # Run SQL query and store in data
        data = cur.execute(
            "SELECT * FROM StudentCourse LEFT JOIN Student ON Student.student_id = StudentCourse.student_id WHERE StudentCourse.is_complete = ?",
            ("1"),
        )

        # Run SQL query to find student number, first name, last name, email address, course names and marks
        student_data = cur.execute(
            "SELECT StudentCourse.student_id, Student.first_name, Student.last_name, Student.email, Course.course_name, StudentCourse.mark FROM StudentCourse LEFT JOIN Student ON Student.student_id = StudentCourse.student_id LEFT JOIN Course ON Course.course_code = StudentCourse.course_code WHERE StudentCourse.is_complete = ?",
            ("1"),
        )

        # Iterate through students and print student number, first name, last name, email address, course names and marks
        all_students = student_data.fetchall()
        students = []
        count = 0
        for item in all_students:
            student_tuple = (
                str(all_students[count])
                .replace("(", "")
                .replace(")", "")
                .replace("'", "")
            )
            students.append(student_tuple.split(","))
            count += 1

        for i in range(len(all_students)):
            print(
                f"\nStudent number: {students[i][0]}\nFirst name: {students[i][1]}\nLast name: {students[i][2]}\nEmail: {students[i][3]}\nCourse name: {students[i][4]}\nMarks: {students[i][5]}"
            )

        # Run command to store data
        offer_to_store(data)

    elif command == "e":  # exit program
        print("Programme exited successfully!")
        break

    else:
        print(f"Incorrect command: '{command}'")
