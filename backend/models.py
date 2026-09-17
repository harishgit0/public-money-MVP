from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)

    # Original project data
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

    # Cost risk
    peer_median = db.Column(db.Float)
    peer_count = db.Column(db.Integer)
    peer_baseline = db.Column(db.String(200))
    cost_deviation_pct = db.Column(db.Float)
    cost_risk = db.Column(db.Float)

    # Contractor risk
    contractor_peer_count = db.Column(db.Integer)
    contractor_project_count = db.Column(db.Integer)
    contractor_concentration = db.Column(db.Float)
    contractor_risk = db.Column(db.Float)

    # Text similarity
    similar_project_id = db.Column(db.String(100))
    similar_project_name = db.Column(db.Text)
    text_similarity = db.Column(db.Float)
    text_similarity_risk = db.Column(db.Float)

    # Risk score contributions
    cost_contribution = db.Column(db.Float)
    contractor_contribution = db.Column(db.Float)
    text_similarity_contribution = db.Column(db.Float)

    # Final risk
    risk_score = db.Column(db.Float)
    risk_band = db.Column(db.String(20))

    # Anomaly detection
    anomaly_score = db.Column(db.Float)
    anomaly_flag = db.Column(db.Boolean)
    top_risk_signal = db.Column(db.String(100))

    # Explanation
    risk_explanation = db.Column(db.Text)

    # Random Forest
    rf_anomaly_probability = db.Column(db.Float)
    rf_anomaly_prediction = db.Column(db.Integer)

    # Ranking
    risk_rank = db.Column(db.Integer)