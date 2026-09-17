import numpy as np
import pandas as pd

from ai_ml.preprocessing.preprocess import load_and_preprocess_data


def calculate_cost_anomaly(
    df: pd.DataFrame,
    min_peer_size: int = 5,
) -> pd.DataFrame:
    """
    Calculate cost anomaly risk for each project.

    Primary baseline:
        constituency + work_category

    Fallback baseline:
        state + work_category
        when the primary peer group has fewer than min_peer_size projects.
    """

    df = df.copy()

    # Primary peer baseline
    primary_group = df.groupby("peer_group")["sanction_amount"]

    primary_median = primary_group.transform("median")
    primary_count = primary_group.transform("count")

    # Fallback baseline
    fallback_group = df.groupby(
        ["state", "work_category"]
    )["sanction_amount"]

    fallback_median = fallback_group.transform("median")
    fallback_count = fallback_group.transform("count")

    # Decide which baseline to use
    use_fallback = primary_count < min_peer_size

    df["peer_median"] = primary_median.where(
        ~use_fallback,
        fallback_median,
    )

    # IMPORTANT:
    # Report the count of the actual baseline being used.
    df["peer_count"] = primary_count.where(
        ~use_fallback,
        fallback_count,
    )

    df["peer_baseline"] = np.where(
        use_fallback,
        "state + work_category",
        "constituency + work_category",
    )

    # Positive deviation only:
    # unusually high cost increases the risk signal.
    df["cost_deviation"] = (
        (df["sanction_amount"] - df["peer_median"])
        / df["peer_median"]
    )

    df["cost_deviation"] = df["cost_deviation"].replace(
        [np.inf, -np.inf],
        np.nan,
    ).fillna(0)

    df["cost_deviation_pct"] = (
        df["cost_deviation"] * 100
    )

    # Ignore projects cheaper than their peer baseline.
    positive_deviation = df["cost_deviation"].clip(lower=0)

    # Cap extreme deviations at 300% for stable 0–100 normalization.
    df["cost_risk"] = (
        positive_deviation.clip(upper=3.0) / 3.0 * 100
    )

    return df


if __name__ == "__main__":
    data = load_and_preprocess_data()
    result = calculate_cost_anomaly(data)

    print("Cost anomaly analysis successful")
    print("Projects:", len(result))

    print("\nHighest cost-risk projects:")
    print(
        result[
            [
                "unique_work_number",
                "work_category",
                "sanction_amount",
                "peer_median",
                "peer_count",
                "peer_baseline",
                "cost_deviation_pct",
                "cost_risk",
            ]
        ]
        .sort_values("cost_risk", ascending=False)
        .head(10)
        .to_string(index=False)
    )