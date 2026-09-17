import os

import pandas as pd

from ai_ml.preprocessing.preprocess import load_and_preprocess_data
from ai_ml.risk.cost_anomaly import calculate_cost_anomaly
from ai_ml.risk.contractor_risk import calculate_contractor_risk
from ai_ml.risk.text_similarity import calculate_text_similarity


OUTPUT_PATH = "ai_ml/data/validation_results.csv"


def composite_score(cost, contractor, text):
    return (
        0.45 * cost
        + 0.30 * contractor
        + 0.25 * text
    )


def validate():
    data = load_and_preprocess_data()

    # Baseline signals
    cost_base = calculate_cost_anomaly(data)
    contractor_base = calculate_contractor_risk(data)
    text_base = calculate_text_similarity(data)

    baseline = data[
        ["unique_work_number", "work_name", "implementing_agency_name"]
    ].copy()

    baseline = baseline.merge(
        cost_base[
            ["unique_work_number", "cost_risk"]
        ],
        on="unique_work_number",
    )

    baseline = baseline.merge(
        contractor_base[
            ["unique_work_number", "contractor_risk"]
        ],
        on="unique_work_number",
    )

    baseline = baseline.merge(
        text_base[
            ["unique_work_number", "text_similarity_risk"]
        ],
        on="unique_work_number",
    )

    baseline["risk_score"] = composite_score(
        baseline["cost_risk"],
        baseline["contractor_risk"],
        baseline["text_similarity_risk"],
    )

    results = []

    # ---------------------------------------------------------
    # CONTROL 1: Planted cost anomaly
    # ---------------------------------------------------------
    cost_candidates = cost_base[
        (cost_base["peer_count"] >= 5)
        & (cost_base["cost_risk"] <= 5)
    ]

    if len(cost_candidates) == 0:
        raise RuntimeError("No suitable cost control project found.")

    cost_target = cost_candidates.iloc[0]
    cost_id = cost_target["unique_work_number"]

    cost_control_data = data.copy()

    cost_mask = (
        cost_control_data["unique_work_number"] == cost_id
    )

    original_cost = float(
        cost_control_data.loc[
            cost_mask, "sanction_amount"
        ].iloc[0]
    )

    # Deliberately make the project unusually expensive.
    cost_control_data.loc[
        cost_mask, "sanction_amount"
    ] = original_cost * 4

    cost_control = calculate_cost_anomaly(
        cost_control_data
    )

    original = baseline[
        baseline["unique_work_number"] == cost_id
    ].iloc[0]

    controlled = cost_control[
        cost_control["unique_work_number"] == cost_id
    ].iloc[0]

    control_score = composite_score(
        controlled["cost_risk"],
        original["contractor_risk"],
        original["text_similarity_risk"],
    )

    results.append(
        {
            "control": "Cost anomaly",
            "project_id": cost_id,
            "baseline_score": original["risk_score"],
            "controlled_score": control_score,
            "baseline_signal": original["cost_risk"],
            "controlled_signal": controlled["cost_risk"],
            "expected": "Risk should increase",
        }
    )

    # ---------------------------------------------------------
    # CONTROL 2: Planted text duplicate
    # ---------------------------------------------------------
    text_candidates = baseline[
        baseline["risk_score"] < baseline["risk_score"].median()
    ]

    text_target = text_candidates.iloc[0]
    text_id = text_target["unique_work_number"]

    reference = data[
        data["unique_work_number"] != text_id
    ].iloc[0]

    text_control_data = data.copy()

    text_mask = (
        text_control_data["unique_work_number"] == text_id
    )

    text_control_data.loc[
        text_mask, "work_name"
    ] = reference["work_name"]

    text_control = calculate_text_similarity(
        text_control_data
    )

    original = baseline[
        baseline["unique_work_number"] == text_id
    ].iloc[0]

    controlled = text_control[
        text_control["unique_work_number"] == text_id
    ].iloc[0]

    control_score = composite_score(
        original["cost_risk"],
        original["contractor_risk"],
        controlled["text_similarity_risk"],
    )

    results.append(
        {
            "control": "Text duplicate",
            "project_id": text_id,
            "baseline_score": original["risk_score"],
            "controlled_score": control_score,
            "baseline_signal": original["text_similarity_risk"],
            "controlled_signal": controlled["text_similarity_risk"],
            "expected": "Risk should increase",
        }
    )

    # ---------------------------------------------------------
    # CONTROL 3: Planted contractor concentration
    # ---------------------------------------------------------
    group_sizes = (
        data.groupby("peer_group")
        .size()
        .sort_values(ascending=False)
    )

    suitable_groups = group_sizes[
        group_sizes >= 6
    ]

    if len(suitable_groups) == 0:
        raise RuntimeError(
            "No suitable contractor control group found."
        )

    selected_group = suitable_groups.index[0]

    group_mask = (
        data["peer_group"] == selected_group
    )

    group_data = data[group_mask]

    agency_counts = (
        group_data["implementing_agency_name"]
        .value_counts()
    )

    dominant_agency = agency_counts.index[0]

    target_candidates = group_data[
        group_data["implementing_agency_name"]
        != dominant_agency
    ]

    if len(target_candidates) == 0:
        raise RuntimeError(
            "Selected contractor group already has one agency only."
        )

    contractor_target = target_candidates.iloc[0]
    contractor_id = contractor_target[
        "unique_work_number"
    ]

    contractor_control_data = data.copy()

    # Deliberately concentrate every project in the peer group
    # under one agency.
    contractor_control_data.loc[
        contractor_control_data["peer_group"]
        == selected_group,
        "implementing_agency_name",
    ] = dominant_agency

    contractor_control = calculate_contractor_risk(
        contractor_control_data
    )

    original = baseline[
        baseline["unique_work_number"] == contractor_id
    ].iloc[0]

    controlled = contractor_control[
        contractor_control["unique_work_number"]
        == contractor_id
    ].iloc[0]

    control_score = composite_score(
        original["cost_risk"],
        controlled["contractor_risk"],
        original["text_similarity_risk"],
    )

    results.append(
        {
            "control": "Contractor concentration",
            "project_id": contractor_id,
            "baseline_score": original["risk_score"],
            "controlled_score": control_score,
            "baseline_signal": original["contractor_risk"],
            "controlled_signal": controlled["contractor_risk"],
            "expected": "Risk should increase",
        }
    )

    validation = pd.DataFrame(results)

    os.makedirs(
        os.path.dirname(OUTPUT_PATH),
        exist_ok=True,
    )

    validation.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print("Controlled-anomaly validation successful")
    print()
    print(
        validation.to_string(index=False)
    )
    print()
    print("Output:", OUTPUT_PATH)


if __name__ == "__main__":
    validate()