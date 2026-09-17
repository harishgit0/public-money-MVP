from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)

    # Original project information
    unique_work_number = db.Column(db.String(100), unique=True, nullable=False)
    state = db.Column(db.String(100))
    constituency = db.Column(db.String(100))
    mp_name = db.Column(db.String(200))
    work_category = db.Column(db.String(200))
    work_name = db.Column(db.Text)
    sanction_amount = db.Column(db.Float)

    date_of_administrative_approval = db.Column(db.String(50))
    expected_completion_date = db.Column(db.String(50))

    implementing_agency_name = db.Column(db.String(300))
    work_status = db.Column(db.String(100))

    # AI-generated risk signals
    cost_anomaly = db.Column(db.Float)
    agency_concentration = db.Column(db.Float)
    text_similarity = db.Column(db.Float)

    # Final risk result
    risk_score = db.Column(db.Float)
    risk_level = db.Column(db.String(20))
    reasons = db.Column(db.Text)