from flask import Flask, render_template, request, redirect, make_response
import pymysql
from dbutils.pooled_db import PooledDB
import base64
import random
import string
import bcrypt
import pdf
import datetime

app = Flask(__name__)

config = {"host": 'localhost',
          "user": 'file_saving',
          "password": 'qP7XafLi',
          "database": 'file_saving',
          "autocommit": "true",
          "cursorclass": pymysql.cursors.DictCursor
          }

database = PooledDB(pymysql, 4, **config)


@app.route("/")
def root_page():
    user_id = check_header(request.headers)
    if not user_id:
        return redirect("/login")
    sql = "SELECT id from notebook where user_id={} ORDER BY title LIMIT 1".format(
        user_id)
    with database.connection().cursor() as cur:
        cur.execute(sql)
        data = cur.fetchone()
    try:
        return redirect("/note/"+data["id"])
    except:
        return redirect("/create")


@app.route("/add", methods=["POST"])
def add_pagedata():
    user_id = check_header(request.headers)
    if not user_id:
        return redirect("/login")
    post_data = request.get_json()
    try:
        sql = "SELECT id from notebook where id='{}' and user_id={}".format(
            post_data["note_id"], user_id)
        with database.connection().cursor() as cur:
            cur.execute(sql)
            record = cur.fetchone()
            note_id = record["id"]

        merge_data = {"image": [], "docs": [], "pdf": []}
        for k, v in post_data.items():
            if k in ["image", "docs", "pdf"]:
                merge_data[k].append(base64.b64decode(v))
        pdf.merge_pdf(note_id+".pdf", merge_data)
        return {"status": True}
    except Exception as e:
        print(e)
        return {"status": False, "msg": "missing information"}


@ app.route("/note/<note_id>")
def note_page(note_id):
    user_id = check_header(request.headers)
    if not user_id:
        return redirect("/login")
    sql = "SELECT title from notebook where id='{}' and user_id={}".format(
        note_id, user_id)
    with database.connection().cursor() as cur:
        cur.execute(sql)
        data = cur.fetchone()
    try:
        title = data["title"]
    except:
        return redirect("/")
    return render_template("index.html", title=title, note_id=note_id, noteArray=get_notelist(user_id))


@ app.route("/data/<note_id>")
def note_data(note_id):
    user_id = check_header(request.headers)
    note_id = note_id.split(".")[0]
    if not user_id:
        return redirect("/login")
    sql = "SELECT id from notebook where id='{}' and user_id={}".format(
        note_id, user_id)
    with database.connection().cursor() as cur:
        cur.execute(sql)
        data = cur.fetchone()
    try:
        id = data["id"]
        with open("data/{}.pdf".format(id), "rb") as f:
            response = make_response(f.read())
        response.headers.set("Content-Type", "application/pdf")
        return response
    except:
        with open("data/dummy.pdf", "rb") as f:
            response = make_response(f.read())
        response.headers.set("Content-Type", "application/pdf")
        return response


@ app.route("/noteinfo")
def get_notelist():
    user_id = check_header(request.headers)
    if not user_id:
        return {"status": False, "msg": "need login"}
    return get_notelist(user_id, request.args.get("offset"))


@app.route("/create",methods=["GET"])
def create_page():
    user_id = check_header(request.headers)
    if not user_id:
        return redirect("/")
    return render_template("create.html")

@ app.route("/create", methods=["POST"])
def create_note():
    data = request.get_json()
    user_id = check_header(request.headers)
    if not user_id:
        return {"status": False, "msg": "need login"}
    note_id = random_name(16)
    sql = "INSERT INTO notebook(id,user_id,title) values('{}',{},'{}')".format(
        note_id, user_id, data["title"])
    with database.connection().cursor() as cur:
        cur.execute(sql)
    return {"status": True, "note_id": note_id}


@ app.route("/remove", methods=["POST"])
def remove_note():
    data = request.get_json()
    user_id = check_header(request.headers)
    if not user_id:
        return {"status": False, "msg": "need login"}
    sql = "DELETE FROM notebook WHERE id='{}' and user_id={}".format(data["note_id"],user_id)
    print(sql,data,user_id)
    with database.connection().cursor() as cur:
        cur.execute(sql)
    return {"status": True}

@app.route("/register",methods=["GET"])
def regist_page():
    user_id = check_header(request.headers)
    if user_id:
        return redirect("/")
    return render_template("register.html")

@ app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    if not (data["address"] and data["pass"]):
        return {"status": False}
    salt = bcrypt.gensalt()
    hash = bcrypt.hashpw(data["pass"].encode(), salt).decode()
    sql = "INSERT INTO user(address,pass) values('{}','{}')".format(
        data["address"], hash)
    with database.connection().cursor() as cur:
        cur.execute(sql)
    return {"status": True}

@app.route("/login",methods=["GET"])
def login_page():
    user_id = check_header(request.headers)
    if user_id:
        return redirect("/")
    return render_template("login.html")

@ app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if not (data["address"] and data["pass"]):
        return {"status": False, "msg": "missing data"}
    sql = "SELECT id,pass from user where address='{}'".format(data["address"])
    with database.connection().cursor() as cur:
        cur.execute(sql)
        try:
            record = cur.fetchone()
            if not bcrypt.checkpw(data["pass"].encode(), record["pass"].encode()):
                return {"status": False, "msg": "user not found"}
        except:
            return {"status": False, "msg": "user not found"}
        token = random_name(24)
        sql = "INSERT INTO token(user_id,token) values('{}','{}')".format(
            record["id"], token)
        cur.execute(sql)
    return {"status": True, "token": token}

@app.route("/export/<note_id>")
def export_pdf(note_id):
    user_id = check_header(request.headers)
    if not user_id:
        return redirect("/login")
    if not note_id:
        return {"status": False, "msg": "missing data"}
    
    if request.args.get("page_num"):
        page_num = list()
        for p in request.args.get("page_num").split(","):
            if "-" in p:
                start,end = p.split("-")
                for i in range(int(start),int(end)+1):
                    page_num.append(i)
            else:
                page_num.append(int(p))
    else:
        return redirect("/data/"+note_id)

    sql = "SELECT id from notebook where user_id={} and id='{}'".format(user_id,note_id)
    with database.connection().cursor() as cur:
        cur.execute(sql)
        note_id = cur.fetchone()["id"]
    if not note_id:
        return {"status": False, "msg": "note not found"}
    try:
        response = make_response(pdf.export_page(note_id+".pdf",*page_num))
        response.headers.set("Content-Type", "application/pdf")
        return response
    except Exception as e: 
        print(e)
        with open("data/dummy.pdf", "rb") as f:
            response = make_response(f.read())
        response.headers.set("Content-Type", "application/pdf")
        return response


@ app.route("/check")
def check_login():
    user_id = check_token(request.headers)
    if user_id:
        return user_id
    return ""

@ app.route("/robots.txt")
def robot():
    return "User-agent: * \nDisallow: /"

@ app.route("/favicon.ico")
def favicon():
    with open("favicon.ico","rb") as f:
        response = make_response(f.read())
        response.headers.set("Content-Type", "image/x-icon")
        return response


def get_notelist(user_id: int, offset: int = 0):
    if not user_id:
        return redirect("/login")
    sql = "SELECT id,title from notebook where user_id={} ORDER BY title LIMIT {},{}".format(
        user_id, offset, offset+300)
    with database.connection().cursor() as cur:
        cur.execute(sql)
        data = cur.fetchall()
    return data


def check_header(header: dict):
    try:
        cookie = cookie_dict(header["Cookie"])
        return check_token(cookie["token"])
    except:
        return False


def check_token(token: str):
    dt = datetime.datetime.today() - datetime.timedelta(days=3)
    with database.connection().cursor() as cur:
        sql = "DELETE FROM token WHERE created_time < '{}';".format(str(dt))
        cur.execute(sql)
        sql = "SELECT user_id from token where token='{}'".format(token)
        cur.execute(sql)
        record = cur.fetchone()
    try:
        return record["user_id"]
    except:
        return False


def cookie_dict(cookie: str):
    items = cookie.split(";")
    result = dict()
    for i in items:
        try:
            k, v = i.split("=")
            result[k.strip()] = v.strip()
        except:
            pass
    return result


def user_search(token: str):
    sql = "SELECT * FROM token where token={}".format(token)
    with database.connection().cursor() as cur:
        cur.execute(sql)
        data = cur.fetchone()
    if data:
        return data["user_id"]
    else:
        return False


def random_name(n: int):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=n))


if __name__ == "__main__":
    app.run(port=9000, debug=True)
