import numpy as np
import pandas as pd


FEATURE_COLUMNS = [
    "cost_deviation_pct",
    "contractor_concentration",
    "text_similarity",
]


def detect_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate a lightweight multivariate anomaly baseline.

    This fallback does not require scikit-learn/SciPy and is intended
    for environments where compiled ML libraries are unavailable.
    """

    result = df.copy()

    features = result[FEATURE_COLUMNS].copy()

    # Robust normalization using median and MAD.
    medians = features.median()
    mad = (features - medians).abs().median()

    # Prevent division by zero for constant features.
    mad = mad.replace(0, 1)

    robust_z = (features - medians).abs() / mad

    # Average deviation across the three signals.
    anomaly_strength = robust_z.mean(axis=1)

    # Convert relative anomaly strength to 0–100.
    result["anomaly_score"] = (
        anomaly_strength.rank(method="average", pct=True) * 100
    )

    result["anomaly_flag"] = result["anomaly_score"] >= 90

    return result


if __name__ == "__main__":
    from ai_ml.preprocessing.preprocess import load_and_preprocess_data
    from ai_ml.risk.cost_anomaly import calculate_cost_anomaly
    from ai_ml.risk.contractor_risk import calculate_contractor_risk
    from ai_ml.risk.text_similarity import calculate_text_similarity

    data = load_and_preprocess_data()

    result = calculate_cost_anomaly(data)

    contractor = calculate_contractor_risk(data)
    result = result.merge(
        contractor[
            [
                "unique_work_number",
                "contractor_concentration",
            ]
        ],
        on="unique_work_number",
        how="left",
    )

    text = calculate_text_similarity(data)
    result = result.merge(
        text[
            [
                "unique_work_number",
                "text_similarity",
            ]
        ],
        on="unique_work_number",
        how="left",
    )

    result = detect_anomalies(result)

    print("Anomaly baseline successful")
    print("Projects:", len(result))

    print("\nTop 10 anomalies:")
    print(
        result[
            [
                "unique_work_number",
                "cost_deviation_pct",
                "contractor_concentration",
                "text_similarity",
                "anomaly_score",
                "anomaly_flag",
            ]
        ]
        .sort_values("anomaly_score", ascending=False)
        .head(10)
        .to_string(index=False)
    )

    print("\nFlagged projects:", int(result["anomaly_flag"].sum()))