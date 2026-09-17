import os

import numpy as np
import pandas as pd

from ai_ml.preprocessing.preprocess import (
    load_and_preprocess_data,
)

from ai_ml.risk.cost_anomaly import (
    calculate_cost_anomaly,
)

from ai_ml.risk.contractor_risk import (
    calculate_contractor_risk,
)

from ai_ml.risk.text_similarity import (
    calculate_text_similarity,
)

from ai_ml.models.anomaly_detector import (
    detect_anomalies,
)

from ai_ml.models.random_forest import (
    build_controlled_training_data,
    train_random_forest,
    predict_anomaly_probability,
    evaluate_model,
    FEATURE_COLUMNS,
)


# ============================================================
# CONFIGURATION
# ============================================================

OUTPUT_DIR = "ai_ml/data"

RISK_RESULTS_PATH = (
    f"{OUTPUT_DIR}/risk_results.csv"
)

RF_RESULTS_PATH = (
    f"{OUTPUT_DIR}/random_forest_results.csv"
)

RF_METRICS_PATH = (
    f"{OUTPUT_DIR}/rf_metrics.csv"
)

RF_IMPORTANCE_PATH = (
    f"{OUTPUT_DIR}/rf_feature_importance.csv"
)


# Transparent composite-risk weights.
COST_WEIGHT = 0.45
CONTRACTOR_WEIGHT = 0.30
TEXT_WEIGHT = 0.25


# ============================================================
# RISK EXPLANATION
# ============================================================

def generate_risk_explanation(row: pd.Series) -> str:
    """
    Generate a concise, evidence-based explanation of why
    a project received its risk score.
    """

    contributions = {
        "Cost Anomaly": row["cost_contribution"],
        "Contractor Concentration": row[
            "contractor_contribution"
        ],
        "Text Similarity": row[
            "text_similarity_contribution"
        ],
    }

    dominant_signal = max(
        contributions,
        key=contributions.get,
    )

    if dominant_signal == "Cost Anomaly":

        return (
            f"Sanction amount is "
            f"{row['cost_deviation_pct']:.1f}% above "
            f"the {row['peer_baseline']} peer median."
        )

    if dominant_signal == "Contractor Concentration":

        return (
            f"{row['implementing_agency_name']} handles "
            f"{int(row['contractor_project_count'])} of "
            f"{int(row['contractor_peer_count'])} projects "
            f"in the comparison group."
        )

    return (
        f"Project description has "
        f"{row['text_similarity']:.2f} semantic similarity "
        f"with project {row['similar_project_id']}."
    )


# ============================================================
# RANDOM FOREST VALIDATION
# ============================================================

def train_and_validate_random_forest(
    result: pd.DataFrame,
):
    """
    Perform leak-free controlled-anomaly validation.

    Original projects are split first.
    Controlled anomalies are then generated independently
    inside train and test partitions.
    """

    rng = np.random.default_rng(42)

    original_indices = rng.permutation(
        len(result)
    )

    split_index = int(
        len(result) * 0.80
    )

    train_indices = (
        original_indices[:split_index]
    )

    test_indices = (
        original_indices[split_index:]
    )

    train_projects = (
        result.iloc[
            train_indices
        ]
        .reset_index(drop=True)
    )

    test_projects = (
        result.iloc[
            test_indices
        ]
        .reset_index(drop=True)
    )

    # --------------------------------------------------------
    # Generate controlled training/test data
    # --------------------------------------------------------

    X_train, y_train = (
        build_controlled_training_data(
            train_projects,
            random_state=42,
        )
    )

    X_test, y_test = (
        build_controlled_training_data(
            test_projects,
            random_state=123,
        )
    )

    # --------------------------------------------------------
    # Train validation model
    # --------------------------------------------------------

    validation_model = train_random_forest(
        X_train,
        y_train,
    )

    test_predictions = (
        validation_model.predict(
            X_test
        )
    )

    metrics = evaluate_model(
        y_test,
        test_predictions,
    )

    metrics["train_original_projects"] = (
        len(train_projects)
    )

    metrics["test_original_projects"] = (
        len(test_projects)
    )

    metrics["train_samples"] = (
        len(X_train)
    )

    metrics["test_samples"] = (
        len(X_test)
    )

    metrics["trees"] = (
        len(validation_model.estimators_)
    )

    # --------------------------------------------------------
    # Train final model on all available controlled data
    # --------------------------------------------------------

    X_full, y_full = (
        build_controlled_training_data(
            result,
            random_state=42,
        )
    )

    final_model = train_random_forest(
        X_full,
        y_full,
    )

    return (
        final_model,
        metrics,
    )


# ============================================================
# COMPLETE PIPELINE
# ============================================================

def run_pipeline() -> pd.DataFrame:
    """
    Run the complete AI/ML risk-analysis pipeline.
    """

    # --------------------------------------------------------
    # 1. Load real MPLAD data
    # --------------------------------------------------------

    data = load_and_preprocess_data()

    # --------------------------------------------------------
    # 2. Calculate the three transparent risk signals
    # --------------------------------------------------------

    cost = calculate_cost_anomaly(
        data
    )

    contractor = calculate_contractor_risk(
        data
    )

    text = calculate_text_similarity(
        data
    )

    # --------------------------------------------------------
    # 3. Base project information
    # --------------------------------------------------------

    result = data[
        [
            "unique_work_number",
            "state",
            "constituency",
            "mp_name",
            "work_category",
            "work_name",
            "sanction_amount",
            "date_of_administrative_approval",
            "expected_completion_date",
            "implementing_agency_name",
            "work_status",
        ]
    ].copy()

    # --------------------------------------------------------
    # 4. Merge cost analysis
    # --------------------------------------------------------

    result = result.merge(
        cost[
            [
                "unique_work_number",
                "peer_median",
                "peer_count",
                "peer_baseline",
                "cost_deviation_pct",
                "cost_risk",
            ]
        ],
        on="unique_work_number",
        how="left",
    )

    # --------------------------------------------------------
    # 5. Merge contractor analysis
    # --------------------------------------------------------

    result = result.merge(
        contractor[
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

    # --------------------------------------------------------
    # 6. Merge text similarity analysis
    # --------------------------------------------------------

    result = result.merge(
        text[
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

    # --------------------------------------------------------
    # 7. Calculate weighted contributions
    # --------------------------------------------------------

    result["cost_contribution"] = (
        COST_WEIGHT
        * result["cost_risk"]
    )

    result["contractor_contribution"] = (
        CONTRACTOR_WEIGHT
        * result["contractor_risk"]
    )

    result["text_similarity_contribution"] = (
        TEXT_WEIGHT
        * result["text_similarity_risk"]
    )

    # --------------------------------------------------------
    # 8. Transparent final risk score
    # --------------------------------------------------------

    result["risk_score"] = (
        result["cost_contribution"]
        + result["contractor_contribution"]
        + result["text_similarity_contribution"]
    ).clip(0, 100)

    # --------------------------------------------------------
    # 9. Risk bands
    # --------------------------------------------------------

    result["risk_band"] = pd.cut(
        result["risk_score"],
        bins=[
            -1,
            29,
            59,
            79,
            100,
        ],
        labels=[
            "Low",
            "Medium",
            "High",
            "Critical",
        ],
    )

    # --------------------------------------------------------
    # 10. Supporting anomaly baseline
    # --------------------------------------------------------

    result = detect_anomalies(
        result
    )

    # --------------------------------------------------------
    # 11. Risk explanation
    # --------------------------------------------------------

    result["top_risk_signal"] = (
        result[
            [
                "cost_contribution",
                "contractor_contribution",
                "text_similarity_contribution",
            ]
        ]
        .idxmax(axis=1)
        .map(
            {
                "cost_contribution": "Cost Anomaly",
                "contractor_contribution": (
                    "Contractor Concentration"
                ),
                "text_similarity_contribution": (
                    "Text Similarity"
                ),
            }
        )
    )

    result["risk_explanation"] = (
        result.apply(
            generate_risk_explanation,
            axis=1,
        )
    )

    # --------------------------------------------------------
    # 12. Random Forest
    # --------------------------------------------------------

    rf_model, rf_metrics = (
        train_and_validate_random_forest(
            result
        )
    )

    result = predict_anomaly_probability(
        rf_model,
        result,
    )

    # --------------------------------------------------------
    # 13. Rank projects
    # --------------------------------------------------------

    result = (
        result
        .sort_values(
            "risk_score",
            ascending=False,
        )
        .reset_index(drop=True)
    )

    result.insert(
        0,
        "risk_rank",
        range(
            1,
            len(result) + 1,
        ),
    )

    # --------------------------------------------------------
    # 14. Save RF metrics
    # --------------------------------------------------------

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True,
    )

    pd.DataFrame(
        [rf_metrics]
    ).to_csv(
        RF_METRICS_PATH,
        index=False,
    )

    # --------------------------------------------------------
    # 15. Save RF feature importance
    # --------------------------------------------------------

    importance_df = pd.DataFrame(
        {
            "feature": FEATURE_COLUMNS,
            "importance": (
                rf_model.feature_importances_
            ),
        }
    ).sort_values(
        "importance",
        ascending=False,
    )

    importance_df.to_csv(
        RF_IMPORTANCE_PATH,
        index=False,
    )

    # --------------------------------------------------------
    # 16. Save complete project results
    # --------------------------------------------------------

    result.to_csv(
        RISK_RESULTS_PATH,
        index=False,
    )

    return result


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    results = run_pipeline()

    print(
        "========================================"
    )

    print(
        "COMPLETE AI/ML PIPELINE SUCCESSFUL"
    )

    print(
        "========================================"
    )

    print(
        f"Projects analyzed: {len(results)}"
    )

    print(
        f"Results: {RISK_RESULTS_PATH}"
    )

    print(
        f"RF metrics: {RF_METRICS_PATH}"
    )

    print(
        f"RF importance: {RF_IMPORTANCE_PATH}"
    )

    print(
        "\nRisk-band distribution:"
    )

    print(
        results[
            "risk_band"
        ]
        .value_counts()
        .sort_index()
        .to_string()
    )

    print(
        "\nRandom Forest validation:"
    )

    rf_metrics = pd.read_csv(
        RF_METRICS_PATH
    ).iloc[0]

    print(
        f"Accuracy : "
        f"{rf_metrics['accuracy']:.4f}"
    )

    print(
        f"Precision: "
        f"{rf_metrics['precision']:.4f}"
    )

    print(
        f"Recall   : "
        f"{rf_metrics['recall']:.4f}"
    )

    print(
        f"F1 Score : "
        f"{rf_metrics['f1']:.4f}"
    )

    print(
        f"Trees    : "
        f"{int(rf_metrics['trees'])}"
    )

    print(
        "\nTop 10 projects:"
    )

    print(
        results[
            [
                "risk_rank",
                "unique_work_number",
                "work_category",
                "sanction_amount",
                "cost_risk",
                "contractor_risk",
                "text_similarity_risk",
                "risk_score",
                "risk_band",
                "top_risk_signal",
                "anomaly_score",
                "rf_anomaly_probability",
                "rf_anomaly_prediction",
            ]
        ]
        .head(10)
        .to_string(index=False)
    )