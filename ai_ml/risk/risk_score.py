import pandas as pd

from ai_ml.preprocessing.preprocess import load_and_preprocess_data
from ai_ml.risk.cost_anomaly import calculate_cost_anomaly
from ai_ml.risk.contractor_risk import calculate_contractor_risk
from ai_ml.risk.text_similarity import calculate_text_similarity


COST_WEIGHT = 0.45
CONTRACTOR_WEIGHT = 0.30
TEXT_WEIGHT = 0.25


def calculate_risk_score() -> pd.DataFrame:
    """Calculate the explainable composite risk score for every project."""

    base_df = load_and_preprocess_data()

    cost_df = calculate_cost_anomaly(base_df)
    contractor_df = calculate_contractor_risk(base_df)
    text_df = calculate_text_similarity(base_df)

    result = base_df[
        [
            "unique_work_number",
            "state",
            "constituency",
            "mp_name",
            "work_category",
            "work_name",
            "sanction_amount",
            "implementing_agency_name",
            "work_status",
        ]
    ].copy()

    # Merge the three independent risk signals.
    result = result.merge(
        cost_df[
            [
                "unique_work_number",
                "peer_median",
                "peer_count",
                "cost_deviation_pct",
                "cost_risk",
            ]
        ],
        on="unique_work_number",
        how="left",
    )

    result = result.merge(
        contractor_df[
            [
                "unique_work_number",
                "contractor_peer_count",
                "contractor_project_count",
                "contractor_concentration",
                "contractor_risk",
            ]
        ],
        on="unique_work_number",
        how="left",
    )

    result = result.merge(
        text_df[
            [
                "unique_work_number",
                "similar_project_id",
                "similar_project_name",
                "text_similarity",
                "text_similarity_risk",
            ]
        ],
        on="unique_work_number",
        how="left",
    )

    # Explainable composite score.
    result["risk_score"] = (
        COST_WEIGHT * result["cost_risk"]
        + CONTRACTOR_WEIGHT * result["contractor_risk"]
        + TEXT_WEIGHT * result["text_similarity_risk"]
    )

    result["risk_score"] = result["risk_score"].clip(0, 100)

    # Risk band.
    result["risk_band"] = pd.cut(
        result["risk_score"],
        bins=[-1, 29, 59, 79, 100],
        labels=["Low", "Medium", "High", "Critical"],
    )

    return result.sort_values(
        "risk_score",
        ascending=False,
    ).reset_index(drop=True)


if __name__ == "__main__":
    result = calculate_risk_score()

    print("Composite risk analysis successful")
    print("Projects:", len(result))

    print("\nTop 10 projects by final risk score:")
    print(
        result[
            [
                "unique_work_number",
                "work_category",
                "sanction_amount",
                "cost_risk",
                "contractor_risk",
                "text_similarity_risk",
                "risk_score",
                "risk_band",
            ]
        ]
        .head(10)
        .to_string(index=False)
    )

    print("\nRisk-band distribution:")
    print(result["risk_band"].value_counts().sort_index())