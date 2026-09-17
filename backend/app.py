from flask import Flask
from models import db

app = Flask(__name__)

# SQLite database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///public_money.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Connect SQLAlchemy with Flask
db.init_app(app)


@app.route("/")
def home():
    return {"message": "Public Money API is running"}


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)