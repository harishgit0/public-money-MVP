import os
import sys
import pandas as pd

# Allow importing models.py from backend/
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import db, Project


RISK_RESULTS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "ai_ml",
    "data",
    "risk_results.csv"
)


def update_risk_results():
    if not os.path.exists(RISK_RESULTS_PATH):
        print(f"ERROR: Risk results file not found:")
        print(RISK_RESULTS_PATH)
        return

    df = pd.read_csv(RISK_RESULTS_PATH)

    print(f"Risk results loaded: {len(df)}")

    updated = 0
    not_found = 0

    with app.app_context():

        for _, result in df.iterrows():

            work_number = result.get("unique_work_number")

            if pd.isna(work_number):
                continue

            project = Project.query.filter_by(
                unique_work_number=str(work_number)
            ).first()

            if not project:
                not_found += 1
                continue

            # Cost risk
            project.peer_median = result.get("peer_median")
            project.peer_count = result.get("peer_count")
            project.peer_baseline = result.get("peer_baseline")
            project.cost_deviation_pct = result.get("cost_deviation_pct")
            project.cost_risk = result.get("cost_risk")

            # Contractor / agency concentration
            project.contractor_peer_count = result.get(
                "contractor_peer_count"
            )
            project.contractor_project_count = result.get(
                "contractor_project_count"
            )
            project.contractor_concentration = result.get(
                "contractor_concentration"
            )
            project.contractor_risk = result.get(
                "contractor_risk"
            )

            # Text similarity
            project.similar_project_id = result.get(
                "similar_project_id"
            )
            project.similar_project_name = result.get(
                "similar_project_name"
            )
            project.text_similarity = result.get(
                "text_similarity"
            )
            project.text_similarity_risk = result.get(
                "text_similarity_risk"
            )

            # Risk contributions
            project.cost_contribution = result.get(
                "cost_contribution"
            )
            project.contractor_contribution = result.get(
                "contractor_contribution"
            )
            project.text_similarity_contribution = result.get(
                "text_similarity_contribution"
            )

            # Final risk
            project.risk_score = result.get("risk_score")
            project.risk_band = result.get("risk_band")

            # Anomaly detection
            project.anomaly_score = result.get("anomaly_score")
            project.anomaly_flag = result.get("anomaly_flag")
            project.top_risk_signal = result.get(
                "top_risk_signal"
            )

            # Explanation
            project.risk_explanation = result.get(
                "risk_explanation"
            )

            # Random Forest
            project.rf_anomaly_probability = result.get(
                "rf_anomaly_probability"
            )
            project.rf_anomaly_prediction = result.get(
                "rf_anomaly_prediction"
            )

            # Rank
            project.risk_rank = result.get("risk_rank")

            updated += 1

        db.session.commit()

    print(f"Projects updated: {updated}")
    print(f"Not found: {not_found}")
    print("Risk results successfully stored in database.")


if __name__ == "__main__":
    update_risk_results()