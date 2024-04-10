import datetime
from itertools import count
from turtle import title
import cursor as cursor
import os
import re
from bson import ObjectId
from flask import Flask, request, render_template, redirect, session
import pymongo

from Mail import send_email

app = Flask(__name__)
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
APP_ROOT = APP_ROOT + "/static/books"
app.secret_key = "Library Management System"
my_conn = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = my_conn["library_management_system"]
admin_col = mydb["admin"]
member_col = mydb["member"]
librarian_col = mydb["librarian"]
books_col = mydb["books"]
payment_col = mydb["payment"]
location_col = mydb["location"]
transcation_col = mydb["transcation"]
reserve_col = mydb["reserve"]
if admin_col.count_documents({}) == 0:
    admin_col.insert_one({"username": "admin", "password": "admin"})


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/admin_login")
def admin_login():
    return render_template("admin_login.html")


@app.route("/admin_login1", methods=["post"])
def admin_login1():
    username = request.form.get("username")
    password = request.form.get("password")
    query = {"username": username, "password": password}
    count = admin_col.count_documents(query)
    if count > 0:
        admin = admin_col.find_one(query)
        session["admin_id"] = str(admin["_id"])
        session["role"] = 'admin'
        return redirect("/admin_home")
    else:
        return render_template("message2.html", message="Invalid Login Details")


@app.route("/admin_home")
def admin_home():
    admin_id = session["admin_id"]
    query = {"_id": ObjectId(admin_id)}
    admin = admin_col.find_one(query)
    return render_template("admin_home.html", admin=admin)


@app.route("/add_librarians")
def add_librarians():
    librarians = librarian_col.find({})
    librarians = list(librarians)
    return render_template("add_librarians.html", librarians=librarians)


@app.route("/add_librarians1", methods=["post"])
def add_librarians1():
    name = request.form.get("name")
    email = request.form.get("email")
    phone = request.form.get("phone")
    password = request.form.get("password")
    gender = request.form.get("gender")
    age = request.form.get("age")
    location_name = request.form.get("location_name")
    query = {'location_name': location_name}
    count = location_col.count_documents(query)
    if count > 0:
        return render_template("message.html", message="This location already exists")
    # print(name,email,phone,password)
    query = {"$or": [{"email": email}, {"phone": phone}]}
    count = librarian_col.count_documents(query)
    if count == 0:
        query = {"name": name, "email": email, "phone": phone, "password": password, "age": age, "gender": gender}
        result = librarian_col.insert_one(query)
        librarian_id = result.inserted_id
        query = {"librarian_id": librarian_id, "location_name": location_name}
        location_col.insert_one(query)
        return render_template("message2.html", message="Librarian Added Successful")
    else:
        return render_template("message2.html", message="Duplicate Entry")


@app.route("/locations")
def locations():
    locations = location_col.find({})
    locations = list(locations)
    return render_template("locations.html", locations=locations)


@app.route("/librarian_login")
def librarian_login():
    return render_template("librarian_login.html")


@app.route("/librarian_login1", methods=["post"])
def librarian_login1():
    email = request.form.get("email")
    password = request.form.get("password")
    query = {"email": email, "password": password}
    count = librarian_col.count_documents(query)
    if count > 0:
        librarian = librarian_col.find_one(query)
        query = {"location_id": ["_id"]}
        location_col.find_one(query)
        session["librarian_id"] = str(librarian["_id"])
        session["role"] = 'librarian'
        return redirect("/librarian_home")
    else:
        return render_template("message2.html", message="Invalid Login Details", color="text-danger")


@app.route("/librarian_home")
def librarian_home():
    librarian_id = session["librarian_id"]
    query = {"_id": ObjectId(librarian_id)}
    librarian = librarian_col.find_one(query)
    return render_template("librarian_home.html", librarian=librarian)


@app.route("/add_books")
def add_books():
    books = books_col.find()
    books = list(books)
    locations = location_col.find()
    return render_template("add_books.html", locations=locations, books=books)


@app.route("/add_book1", methods=["post"])
def add_book1():
    book_name = request.form.get("book_name")
    book_image = request.files.get("book_image")
    book_author = request.form.get("book_author")
    book_publisher = request.form.get("book_publisher")
    book_price = request.form.get("book_price")
    book_description = request.form.get("book_description")
    query = {"book_name": book_name}
    count = books_col.count_documents(query)
    if count == 0:
        path = APP_ROOT + "/" + book_image.filename
        book_image.save(path)
        query = {"book_name": book_name, "book_image": book_image.filename, "book_author": book_author,
                 "book_publisher": book_publisher, "book_price": book_price, "book_description": book_description}
        books_col.insert_one(query)
        return render_template("message.html", message="Book Added successfully")
    else:
        return render_template("message.html", message="Book is Already Exist")


@app.route("/view_books_member")
def view_books_member():
    return render_template("view_books_member.html")


@app.route("/get_books")
def get_books():
    keyword = request.args.get("keyword")
    keyword = re.compile(".*" + keyword + ".*", re.IGNORECASE)
    query = {"$or": [{"book_name": keyword}, {"book_publisher": keyword}]}
    books = books_col.find(query)
    return render_template("get_books.html", books=books)


@app.route("/view_books")
def view_books():
    locations = location_col.find({})
    locations = list(locations)
    books = books_col.find()
    books = list(books)
    if session['role'] == 'librarian':
        librarian_id=session["librarian_id"]
        return render_template("view_books.html", books=books, librarian_id=librarian_id, locations=locations,
                               get_location_by_librarian_id=get_location_by_librarian_id)
    return render_template("view_books.html", books=books,locations=locations)


def get_location_by_librarian_id(librarian_id):
    query = {"librarian_id": ObjectId(librarian_id)}
    location = location_col.find_one(query)
    return location


@app.route("/add_book_copies")
def add_book_copies():
    book_id = request.args.get("book_id")
    return render_template("add_book_copies.html", book_id=book_id)


@app.route("/add_book_copy1")
def add_book_copy1():
    no_of_copies = request.args.get("no_of_copies")
    book_id = request.args.get("book_id")
    librarian_id = session["librarian_id"]
    copies = []
    for i in range(1, int(no_of_copies) + 1):
        copy = "Copy "+str(i)
        copies.append(copy)
    query1 = {"_id": ObjectId(book_id)}
    book = books_col.find_one(query1)
    if 'book_copies' not in book:
        query2 = {"$set": {"book_copies": {str(librarian_id): copies}}}
        books_col.update_one(query1, query2)
    else:
        for copy in copies:
            count = books_col.count_documents({"book_copies." + str(librarian_id): copy})
            if count == 0:
                query2 = {"$push": {"book_copies." + str(librarian_id): copy}}
                books_col.update_one(query1, query2)
            else:
                return render_template("message.html", message="Duplicate Book Copy Number " + str(copy))
    return render_template("message.html", message="Added successfully")


@app.route("/view_book_copies")
def view_book_copies():
    book_id = request.args.get("book_id")
    query = {"_id": ObjectId(book_id)}
    books = books_col.find(query)
    books = list(books)
    return render_template("view_book_copies.html", books=books, str=str,
                           get_librarian_by_librarian_id=get_librarian_by_librarian_id)


def get_librarian_by_librarian_id(librarian_id):
    query = {"_id": ObjectId(librarian_id)}
    librarian = librarian_col.find_one(query)
    query = {"librarian_id": librarian['_id']}
    location = location_col.find_one(query)
    return librarian, location


@app.route("/logout")
def logout():
    session.clear()
    return render_template("home.html")


@app.route("/member_login")
def member_login():
    return render_template("member_login.html")


@app.route("/member_login1", methods=["post"])
def member_login1():
    email = request.form.get("email")
    password = request.form.get("password")
    query = {"email": email, "password": password}
    count = member_col.count_documents(query)
    if count > 0:
        member = member_col.find_one(query)
        session["member_id"] = str(member["_id"])
        session["role"] = 'member'
        return redirect("/member_home")
    else:
        return render_template("message2.html", message="Invalid Login Details")


@app.route("/member_register")
def member_register():
    return render_template("member_register.html")


@app.route("/member_register1", methods=["post"])
def member_register1():
    name = request.form.get("name")
    email = request.form.get("email")
    phone = request.form.get("phone")
    age = request.form.get("age")
    password = request.form.get("password")
    gender = request.form.get("gender")
    query = {"$or": [{"email": email}, {"phone": phone}]}
    count = member_col.count_documents(query)
    if count == 0:
        query = {"name": name, "email": email, "phone": phone, "age": age, "password": password, "gender": gender}
        member_col.insert_one(query)
        return render_template("message2.html", message="Member Registered Successful")
    else:
        return render_template("message2.html", message="Duplicate Entry")


@app.route("/member_home")
def member_home():
    return render_template("member_home.html")


@app.route("/sent_book_request")
def sent_book_request():
    book_id = request.args.get("book_id")
    query = {"_id": ObjectId(book_id)}
    book = books_col.find_one(query)
    return render_template("sent_book_request.html", book=book,
                           get_librarian_by_librarian_id=get_librarian_by_librarian_id,
                           check_is_book_available2=check_is_book_available2)


@app.route("/librarian_send_request")
def librarian_send_request():
    librarian_id = request.args.get('librarian_id')
    book_id = request.args.get("book_id")
    member_id = session['member_id']
    status = request.args.get("status")
    query = {'librarian_id': ObjectId(librarian_id), "book_id": ObjectId(book_id), "member_id": ObjectId(member_id),
             "status": "Request Sent"}
    transcation_col.insert_one(query)
    return render_template("message.html", message="Request send successfully")


@app.route("/librarian_reserve_bool")
def librarian_reserve_bool():
    librarian_id = request.args.get('librarian_id')
    book_id = request.args.get("book_id")
    member_id = session['member_id']
    status = request.args.get("status")
    query = {'librarian_id': ObjectId(librarian_id), "book_id": ObjectId(book_id), "member_id": ObjectId(member_id),
             "status": "Reserved"}
    result = transcation_col.insert_one(query)
    transaction_id = result.inserted_id
    query = {"transaction_id": transaction_id, "member_id": ObjectId(member_id), "date": datetime.datetime.now(),
             "status": "reserve requested"}
    reserve_col.insert_one(query)
    return render_template("message.html", message="Book is Reserved we will notify once it is available")


@app.route("/view_book_request")
def view_book_request():
    type = request.args.get("type")
    if session["role"] == 'librarian':
        librarian_id = session['librarian_id']
        if type == 'requested':
            query = {'status': 'Request Sent'}
        if type == 'processing':
            query = {"$or": [{'status': 'book assigned'},
                             {'status': 'book return requested'}]}
        if type == 'history':
            query = {"$or": [{'status': 'cancelled'},
                             {'status': 'return accepted'}]}
        if type == 'reserved':
            query = {"$or": [{'status': 'Reserved'}]}

    if session['role'] == 'member':
        member_id = session['member_id']
        if type == 'reserved':
            query = {"member_id": ObjectId(member_id), 'status': 'Reserved'}
        else:
            query = {"member_id": ObjectId(member_id)}
        transactions = transcation_col.find(query)
        transactions = list(transactions)
        return render_template("view_book_request.html", transactions=transactions,
                               get_book_by_book_id=get_book_by_book_id, get_member_by_member_id=get_member_by_member_id,
                               get_fine_by_transaction_id=get_fine_by_transaction_id, get_reservation=get_reservation,
                               has_paid=has_paid)
    else:
        transactions = transcation_col.find(query)
        transactions = list(transactions)
        transactions.reverse()
        return render_template("view_book_request.html", transactions=transactions,
                               get_book_by_book_id=get_book_by_book_id, get_member_by_member_id=get_member_by_member_id,
                               get_fine_by_transaction_id=get_fine_by_transaction_id, get_reservation=get_reservation,
                               has_paid=has_paid)


def get_book_by_book_id(book_id):
    query = {"_id": ObjectId(book_id)}
    book = books_col.find_one(query)
    return book


def get_member_by_member_id(member_id):
    query = {"_id": ObjectId(member_id)}
    member = member_col.find_one(query)
    return member


@app.route("/cancel_request")
def cancel_request():
    transaction_id = request.args.get('transaction_id')
    query = {"_id": ObjectId(transaction_id)}
    query1 = {"$set": {"status": "cancelled"}}
    transcation_col.update_one(query, query1)
    return render_template("message.html", message="Request Cancelled")


@app.route("/assign_book_copies")
def assign_book_copies():
    book_id = request.args.get("book_id")
    transaction_id = request.args.get("transaction_id")
    query = {"_id": ObjectId(book_id)}
    books = books_col.find(query)
    books = list(books)
    return render_template("assign_book_copies.html", books=books, transaction_id=transaction_id, book_id=book_id,
                           check_is_book_available=check_is_book_available)


@app.route("/assign_book_copy1")
def assign_book_copy1():
    book_copy = request.args.get("book_copy")
    book_id = request.args.get("book_id")
    query = {"_id": ObjectId(book_id)}
    books = books_col.find_one(query)

    status = 'book assigned'
    transaction_id = request.args.get("transaction_id")
    check_in = datetime.datetime.now()
    check_out = check_in + datetime.timedelta(days=15)
    query = {'_id': ObjectId(transaction_id)}
    query2 = {"$set": {'book_copy': book_copy, 'check_in': check_in, 'check_out': check_out,
                       'status': status}}
    transcation_col.update_one(query, query2)
    return render_template("message.html", message="Book Assigned")


@app.route("/return_book")
def return_book():
    transaction_id = request.args.get("transaction_id")
    fine = request.args.get('fine')
    if int(fine) > 0:
        return render_template("payments.html", transaction_id=transaction_id, fine=fine)
    status = 'book return requested'
    query = {"_id": ObjectId(transaction_id)}
    query2 = {"$set": {'status': status}}
    transcation_col.update_one(query, query2)
    return render_template("message.html", message="Book Return Requested")


@app.route("/accept")
def accept():
    status = 'return accepted'
    check_out = datetime.datetime.now()
    transaction_id = request.args.get("transaction_id")
    query = {"_id": ObjectId(transaction_id)}
    query2 = {"$set": {'status': status, 'check_out': check_out}}
    transcation_col.update_one(query, query2)
    transaction = transcation_col.find_one(query)
    query = {"book_id": transaction['book_id'], "status": "Reserved"}
    transactions = transcation_col.find(query)
    query = {"_id": transaction['book_id']}
    book = books_col.find_one(query)
    for transaction in transactions:
        query = {"_id": transaction["member_id"]}
        member = member_col.find_one(query)
        query = {"_id": transaction["librarian_id"]}
        librarian = librarian_col.find_one(query)
        subject = "Book " + book["book_name"] + " is Available at Librarian " + librarian["name"]
        message = "Hello " + member["name"] + " Book " + book["book_name"] + " is Available at Librarian " + librarian[
            "name"] + " You can send Request Now";
        email = member['email']
        send_email(subject, message, email)
    return render_template("message.html", message="Book Accepted")


def get_fine_by_transaction_id(transaction_id):
    query = {"_id": ObjectId(transaction_id), "status": "book assigned"}
    transaction = transcation_col.find_one(query)
    if transaction == None:
        return 0

    today = datetime.datetime.now()
    if transaction['check_out'] > today:
        return 0
    diff = today - transaction['check_out']
    hours = diff.total_seconds() / 3600
    days = int(hours / 24)
    if hours % 24 > 0:
        days = days + 1
    return days


@app.route('/payment1', methods=['post'])
def payment1():
    transaction_id = request.form.get("transaction_id")
    member_id = request.form.get("member_id")
    fine = request.form.get("fine")
    status = request.form.get("status")
    card_type = request.form.get("card_type")
    card_number = request.form.get("card_number")
    card_name = request.form.get("card_name")
    cvv = request.form.get("cvv")
    date = datetime.datetime.now()
    expiry_date = request.form.get("expiry_date")
    query = {'transaction_id': ObjectId(transaction_id), 'member_id': ObjectId(member_id), 'fine': fine,
             'status': status, 'card_number': card_number, 'card_name': card_name, 'card_type': card_type,
             'expiry_date': expiry_date, 'cvv': cvv,
             'date': date}
    query1 = {'_id': ObjectId(transaction_id)}
    status = 'book return requested'
    query2 = {"$set": {'status': status}}
    transcation_col.update_one(query1, query2)
    payment_col.insert_one(query)
    return render_template("message.html", message="Payment done successfully")


@app.route("/set_status", methods=['post'])
def set_status():
    status = request.form.get('status')
    transaction_id = request.form.get('transaction_id')
    query1 = {'_id': ObjectId(transaction_id)}
    query2 = {"$set": {'status': status}}
    transcation_col.update_one(query1, query2)
    return render_template('message.html', message=status)


def check_is_book_available(book_id, book_copy_number, librarian_id):
    query = {"book_id": book_id, "book_copy": book_copy_number, "librarian_id": ObjectId(librarian_id)}
    from_date = datetime.datetime.now()
    to_date = from_date + datetime.timedelta(days=15)
    query = {"$or": [{"check_in": {"$gte": from_date, "$lte": to_date},
                      "check_out": {"$gte": from_date, "$gte": to_date},
                      "book_id": book_id, "book_copy": book_copy_number, "librarian_id": ObjectId(librarian_id)},
                     {"check_in": {"$lte": from_date, "$lte": to_date},
                      "check_out": {"$gte": from_date, "$lte": to_date},
                      "book_id": book_id, "book_copy": book_copy_number, "librarian_id": ObjectId(librarian_id)},
                     {"check_in": {"$lte": from_date, "$lte": to_date},
                      "check_out": {"$gte": from_date, "$gte": to_date},
                      "book_id": book_id, "book_copy": book_copy_number, "librarian_id": ObjectId(librarian_id)},
                     {"check_in": {"$gte": from_date, "$lte": to_date},
                      "check_out": {"$gte": from_date, "$lte": to_date},
                      "book_id": book_id, "book_copy": book_copy_number, "librarian_id": ObjectId(librarian_id)}]}
    count = transcation_col.count_documents(query)
    if count > 0:
        return False
    return True


def check_is_book_available2(book_id, librarian_id):
    from_date = datetime.datetime.now()
    to_date = from_date + datetime.timedelta(days=15)
    query = {"$or": [{"check_in": {"$gte": from_date, "$lte": to_date},
                      "check_out": {"$gte": from_date, "$gte": to_date},
                      "book_id": book_id, "librarian_id": ObjectId(librarian_id)},
                     {"check_in": {"$lte": from_date, "$lte": to_date},
                      "check_out": {"$gte": from_date, "$lte": to_date},
                      "book_id": book_id, "librarian_id": ObjectId(librarian_id)},
                     {"check_in": {"$lte": from_date, "$lte": to_date},
                      "check_out": {"$gte": from_date, "$gte": to_date},
                      "book_id": book_id, "librarian_id": ObjectId(librarian_id)},
                     {"check_in": {"$gte": from_date, "$lte": to_date},
                      "check_out": {"$gte": from_date, "$lte": to_date},
                      "book_id": book_id, "librarian_id": ObjectId(librarian_id)}]}
    count = transcation_col.count_documents(query)
    query = {"_id": book_id}
    book = books_col.find_one(query)
    count2 = 0
    if librarian_id in book['book_copies']:
        count2 = len(book['book_copies'][librarian_id])
    if count2 > count:
        return True
    return False


def get_reservation(transaction_id):
    query = {"transaction_id": transaction_id}
    reserve = reserve_col.find_one(query)
    return reserve


@app.route("/delete_reserved")
def delete_reserved():
    transaction_id = request.args.get('transaction_id')
    query = {'_id': ObjectId(transaction_id)}
    transcation_col.delete_one(query)
    query2 = {'transaction_id': ObjectId(transaction_id)}
    reserve_col.delete_one(query2)
    return render_template("message.html", message="Deleted")


def has_paid(transaction_id):
    query = {"transaction_id": transaction_id}
    payment = payment_col.find_one(query)
    return payment


@app.route("/view_payments")
def view_payments():
    transaction_id = request.args.get('transaction_id')
    query = {"transaction_id": ObjectId(transaction_id)}
    payment = payment_col.find_one(query)
    return render_template("view_payments.html", payment=payment)


app.run(debug=True)
