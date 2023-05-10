import os
import random
import re
from flask_session import Session
from flask import Flask, redirect, render_template, request, session
from functools import wraps
import json
import sqlite3

app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = True
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Initialize static variables
with open("config.json", "r") as f:
    DATABASES = json.load(f)["databases"]


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


def login_required(f):
    """https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    uid = session["user_id"]  # abbreviation
    if request.method == "POST":
        if request.form.get("action") == "undo":
            # get previous index from history stack
            undo_idx = session["history"].pop()

            # add current index back to pool
            session["pool"].append(request.form.get("idx"))

            # redirect directly since NA posts aren't in annotated database
            if len(session["na"]) != 0:
                if undo_idx == session["na"][-1]:
                    session["na"].pop()
                    session["pool"].append(undo_idx)
                    with open(f"data/user/{uid}/user_data.json", "w") as f:
                        user_data_dict = {
                            "history": session["history"],
                            "pool": session["pool"],
                            "na": session["na"],
                        }
                        json.dump(user_data_dict, f)
                    return redirect("/")

            # add item back to list of unseen data
            annotated_conn = sqlite3.connect(f"data/user/{uid}/annotations.db")
            with annotated_conn:
                annotated_cur = annotated_conn.cursor()
                dropped_post = tuple(
                    annotated_cur.execute(f"SELECT * FROM posts WHERE id={undo_idx};")
                )[0]
                annotated_cur.execute(f"DELETE FROM posts WHERE id={undo_idx}")

                annotated_conn.commit()
            session["pool"].append(undo_idx)

            # update user JSON on disk
            with open(f"data/user/{uid}/user_data.json", "w") as f:
                user_data_dict = {
                    "history": session["history"],
                    "pool": session["pool"],
                    "na": session["na"],
                }
                json.dump(user_data_dict, f)

        elif request.form.get("action") == "na":
            session["history"].append(request.form.get("idx"))
            session["na"].append(request.form.get("idx"))
            with open(f"data/user/{uid}/user_data.json", "w") as f:
                user_data_dict = {
                    "history": session["history"],
                    "pool": session["pool"],
                    "na": session["na"],
                }
                json.dump(user_data_dict, f)
        else:  # add annotation to annotated database
            # conditional check to ensure that answers are within range
            for i in request.form.items():
                if i[0] not in [
                    "idx",
                    "ppn",
                    "ppp",
                    "agg",
                    "fat",
                    "rat",
                    "gdi",
                    "edi",
                    "sir",
                ]:
                    if i[1] not in ["0", "1"]:
                        print("ERROR 1")
                        print(i)
                        return redirect("/")
                elif i[0] not in ["idx", "ppn", "ppp", "agg", "gid", "edi", "sir"]:
                    if i[1] not in ["0", "1", "2", "3"]:
                        print("ERROR 2")
                        print(i)
                        return redirect("/")
                elif i[0] not in ["idx", "ppn", "ppp"]:
                    if i[1] not in ["0", "1", "2"]:
                        print("ERROR 3")
                        print(i)
                        return redirect("/")
                elif i[0] not in ["idx"]:
                    if i[1] not in [str(x) for x in range(8)]:
                        print("ERROR 4")
                        print(i)
                        return redirect("/")

            # define variables from post request
            idx = int(request.form.get("idx"))
            party_politics_positive = int(request.form.get("ppp"))
            party_politics_negative = int(request.form.get("ppn"))
            aggressiveness = int(request.form.get("agg"))
            hatred = int(request.form.get("htr"))
            threat = int(request.form.get("thr"))
            male_preference = int(request.form.get("mpr"))
            female_preference = int(request.form.get("fpr"))
            gender_equality_preference = int(request.form.get("geq"))
            foreigner_attitude = int(request.form.get("fat"))
            religion_attitude = int(request.form.get("rat"))
            gender_disadvantage = int(request.form.get("gdi"))
            ethnicity_disadvantage = int(request.form.get("edi"))
            us_vs_them = int(request.form.get("ust"))
            sarcasm_irony = int(request.form.get("sir"))

            conn = sqlite3.connect(DATABASES[uid])
            annotated_conn = sqlite3.connect(f"data/user/{uid}/annotations.db")
            with conn, annotated_conn:
                cur, annotated_cur = conn.cursor(), annotated_conn.cursor()
                _, forum, url, text = tuple(
                    cur.execute(f"SELECT * FROM posts WHERE id={idx};")
                )[0]
                annotated_cur.execute(
                    "INSERT INTO posts VALUES"
                    "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
                    (
                        idx,
                        forum,
                        url,
                        text,
                        party_politics_positive,
                        party_politics_negative,
                        aggressiveness,
                        hatred,
                        threat,
                        male_preference,
                        female_preference,
                        gender_equality_preference,
                        foreigner_attitude,
                        religion_attitude,
                        gender_disadvantage,
                        ethnicity_disadvantage,
                        us_vs_them,
                        sarcasm_irony,
                    ),
                )

                annotated_conn.commit()
                conn.commit()

            session["history"].append(idx)

            # update user JSON
            with open(f"data/user/{uid}/user_data.json", "w") as f:
                user_data_dict = {
                    "history": session["history"],
                    "pool": session["pool"],
                    "na": session["na"],
                }
                json.dump(user_data_dict, f)
        return redirect("/")

    else:  # i.e. if GET request, login etc
        # If new user: initialize user directory and history variable
        if not os.path.exists(f"data/user/{uid}"):
            os.mkdir(f"data/user/{uid}")

            # initialize empty lists
            session["history"] = []
            session["na"] = []

            conn = sqlite3.connect(DATABASES[uid])
            annotated_conn = sqlite3.connect(f"data/user/{uid}/annotations.db")

            with conn, annotated_conn:
                cur, annotated_cur = conn.cursor(), annotated_conn.cursor()

                # get list of all ids in original database
                session["pool"] = list(reversed(
                    [x[0] for x in cur.execute("SELECT * FROM posts;")]
                ))

                # create annotation database
                annotated_cur.execute(
                    "CREATE TABLE posts("
                    "id INTEGER UNIQUE PRIMARY KEY,"
                    "forum TEXT,"
                    "url TEXT,"
                    "text TEXT,"
                    "party_politics_positive INTEGER,"
                    "party_politics_negative INTEGER,"
                    "aggressiveness INTEGER,"
                    "hatred INTEGER,"
                    "threat INTEGER,"
                    "male_preference INTEGER,"
                    "female_preference INTEGER,"
                    "gender_equality_preference INTEGER,"
                    "foreigner_attitude INTEGER,"
                    "religion_attitude INTEGER,"
                    "gender_disadvantage INTEGER,"
                    "ethnicity_disadvantage INTEGER,"
                    "us_vs_them INTEGER,"
                    "sarcasm_irony INTEGER"
                    ");"
                )
                annotated_conn.commit()

            # create user JSON
            with open(f"data/user/{uid}/user_data.json", "w") as f:
                user_data_dict = {
                    "history": session["history"],
                    "pool": session["pool"],
                    "na": session["na"],
                }
                json.dump(user_data_dict, f)
        else:
            # load user JSON
            with open(f"data/user/{uid}/user_data.json", "r") as f:
                user_data_dict = json.load(f)
                session["history"] = user_data_dict["history"]
                session["pool"] = user_data_dict["pool"]
                session["na"] = user_data_dict["na"]

        # if pool is empty annotation is finished
        if not session["pool"]:
            return render_template("finished.html")
        else:
            # this is necessary in case the user refreshes the page
            with open(f"data/user/{uid}/user_data.json", "r") as f:
                session["pool"] = json.load(f)["pool"]
            idx = session["pool"].pop()
            conn = sqlite3.connect(DATABASES[uid])
            with conn:
                cur = conn.cursor()
                post = tuple(cur.execute(f"SELECT * FROM posts WHERE id={idx};"))[0]
            return render_template(
                "index.html",
                post=post[3],
                url=post[2],
                forum=post[1],
                history=session["history"],
                idx=idx,
                current_post=len(session["history"]) + 1,
                total_length=len(session["pool"]) + len(session["history"]) + 1,
                user_id=uid,
            )


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # Check user-compliance with username guidelines
        username = request.form.get("username")
        if not username:
            return render_template("login.html", failure=True)
        elif " " in username:
            return render_template("login.html", failure=True)
        elif re.search(r"[^a-z]", username):
            return render_template("login.html", failure=True)
        else:
            session["user_id"] = username
            return redirect("/")
    return render_template("login.html", failure=False)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/failure")
def failure():
    return render_template("failure.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0")
