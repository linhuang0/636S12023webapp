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

app = Flask(__name__)

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
    return render_template("base.html")

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

@app.route("/loanbook")
def loanbook():
    todaydate = datetime.now().date()
    connection = getCursor()
    connection.execute("SELECT * FROM borrowers;")
    borrowerList = connection.fetchall()
    sql = """SELECT * FROM bookcopies
inner join books on books.bookid = bookcopies.bookid
 WHERE bookcopyid not in (SELECT bookcopyid from loans where returned <> 1 or returned is NULL);"""
    connection.execute(sql)
    bookList = connection.fetchall()
    return render_template("addloan.html", loandate = todaydate,borrowers = borrowerList, books= bookList)

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
                b.category, b.yearofpublication, bc.format 
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
   
@app.route("/route/search", methods=["POST"])
def publicsearch():
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

@app.route("/staff/search", methods=["POST"])
def staffsearch():
    return render_template("staffroute")

@app.route("/staff/addborrower", methods=["POST"])
def addborrower():
    return redirect("/staff")

@app.route("/staff/editborrower", methods=["POST"])
def editborrower():
    return redirect("/staff")

@app.route("/staff/issuebooks", methods=["POST"])
def issuebooks():
    return redirect("/staff")

@app.route("/staff/returnbooks", methods=["POST"])
def returnbooks():
    return redirect("/staff")

@app.route("/staff/listoverduebooks")
def listoverduebooks():
    return redirect("/staff/listoverduebooks.html")

@app.route("/staff/listloansumary")
def listloansumary():
    return redirect("/staff/listloansumary.html")

@app.route("/staff/listborrowersummay")
def listborrowersummay():
    return redirect("/staffroute/listborrowersummay.html")
