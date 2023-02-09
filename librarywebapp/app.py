from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
import re
from datetime import datetime
import mysql.connector
from mysql.connector import FieldType
import connect
from flask import Flask, redirect, render_template, request, session

app = Flask(__name__)

app.secret_key = "secret_key" # use a secret key to securely store session data


dbconn = None
connection = None

def getCursor():
    global dbconn
    global connection
    connection = mysql.connector.connect(user=connect.dbuser, \
    password=connect.dbpass, host=connect.dbhost, \
    database=connect.dbname, autocommit=True)
    dbconn = connection.cursor()
    return dbconn

@app.route("/")
def home():
    return render_template("route.html")

@app.route("/listbooks")
def listbooks():
    connection = getCursor()
    sql= """select br.borrowerid, br.firstname, br.familyname,  
                l.borrowerid, l.bookcopyid, l.loandate, l.returned, b.bookid, b.booktitle, b.author, 
                b.category, b.yearofpublication, bc.format 
            from books b
                inner join bookcopies bc on b.bookid = bc.bookid
                    inner join loans l on bc.bookcopyid = l.bookcopyid
                        inner join borrowers br on l.borrowerid = br.borrowerid
            where l.returned = 1
            order by br.familyname, br.firstname, l.loandate;"""        
    connection.execute(sql)
    bookList = connection.fetchall()
    return render_template("booklist.html", booklist = bookList)    

@app.route("/loanbook", methods=["GET"])
def loanbook():
    todaydate = datetime.now().date()
    borrowerid = request.args.get('borrowerid')
    connection = getCursor()
    if borrowerid:
         connection.execute("SELECT * FROM borrowers where borrowerid=%s;",(borrowerid,))
    else:
        connection.execute("SELECT * FROM borrowers;")

    borrowerList = connection.fetchall()
    sql = """SELECT * FROM bookcopies
        inner join books on books.bookid = bookcopies.bookid
        WHERE bookcopyid not in (SELECT bookcopyid from loans where returned <> 1 or returned is NULL)
        OR (bookcopies.format = 'ebook' OR bookcopies.format = 'Audio Book');"""
    connection.execute(sql)
    bookList = connection.fetchall()
    return render_template("addloan.html", loandate = todaydate,borrowers = borrowerList, books= bookList,borrowerid=borrowerid)

@app.route("/loan/add", methods=["POST"])
def addloan():
    borrowerid = request.form.get('borrower')
    bookid = request.form.get('book')
    loandate = request.form.get('loandate')
    cur = getCursor()
    cur.execute("INSERT INTO loans (borrowerid, bookcopyid, loandate, returned) VALUES(%s,%s,%s,0);",(borrowerid, bookid, str(loandate),))
    return redirect("/currentloans")

@app.route("/listborrowers")
def listborrowers():
    connection = getCursor()
    connection.execute("SELECT * FROM borrowers;")
    borrowerList = connection.fetchall()
    return render_template("borrowerlist.html", borrowerlist = borrowerList)

@app.route("/currentloans")
def currentloans():
    connection = getCursor()
    sql=""" select br.borrowerid, br.firstname, br.familyname,  
                l.borrowerid, l.bookcopyid, l.loandate, l.returned, b.bookid, b.booktitle, b.author, 
                b.category, b.yearofpublication, bc.format,l.loanid 
            from books b
                inner join bookcopies bc on b.bookid = bc.bookid
                    inner join loans l on bc.bookcopyid = l.bookcopyid
                        inner join borrowers br on l.borrowerid = br.borrowerid
            order by br.familyname, br.firstname, l.loandate;"""
    connection.execute(sql)
    loanList = connection.fetchall()
    return render_template("currentloans.html", loanlist = loanList)

# add public access /route
@app.route("/route")
def publicroute():
    return render_template("route.html")

# add staff access /route
@app.route("/staff")
def staffroute():
    return render_template("staffroute.html")
   
@app.route("/searchbooks", methods=["POST"])
def searchbooks():
    todaydate = datetime.now().date()
    catalogue=request.form.get('catalogue')
    selectedcatalogue ="All"
    if catalogue == "title": 
        selectedcatalogue = "b.booktitle" 
    elif catalogue == "author": 
        selectedcatalogue = "b.author"
    searchterm=request.form.get('search')
    searchterm="%" +searchterm +"%"
    allsql= """select br.borrowerid, br.firstname, br.familyname,  
                l.borrowerid, l.bookcopyid, l.loandate, l.returned, b.bookid, b.booktitle, b.author, 
                b.category, b.yearofpublication, bc.format 
            from books b
                inner join bookcopies bc on b.bookid = bc.bookid
                    inner join loans l on bc.bookcopyid = l.bookcopyid
                        inner join borrowers br on l.borrowerid = br.borrowerid
            where %s LIKE %s or %s LIKE %s
            order by br.familyname, br.firstname, l.loandate;"""
    sql= """select br.borrowerid, br.firstname, br.familyname,  
                l.borrowerid, l.bookcopyid, l.loandate, l.returned, b.bookid, b.booktitle, b.author, 
                b.category, b.yearofpublication, bc.format 
            from books b
                inner join bookcopies bc on b.bookid = bc.bookid
                    inner join loans l on bc.bookcopyid = l.bookcopyid
                        inner join borrowers br on l.borrowerid = br.borrowerid
            where %s LIKE %s
            order by br.familyname, br.firstname, l.loandate;"""        
    allparameters=("b.booktitle",searchterm,"b.author",searchterm)
    parameters=(selectedcatalogue,searchterm)
    connection = getCursor()
    if selectedcatalogue =="All":
        connection.execute(allsql,allparameters)
    else : connection.execute(sql,parameters)
    bookList = connection.fetchall()
    return render_template("booklist.html", booklist = bookList,loandate = todaydate)
    
@app.route("/searchborrower", methods=["POST"])
def searchborrower():
    connection = getCursor()
    searchterm = request.form.get('search')
    if searchterm.isdigit() == True:
        connection.execute("SELECT * FROM borrowers where borrowerid = %s;",(searchterm,))
    else: 
        searchterm="%" +searchterm +"%"
        connection.execute("SELECT * FROM borrowers where firstname LIKE %s or familyname LIKE %s;",(searchterm,searchterm))
    borrowerList = connection.fetchall()
    return render_template("borrowerlist.html", borrowerlist = borrowerList)

@app.route("/addborrower", methods=["GET", "POST"])
def addborrower():
    if request.method == "GET":
        return render_template("addborrower.html")
    else:
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        dob = request.form.get("dob")
        house_number = request.form.get("house_number")
        street = request.form.get("street")
        town = request.form.get("town")
        city = request.form.get("city")
        postal_code = request.form.get("postal_code")

        # Save the borrower information to a database
        cur = getCursor()
        cur.execute("INSERT INTO borrowers (borrowerid, firstname, familyname, dateofbirth,housenumbername,street,town,city,postalcode) VALUES(null,%s,%s,%s,%s,%s,%s,%s,%s);",((str(first_name), str(last_name), dob, str(house_number), str(street), str(town), str(city), str(postal_code),)))
        updatestatus = "Add borrower sucessful"
        session['updatestatus'] = updatestatus
        # Redirect to the borrower detail page
        return redirect("/listborrowers")


@app.route("/borrowerdetail", methods=["GET"])
def borrowerdetail():
    connection = getCursor()
    borrowerid = request.args.get('borrowerid')
    connection.execute("SELECT * FROM borrowers where borrowerid = %s;",(borrowerid,))
    updatestatus = session.get('updatestatus', None)
    borrowerList = connection.fetchall()
    # code to retrieve borrower details and render the template
    return render_template("borrowerdetail.html",borrowerlist=borrowerList,borrowerid=borrowerid, updatestatus=updatestatus)


@app.route("/updateborrower", methods=["POST"])
def updateborrower():
    borrowerid = request.form.get('borrowerid')
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    dob = request.form.get('dob')
    house_number = request.form.get('house_number')
    street = request.form.get('street')
    town = request.form.get('town')
    city = request.form.get('city')
    postal_code = request.form.get('postal_code')

    # Check if none of the fields is missing or empty
    if not first_name and not last_name and not dob and not house_number and not street and not town and not city and not postal_code:
        updatestatus = "At least one field is required. Please fill in the missing fields and try again."
        session['updatestatus'] = updatestatus
        return redirect("/borrowerdetail?borrowerid="+borrowerid)

    # Connect to the database and execute the update query
    connection = getCursor()
    updateborrowersql = "UPDATE borrowers SET firstname = %s, familyname = %s, dateofbirth =%s, housenumbername = %s,street=%s,town= %s,city=%s,postalcode=%s WHERE borrowerid = %s;"
    connection.execute(updateborrowersql, (str(first_name), str(last_name), dob, str(house_number), str(street), str(town), str(city), str(postal_code), borrowerid,))

    # Update status and redirect back to the borrower detail page
    updatestatus = "Updated borrower detail successful, Press Enter to continue."
    session['updatestatus'] = updatestatus
    return redirect("/borrowerdetail?borrowerid="+borrowerid)


@app.route("/returnbook", methods=["GET"])
def returnbook():
    loanid = request.args.get('loanid', None)
    if loanid is None:
        # return an error message or redirect the user to a different page
        return redirect("/error")
    connection = getCursor()
    sql= "UPDATE loans set returned ='1' where loanid =%s;"
    connection.execute(sql,(loanid,))
    return redirect("/currentloans")

@app.route("/staff/listoverduebooks")
def listoverduebooks():
    return redirect("/staff/listoverduebooks.html")

@app.route("/staff/listloansumary")
def listloansumary():
    return redirect("/staff/listloansumary.html")

@app.route("/staff/listborrowersummay")
def listborrowersummay():
    return redirect("/staffroute/listborrowersummay.html")


