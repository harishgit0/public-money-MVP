from flask import Flask, jsonify
from models import db, Project

app = Flask(__name__)

# SQLite database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///public_money.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)


@app.route("/")
def home():
    return {"message": "Public Money API is running"}


@app.route("/api/projects")
def get_projects():
    projects = Project.query.all()

    return jsonify([
        {
            "id": project.id,
            "unique_work_number": project.unique_work_number,
            "state": project.state,
            "constituency": project.constituency,
            "mp_name": project.mp_name,
            "work_category": project.work_category,
            "work_name": project.work_name,
            "sanction_amount": project.sanction_amount,
            "date_of_administrative_approval": project.date_of_administrative_approval,
            "expected_completion_date": project.expected_completion_date,
            "implementing_agency_name": project.implementing_agency_name,
            "work_status": project.work_status,
            "cost_anomaly": project.cost_anomaly,
            "agency_concentration": project.agency_concentration,
            "text_similarity": project.text_similarity,
            "risk_score": project.risk_score,
            "risk_level": project.risk_level,
            "reasons": project.reasons
        }
        for project in projects
    ])

@app.route("/api/projects/<int:project_id>")
def get_project(project_id):
    project = Project.query.get_or_404(project_id)

    return jsonify({
        "id": project.id,
        "unique_work_number": project.unique_work_number,
        "state": project.state,
        "constituency": project.constituency,
        "mp_name": project.mp_name,
        "work_category": project.work_category,
        "work_name": project.work_name,
        "sanction_amount": project.sanction_amount,
        "date_of_administrative_approval": project.date_of_administrative_approval,
        "expected_completion_date": project.expected_completion_date,
        "implementing_agency_name": project.implementing_agency_name,
        "work_status": project.work_status,
        "cost_anomaly": project.cost_anomaly,
        "agency_concentration": project.agency_concentration,
        "text_similarity": project.text_similarity,
        "risk_score": project.risk_score,
        "risk_level": project.risk_level,
        "reasons": project.reasons
    })

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)