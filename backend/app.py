from flask import Flask, jsonify, request
from models import db, Project

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///public_money.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)


@app.route("/")
def home():
    return {"message": "Public Money API is running"}


def project_to_dict(project):
    return {
        # Original project data
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

        # Cost risk
        "peer_median": project.peer_median,
        "peer_count": project.peer_count,
        "peer_baseline": project.peer_baseline,
        "cost_deviation_pct": project.cost_deviation_pct,
        "cost_risk": project.cost_risk,

        # Contractor risk
        "contractor_peer_count": project.contractor_peer_count,
        "contractor_project_count": project.contractor_project_count,
        "contractor_concentration": project.contractor_concentration,
        "contractor_risk": project.contractor_risk,

        # Text similarity
        "similar_project_id": project.similar_project_id,
        "similar_project_name": project.similar_project_name,
        "text_similarity": project.text_similarity,
        "text_similarity_risk": project.text_similarity_risk,

        # Risk contributions
        "cost_contribution": project.cost_contribution,
        "contractor_contribution": project.contractor_contribution,
        "text_similarity_contribution": project.text_similarity_contribution,

        # Final risk
        "risk_score": project.risk_score,
        "risk_band": project.risk_band,

        # Anomaly detection
        "anomaly_score": project.anomaly_score,
        "anomaly_flag": project.anomaly_flag,
        "top_risk_signal": project.top_risk_signal,

        # Explanation
        "risk_explanation": project.risk_explanation,

        # Random Forest
        "rf_anomaly_probability": project.rf_anomaly_probability,
        "rf_anomaly_prediction": project.rf_anomaly_prediction,

        # Ranking
        "risk_rank": project.risk_rank
    }


@app.route("/api/projects")
def get_projects():
    projects = Project.query.all()

    return jsonify([
        project_to_dict(project)
        for project in projects
    ])


@app.route("/api/projects/<int:project_id>")
def get_project(project_id):
    project = Project.query.get_or_404(project_id)

    return jsonify(project_to_dict(project))


@app.route("/api/risk-results", methods=["POST"])
def update_risk_results():
    data = request.get_json()

    if not data or not isinstance(data, list):
        return jsonify({"error": "Expected a list of risk results"}), 400

    updated = 0
    not_found = []

    for result in data:
        work_number = result.get("unique_work_number")

        if not work_number:
            continue

        project = Project.query.filter_by(
            unique_work_number=work_number
        ).first()

        if not project:
            not_found.append(work_number)
            continue

        project.peer_median = result.get("peer_median")
        project.peer_count = result.get("peer_count")
        project.peer_baseline = result.get("peer_baseline")
        project.cost_deviation_pct = result.get("cost_deviation_pct")
        project.cost_risk = result.get("cost_risk")

        project.contractor_peer_count = result.get("contractor_peer_count")
        project.contractor_project_count = result.get("contractor_project_count")
        project.contractor_concentration = result.get("contractor_concentration")
        project.contractor_risk = result.get("contractor_risk")

        project.similar_project_id = result.get("similar_project_id")
        project.similar_project_name = result.get("similar_project_name")
        project.text_similarity = result.get("text_similarity")
        project.text_similarity_risk = result.get("text_similarity_risk")

        project.cost_contribution = result.get("cost_contribution")
        project.contractor_contribution = result.get("contractor_contribution")
        project.text_similarity_contribution = result.get(
            "text_similarity_contribution"
        )

        project.risk_score = result.get("risk_score")
        project.risk_band = result.get("risk_band")

        project.anomaly_score = result.get("anomaly_score")
        project.anomaly_flag = result.get("anomaly_flag")
        project.top_risk_signal = result.get("top_risk_signal")

        project.risk_explanation = result.get("risk_explanation")

        project.rf_anomaly_probability = result.get(
            "rf_anomaly_probability"
        )
        project.rf_anomaly_prediction = result.get(
            "rf_anomaly_prediction"
        )

        project.risk_rank = result.get("risk_rank")

        updated += 1

    db.session.commit()

    return jsonify({
        "message": "Risk results updated successfully",
        "updated": updated,
        "not_found": not_found
    })




if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)