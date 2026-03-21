from flask import Flask, render_template, request, redirect, session, url_for
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from model.users import Users, Post, db
import os
from form import RegisterForm

app = Flask(__name__)

app.config["SECRET_KEY"] = "your_secret_key_here"

# DATABASE CONFIG
db_url = os.environ.get("DATABASE_URL")

if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# INIT DB
db.init_app(app)

# LOGIN MANAGER
loginmanager = LoginManager()
loginmanager.init_app(app)
loginmanager.login_view = "login"


@loginmanager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))


# CREATE TABLES
with app.app_context():
    db.create_all()


# ------------------ ROUTES ------------------ #

@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data

        user = Users(username=username, email=email)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        return render_template("login.html", message="Registration successful! Please log in.")

    return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = Users.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("dashboard", user_id=user.id))

        return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")


@app.route("/dashboard/<int:user_id>")
@login_required
def dashboard(user_id):
    posts = Post.query.order_by(Post.created_at.desc()).all()

    return render_template(
        "dashboard.html",
        user_id=user_id,
        current_user=current_user.username,
        posts=posts
    )


@app.route("/create_post", methods=["GET", "POST"])
@login_required
def create_post():
    if request.method == "POST":
        content = request.form.get("content")

        new_post = Post(
            content=content,
            user_id=current_user.id
        )

        db.session.add(new_post)
        db.session.commit()

        return redirect(url_for("dashboard", user_id=current_user.id))

    return render_template("create_post.html")


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return redirect("/login")


@app.route("/delete_account/<int:user_id>", methods=["GET", "POST"])
@login_required
def delete_account(user_id):
    user = Users.query.get(user_id)

    if user:
        db.session.delete(user)
        db.session.commit()

    session.pop("user_id", None)
    return redirect("/login")


@app.route("/update_email/<int:user_id>", methods=["GET", "POST"])
@login_required
def update_email(user_id):
    user = Users.query.get(user_id)

    if request.method == "POST":
        new_email = request.form.get("new_email")

        if user:
            user.email = new_email
            db.session.commit()
            return redirect(url_for("dashboard", user_id=user_id))

    return render_template("update_email.html", user=user)


@app.route("/fetch_all")
@login_required
def fetch_all():
    users = Users.query.all()
    return render_template("fetch_all_users.html", users=users)


# ------------------ RUN ------------------ #

if __name__ == "__main__":
    app.run(debug=True)