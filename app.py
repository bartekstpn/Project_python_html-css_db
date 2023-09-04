from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import random
import requests

app = Flask(__name__)

with app.app_context():
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
    app.config["SECRET_KEY"] = "your_secret_key"

    db = SQLAlchemy(app)
    login_manager = LoginManager(app)
    login_manager.login_view = "login"

    class User(UserMixin, db.Model):
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(80), unique=True, nullable=False)
        password = db.Column(db.String(80), nullable=False)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    class MealHistory(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
        recipe = db.Column(db.String(255), nullable=False)
        chosen_diet = db.Column(db.String(20))
        ingredients_to_avoid = db.Column(db.String(255))
        comment = db.Column(db.String(255))

    db.create_all()

@app.route("/")
def index():
    return render_template("index.html")

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            return redirect(url_for("index"))
        else:
            flash("Błąd logowania. Spróbuj ponownie.", "danger")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.route("/generate", methods=["POST"])
@login_required
def generate():
    chosen_diet = request.form.get("diet")
    ingredients_to_avoid = request.form.get("ingredients")
    comment = request.form.get("comment")

    api_key = "7d08c6af87b94189b075a163b39e9c18"
    endpoint = f"https://api.spoonacular.com/recipes/random?number=3&apiKey={api_key}"
    response = requests.get(endpoint)
    if response.status_code == 200:
        data = response.json()
        random_recipe = data["recipes"][0]["title"]
    else:
        random_recipe = "Nie udało się pobrać przepisu"

    meal_history = MealHistory(
        user_id=current_user.id,
        recipe=random_recipe,
        chosen_diet=chosen_diet,
        ingredients_to_avoid=ingredients_to_avoid,
        comment=comment
    )

    db.session.add(meal_history)
    db.session.commit()

    return render_template("result.html", recipe=random_recipe)

@app.route("/history")
@login_required
def history():
    history_data = MealHistory.query.filter_by(user_id=current_user.id).all()
    return render_template("history.html", history_data=history_data)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Użytkownik o podanej nazwie już istnieje. Wybierz inną nazwę.", "danger")
        else:
            new_user = User(username=username, password=password)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for("login"))

    return render_template("registration.html")

if __name__ == "__main__":
    app.run(debug=True)