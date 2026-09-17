import pandas as pd

from ai_ml.preprocessing.preprocess import load_and_preprocess_data


def calculate_contractor_risk(
    df: pd.DataFrame,
    min_peer_size: int = 5,
) -> pd.DataFrame:
    """
    Calculate contractor concentration risk.

    Concentration is measured as the share of projects handled by
    the same implementing agency within the relevant peer group.

    Primary peer group:
        constituency + work_category

    Fallback peer group:
        state + work_category
    """

    df = df.copy()

    # Primary peer-group counts
    peer_project_count = df.groupby("peer_group")["unique_work_number"].transform("count")

    contractor_peer_count = (
        df.groupby(
            ["peer_group", "implementing_agency_name"]
        )["unique_work_number"]
        .transform("count")
    )

    primary_concentration = (
        contractor_peer_count / peer_project_count
    )

    # Fallback: state + category
    fallback_group = df.groupby(
        ["state", "work_category"]
    )["unique_work_number"]

    fallback_project_count = fallback_group.transform("count")

    fallback_contractor_count = (
        df.groupby(
            ["state", "work_category", "implementing_agency_name"]
        )["unique_work_number"]
        .transform("count")
    )

    fallback_concentration = (
        fallback_contractor_count / fallback_project_count
    )

    # Use fallback for small constituency/category groups
    use_fallback = peer_project_count < min_peer_size

    df["contractor_peer_count"] = peer_project_count.where(
        ~use_fallback,
        fallback_project_count,
    )

    df["contractor_project_count"] = contractor_peer_count.where(
        ~use_fallback,
        fallback_contractor_count,
    )

    df["contractor_concentration"] = primary_concentration.where(
        ~use_fallback,
        fallback_concentration,
    )

    # Convert 0–1 concentration to a 0–100 risk signal
    df["contractor_risk"] = (
        df["contractor_concentration"] * 100
    ).clip(upper=100)

    return df


if __name__ == "__main__":
    data = load_and_preprocess_data()
    result = calculate_contractor_risk(data)

    print("Contractor concentration analysis successful")
    print("Projects:", len(result))

    print("\nHighest contractor-risk projects:")
    print(
        result[
            [
                "unique_work_number",
                "work_category",
                "implementing_agency_name",
                "contractor_peer_count",
                "contractor_project_count",
                "contractor_concentration",
                "contractor_risk",
            ]
        ]
        .sort_values("contractor_risk", ascending=False)
        .head(10)
        .to_string(index=False)
    )