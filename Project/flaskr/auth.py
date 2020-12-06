import functools
import re
pttn = re.compile(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")
isEmail = lambda x: pttn.match(x) and True or False
import smtplib
from email.mime.text import MIMEText

from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash

from flaskr.db import get_db

bp = Blueprint("auth", __name__, url_prefix="/auth")

def login_required(view):
    """View decorator that redirects anonymous users to the login page."""

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))

        return view(**kwargs)

    return wrapped_view


@bp.before_app_request
def load_logged_in_user():
    """If a user id is stored in the session, load the user object from
    the database into ``g.user``."""
    user_id = session.get("user_id")

    if user_id is None:
        g.user = None
    else:
        g.user = (
            get_db().execute("SELECT * FROM user WHERE id = ?", (user_id,)).fetchone()
        )


@bp.route("/register", methods=("GET", "POST"))
def register():
    """Register a new user.

    Validates that the username is not already taken. Hashes the
    password for security.
    """
    if request.method == "POST":
        import requests
        username = request.form["username"]
        password = request.form["password"]
        email = request.form["email"]
        db = get_db()
        error = None

        if not username:
            error = "Username is required."
        elif not password:
            error = "Password is required."
        elif not email or not isEmail(email):
            error = "Valid Email is required."
        elif (
            db.execute("SELECT id FROM user WHERE username = ?", (username,)).fetchone()
            is not None
        ):
            error = f"User {username} is already registered."

        if error is None:
            # the name is available, store it in the database and go to
            # the login page
            db.execute(
                "INSERT INTO user (username, password, email) VALUES (?, ?, ?)",
                (username, generate_password_hash(password), email),
            )
            db.commit()
            uid = db.execute("SELECT id FROM user WHERE username = ?", (username,)).fetchone()["id"]
            return redirect(url_for("auth.confirm",id=uid))

        flash(error)

    return render_template("auth/register.html")

@bp.route("/confirm",methods=['GET'])
def confirm():
    """Send the confirmation email to registered user"""
    from random import randint
    token = randint(10000000,99999999)
    uid= request.args.get('id')
    db = get_db()
    user = db.execute(
        "SELECT * FROM user WHERE id = ?", (uid,)
    ).fetchone()
    if user:
        if user["verified"]!=0:
            return "Email already verified."
        r_set = db.execute("UPDATE user SET token = ? WHERE id = ?", (token,uid))
        db.commit()
        if not r_set.rowcount:
            return "update failed"
        smtpserver = smtplib.SMTP('localhost', 8025)
        msg = MIMEText("Confirm Link: "+url_for("auth.verify", id=uid, tk=token, _external=True))
        msg['Subject'] = 'Verification email'
        msg['From'] = 'flaskr-admin@gmail.com'
        msg['To'] = user["email"]
        smtpserver.sendmail(msg['From'], [msg['To']], msg.as_string())
        return "Confirmation sent." # "Confirm Link: "+url_for("auth.verify", id=uid, tk=token, _external=True)
    else:
        return "User Not Found"

@bp.route("/reset",methods=['GET'])
def reset():
    db = get_db()
    from random import randint
    token = randint(10000000,99999999)
    username= request.args.get('usr')
    user = db.execute(
        "SELECT * FROM user WHERE username = ?", (username,)
    ).fetchone()
    if user:
        db.execute("UPDATE user SET token = ? WHERE id = ?", (token,user["id"]))
        db.commit()
        smtpserver = smtplib.SMTP('localhost', 8025)
        msg = MIMEText("Reser Password Link: "+url_for("auth.resetpw", usr=username, tk=token, _external=True))
        msg['Subject'] = 'Password Reset email'
        msg['From'] = 'flaskr-admin@gmail.com'
        msg['To'] = user["email"]
        smtpserver.sendmail(msg['From'], [msg['To']], msg.as_string())
        return "Reset Email Sent." #render_template("auth/resetpw.html",username=username, token=token)
    else:
        return "User Not Found."
    
# TODO Add annotation
@bp.route("/resetpw",methods=['GET', 'POST'])
def resetpw():
    """Reset the user password through email"""
    db = get_db()
    if request.method == 'GET':
        username = request.args.get('usr')
        token = request.args.get('tk')
        user = db.execute(
            "SELECT * FROM user WHERE username = ?", (username,)
        ).fetchone()
        if user:
            return render_template("auth/resetpw.html",username=username, token=token)
        else:
            return "User Not Found."
    else:
        username = request.form["username"]
        token = request.form["token"]
        password = request.form["password"]
        user = db.execute(
            "SELECT * FROM user WHERE username = ?", (username,)
        ).fetchone()
        if user:
            if int(user["token"])==int(token):
                db.execute("UPDATE user SET password = ? WHERE id = ?", (generate_password_hash(password),user["id"]))
                db.commit()
                flash("Password updated")
            else:
                return "Bad credentials."

        else:
            return "User Not Found."

    return redirect(url_for("auth.login"))

@bp.route("/verify",methods=['GET'])
def verify():
    """Verify the confirmation email is valid"""
    if request.method == 'GET':
        uid=request.args.get('id')
        token=request.args.get('tk')
        db = get_db()
        user = db.execute(
            "SELECT * FROM user WHERE id = ?", (uid,)
        ).fetchone()
        ## print(user["token"],type(user["token"]),user["id"],type(user["id"])) #(str, int)
        if int(user["token"])==int(token) and int(user["id"])==int(uid):
            db.execute("UPDATE user SET verified = 1 WHERE id = ?", (uid,))
            db.commit()
            flash("Account Verified")
        else:
            flash("Failed to verify Account")
    return redirect(url_for("auth.login"))

@bp.route("/login", methods=("GET", "POST"))
def login():
    """Log in a registered user by adding the user id to the session."""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        ## email = request.form["email"] # unused
        db = get_db()
        error = None
        user = db.execute(
            "SELECT * FROM user WHERE username = ?", (username,)
        ).fetchone()

        if user is None:
            error = "Incorrect username."
        elif not check_password_hash(user["password"], password):
            error = "Incorrect password."
        elif user["verified"]==0:
            error = "Please verify your email first. Confirmation email is sent to "+user["email"]

        if error is None:
            # store the user id in a new session and return to the index
            session.clear()
            session["user_id"] = user["id"]
            return redirect(url_for("index"))

        flash(error)

    return render_template("auth/login.html")


@bp.route("/logout")
def logout():
    """Clear the current session, including the stored user id."""
    session.clear()
    return redirect(url_for("index"))
