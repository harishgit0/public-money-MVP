import pandas as pd


DATA_PATH = "data/mplad_projects.csv"


def load_and_preprocess_data(data_path: str = DATA_PATH) -> pd.DataFrame:
    """Load and prepare MPLAD project data for risk analysis."""

    df = pd.read_csv(data_path)

    # Normalize column names
    df.columns = df.columns.str.strip()

    # Clean text fields
    text_columns = [
        "state",
        "constituency",
        "mp_name",
        "work_category",
        "work_name",
        "implementing_agency_name",
        "work_status",
    ]

    for column in text_columns:
        df[column] = df[column].fillna("").astype(str).str.strip()

    # Ensure project cost is numeric
    df["sanction_amount"] = pd.to_numeric(
        df["sanction_amount"],
        errors="coerce",
    )

    # Parse dates (dataset uses DD-MM-YYYY)
    df["date_of_administrative_approval"] = pd.to_datetime(
        df["date_of_administrative_approval"],
        dayfirst=True,
        errors="coerce",
    )

    df["expected_completion_date"] = pd.to_datetime(
        df["expected_completion_date"],
        dayfirst=True,
        errors="coerce",
    )

    # Create the peer group used for cost and contractor analysis
    df["peer_group"] = (
        df["constituency"]
        + " | "
        + df["work_category"]
    )

    return df


if __name__ == "__main__":
    df = load_and_preprocess_data()

    print("Preprocessing successful")
    print("Shape:", df.shape)
    print("\nColumns:")
    print(df.columns.tolist())
    print("\nSample:")
    print(df[
        [
            "unique_work_number",
            "constituency",
            "work_category",
            "sanction_amount",
            "peer_group",
        ]
    ].head())