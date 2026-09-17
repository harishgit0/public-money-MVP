import numpy as np
import pandas as pd
from fastembed import TextEmbedding

from ai_ml.preprocessing.preprocess import load_and_preprocess_data


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def calculate_text_similarity(
    df: pd.DataFrame,
    model_name: str = MODEL_NAME,
) -> pd.DataFrame:
    """
    Calculate semantic similarity between project descriptions.

    For each project, find the most similar other project and use
    its cosine similarity as the text-based risk signal.
    """

    df = df.copy()

    descriptions = (
        df["work_name"]
        .fillna("")
        .astype(str)
        .tolist()
    )

    # FastEmbed uses ONNX Runtime and avoids PyTorch.
    model = TextEmbedding(model_name=model_name)

    # Generate embeddings.
    embeddings = np.array(
        list(model.embed(descriptions))
    )

    # Normalize embeddings so dot product = cosine similarity.
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    normalized_embeddings = embeddings / np.maximum(norms, 1e-12)

    # Cosine similarity matrix.
    similarity_matrix = normalized_embeddings @ normalized_embeddings.T

    # Prevent a project from matching itself.
    np.fill_diagonal(similarity_matrix, -1.0)

    # Best matching project for every project.
    best_match_indices = similarity_matrix.argmax(axis=1)

    best_similarities = similarity_matrix[
        np.arange(len(df)),
        best_match_indices,
    ]

    df["similar_project_id"] = df.iloc[
        best_match_indices
    ]["unique_work_number"].values

    df["similar_project_name"] = df.iloc[
        best_match_indices
    ]["work_name"].values

    df["text_similarity"] = best_similarities

    # Convert similarity to 0–100 risk.
    df["text_similarity_risk"] = (
        df["text_similarity"]
        .clip(0, 1)
        * 100
    )

    return df


if __name__ == "__main__":
    data = load_and_preprocess_data()
    result = calculate_text_similarity(data)

    print("\nText similarity analysis successful")
    print("Projects:", len(result))

    print("\nHighest text-similarity projects:")
    print(
        result[
            [
                "unique_work_number",
                "work_name",
                "similar_project_id",
                "similar_project_name",
                "text_similarity",
                "text_similarity_risk",
            ]
        ]
        .sort_values(
            "text_similarity_risk",
            ascending=False,
        )
        .head(10)
        .to_string(index=False)
    )