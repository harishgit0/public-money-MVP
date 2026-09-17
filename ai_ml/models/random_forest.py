import os
from dataclasses import dataclass

import numpy as np
import pandas as pd


FEATURE_COLUMNS = [
    "cost_deviation_pct",
    "contractor_concentration",
    "text_similarity",
]


# ============================================================
# CONTROLLED TRAINING DATA
# ============================================================

def build_controlled_training_data(
    df: pd.DataFrame,
    random_state: int = 42,
):
    """
    Build a balanced dataset containing:

        label 0 -> original/normal project
        label 1 -> controlled anomaly

    IMPORTANT:
    These are synthetic control labels created for model validation.
    They are NOT confirmed fraud labels.
    """

    rng = np.random.default_rng(random_state)

    normal = (
        df[FEATURE_COLUMNS]
        .replace([np.inf, -np.inf], np.nan)
        .fillna(0)
        .astype(float)
        .copy()
    )

    normal["label"] = 0

    n_projects = len(normal)

    if n_projects == 0:
        raise ValueError(
            "Cannot build Random Forest training data from an empty dataset."
        )

    # Randomly divide projects into three controlled-anomaly groups.
    indices = rng.permutation(n_projects)

    split_1 = n_projects // 3
    split_2 = 2 * n_projects // 3

    cost_indices = indices[:split_1]
    contractor_indices = indices[split_1:split_2]
    text_indices = indices[split_2:]

    anomaly_parts = []

    # --------------------------------------------------------
    # CONTROL 1: Cost anomaly
    # --------------------------------------------------------

    if len(cost_indices) > 0:
        cost_anomalies = normal.iloc[
            cost_indices
        ][FEATURE_COLUMNS].copy()

        cost_anomalies["cost_deviation_pct"] = (
            cost_anomalies["cost_deviation_pct"] + 300
        )

        anomaly_parts.append(cost_anomalies)

    # --------------------------------------------------------
    # CONTROL 2: Contractor concentration
    # --------------------------------------------------------

    if len(contractor_indices) > 0:
        contractor_anomalies = normal.iloc[
            contractor_indices
        ][FEATURE_COLUMNS].copy()

        contractor_anomalies[
            "contractor_concentration"
        ] = 1.0

        anomaly_parts.append(contractor_anomalies)

    # --------------------------------------------------------
    # CONTROL 3: Text duplication
    # --------------------------------------------------------

    if len(text_indices) > 0:
        text_anomalies = normal.iloc[
            text_indices
        ][FEATURE_COLUMNS].copy()

        text_anomalies["text_similarity"] = 1.0

        anomaly_parts.append(text_anomalies)

    if not anomaly_parts:
        raise ValueError(
            "Unable to generate controlled anomaly samples."
        )

    anomalies = pd.concat(
        anomaly_parts,
        ignore_index=True,
    )

    anomalies["label"] = 1

    training = pd.concat(
        [
            normal,
            anomalies,
        ],
        ignore_index=True,
    )

    X = training[
        FEATURE_COLUMNS
    ].astype(float)

    y = training[
        "label"
    ].astype(int)

    return X, y


# ============================================================
# DECISION TREE
# ============================================================

@dataclass
class TreeNode:
    is_leaf: bool
    probability: float
    feature_index: int | None = None
    threshold: float | None = None
    left: object = None
    right: object = None


class DecisionTree:
    """
    Lightweight numerical decision tree.

    Each tree receives a random bootstrap sample and considers
    only a random subset of features at each split.
    """

    def __init__(
        self,
        max_depth: int = 7,
        min_samples_leaf: int = 3,
        max_features: int = 1,
        random_state: int = 42,
    ):
        self.max_depth = max_depth
        self.min_samples_leaf = min_samples_leaf
        self.max_features = max_features

        self.rng = np.random.default_rng(
            random_state
        )

        self.root = None
        self.feature_importances_ = None

    # --------------------------------------------------------
    # Gini impurity
    # --------------------------------------------------------

    @staticmethod
    def gini(y: np.ndarray) -> float:
        if len(y) == 0:
            return 0.0

        probability = np.mean(y)

        return float(
            2.0
            * probability
            * (1.0 - probability)
        )

    # --------------------------------------------------------
    # Candidate split thresholds
    # --------------------------------------------------------

    def _candidate_thresholds(
        self,
        values: np.ndarray,
    ) -> np.ndarray:

        unique_values = np.unique(values)

        if len(unique_values) <= 1:
            return np.array([])

        # Small number of unique values:
        # evaluate all midpoints.
        if len(unique_values) <= 64:

            return (
                unique_values[:-1]
                + unique_values[1:]
            ) / 2.0

        # Larger feature cardinality:
        # use quantile-based candidates to keep training manageable.
        quantiles = np.linspace(
            0.05,
            0.95,
            32,
        )

        thresholds = np.unique(
            np.quantile(
                values,
                quantiles,
            )
        )

        return thresholds

    # --------------------------------------------------------
    # Find best split
    # --------------------------------------------------------

    def _best_split(
        self,
        X: np.ndarray,
        y: np.ndarray,
        feature_indices: np.ndarray,
    ):

        parent_impurity = self.gini(y)

        if parent_impurity == 0:
            return None

        best_gain = 0.0
        best_feature = None
        best_threshold = None

        n_samples = len(y)

        for feature_index in feature_indices:

            values = X[:, feature_index]

            thresholds = self._candidate_thresholds(
                values
            )

            for threshold in thresholds:

                left_mask = values <= threshold
                right_mask = ~left_mask

                left_count = int(
                    left_mask.sum()
                )

                right_count = int(
                    right_mask.sum()
                )

                if (
                    left_count
                    < self.min_samples_leaf
                    or right_count
                    < self.min_samples_leaf
                ):
                    continue

                left_impurity = self.gini(
                    y[left_mask]
                )

                right_impurity = self.gini(
                    y[right_mask]
                )

                weighted_impurity = (
                    left_count / n_samples
                ) * left_impurity + (
                    right_count / n_samples
                ) * right_impurity

                gain = (
                    parent_impurity
                    - weighted_impurity
                )

                if gain > best_gain:

                    best_gain = gain
                    best_feature = feature_index
                    best_threshold = threshold

        if best_feature is None:
            return None

        return (
            best_feature,
            best_threshold,
            best_gain,
        )

    # --------------------------------------------------------
    # Grow tree recursively
    # --------------------------------------------------------

    def _grow(
        self,
        X: np.ndarray,
        y: np.ndarray,
        depth: int,
    ):

        probability = float(
            np.mean(y)
        )

        # Stopping conditions.
        if (
            depth >= self.max_depth
            or len(y)
            < 2 * self.min_samples_leaf
            or self.gini(y) == 0
        ):
            return TreeNode(
                is_leaf=True,
                probability=probability,
            )

        n_features = X.shape[1]

        feature_indices = self.rng.choice(
            n_features,
            size=min(
                self.max_features,
                n_features,
            ),
            replace=False,
        )

        split = self._best_split(
            X,
            y,
            feature_indices,
        )

        if split is None:
            return TreeNode(
                is_leaf=True,
                probability=probability,
            )

        (
            feature_index,
            threshold,
            gain,
        ) = split

        values = X[:, feature_index]

        left_mask = values <= threshold
        right_mask = ~left_mask

        left_child = self._grow(
            X[left_mask],
            y[left_mask],
            depth + 1,
        )

        right_child = self._grow(
            X[right_mask],
            y[right_mask],
            depth + 1,
        )

        if self.feature_importances_ is not None:

            self.feature_importances_[
                feature_index
            ] += gain * len(y)

        return TreeNode(
            is_leaf=False,
            probability=probability,
            feature_index=feature_index,
            threshold=threshold,
            left=left_child,
            right=right_child,
        )

    # --------------------------------------------------------
    # Fit
    # --------------------------------------------------------

    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
    ):

        X = np.asarray(
            X,
            dtype=float,
        )

        y = np.asarray(
            y,
            dtype=int,
        )

        self.feature_importances_ = (
            np.zeros(
                X.shape[1],
                dtype=float,
            )
        )

        self.root = self._grow(
            X,
            y,
            depth=0,
        )

        total_importance = (
            self.feature_importances_.sum()
        )

        if total_importance > 0:

            self.feature_importances_ /= (
                total_importance
            )

        return self

    # --------------------------------------------------------
    # Predict one sample
    # --------------------------------------------------------

    def _predict_one(
        self,
        row: np.ndarray,
        node: TreeNode,
    ) -> float:

        if node.is_leaf:
            return node.probability

        if (
            row[node.feature_index]
            <= node.threshold
        ):
            return self._predict_one(
                row,
                node.left,
            )

        return self._predict_one(
            row,
            node.right,
        )

    # --------------------------------------------------------
    # Predict probabilities
    # --------------------------------------------------------

    def predict_proba(
        self,
        X: np.ndarray,
    ) -> np.ndarray:

        X = np.asarray(
            X,
            dtype=float,
        )

        return np.array(
            [
                self._predict_one(
                    row,
                    self.root,
                )
                for row in X
            ]
        )


# ============================================================
# RANDOM FOREST
# ============================================================

class NumpyRandomForestClassifier:
    """
    Random Forest classifier implemented with NumPy.

    Random Forest components:
        1. Bootstrap sampling
        2. Multiple decision trees
        3. Random feature selection
        4. Tree-level probability aggregation
    """

    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: int = 7,
        min_samples_leaf: int = 3,
        max_features: str = "sqrt",
        random_state: int = 42,
    ):

        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.min_samples_leaf = min_samples_leaf
        self.max_features = max_features
        self.random_state = random_state

        self.estimators_ = []
        self.feature_importances_ = None

    # --------------------------------------------------------
    # Number of random features per split
    # --------------------------------------------------------

    def _get_max_features(
        self,
        feature_count: int,
    ) -> int:

        if self.max_features == "sqrt":

            return max(
                1,
                int(
                    np.sqrt(
                        feature_count
                    )
                ),
            )

        if self.max_features == "log2":

            return max(
                1,
                int(
                    np.log2(
                        feature_count
                    )
                ),
            )

        return min(
            int(self.max_features),
            feature_count,
        )

    # --------------------------------------------------------
    # Train forest
    # --------------------------------------------------------

    def fit(
        self,
        X: pd.DataFrame | np.ndarray,
        y: pd.Series | np.ndarray,
    ):

        X = np.asarray(
            X,
            dtype=float,
        )

        y = np.asarray(
            y,
            dtype=int,
        )

        if len(X) != len(y):
            raise ValueError(
                "X and y must contain the same number of samples."
            )

        if len(X) == 0:
            raise ValueError(
                "Cannot train on an empty dataset."
            )

        rng = np.random.default_rng(
            self.random_state
        )

        n_samples, n_features = X.shape

        max_features = (
            self._get_max_features(
                n_features
            )
        )

        self.estimators_ = []

        importance_sum = np.zeros(
            n_features,
            dtype=float,
        )

        for tree_index in range(
            self.n_estimators
        ):

            # ------------------------------------------------
            # Bootstrap sampling
            # ------------------------------------------------

            bootstrap_indices = (
                rng.integers(
                    0,
                    n_samples,
                    size=n_samples,
                )
            )

            X_bootstrap = X[
                bootstrap_indices
            ]

            y_bootstrap = y[
                bootstrap_indices
            ]

            # ------------------------------------------------
            # Create tree
            # ------------------------------------------------

            tree = DecisionTree(
                max_depth=self.max_depth,
                min_samples_leaf=(
                    self.min_samples_leaf
                ),
                max_features=max_features,
                random_state=(
                    self.random_state
                    + tree_index
                ),
            )

            tree.fit(
                X_bootstrap,
                y_bootstrap,
            )

            self.estimators_.append(
                tree
            )

            importance_sum += (
                tree.feature_importances_
            )

        total_importance = (
            importance_sum.sum()
        )

        if total_importance > 0:

            importance_sum /= (
                total_importance
            )

        self.feature_importances_ = (
            importance_sum
        )

        return self

    # --------------------------------------------------------
    # Probability prediction
    # --------------------------------------------------------

    def predict_proba(
        self,
        X: pd.DataFrame | np.ndarray,
    ) -> np.ndarray:

        X = np.asarray(
            X,
            dtype=float,
        )

        if not self.estimators_:
            raise RuntimeError(
                "Random Forest has not been trained."
            )

        tree_predictions = np.array(
            [
                tree.predict_proba(X)
                for tree in self.estimators_
            ]
        )

        # Average the probabilities from all trees.
        return tree_predictions.mean(
            axis=0
        )

    # --------------------------------------------------------
    # Class prediction
    # --------------------------------------------------------

    def predict(
        self,
        X: pd.DataFrame | np.ndarray,
    ) -> np.ndarray:

        probabilities = (
            self.predict_proba(X)
        )

        return (
            probabilities >= 0.5
        ).astype(int)


# ============================================================
# MODEL HELPERS
# ============================================================

def train_random_forest(
    X,
    y,
):
    """Train the project Random Forest."""

    model = NumpyRandomForestClassifier(
        n_estimators=100,
        max_depth=7,
        min_samples_leaf=3,
        max_features="sqrt",
        random_state=42,
    )

    model.fit(
        X,
        y,
    )

    return model


def predict_anomaly_probability(
    model,
    df: pd.DataFrame,
) -> pd.DataFrame:

    result = df.copy()

    X = (
        result[FEATURE_COLUMNS]
        .replace(
            [np.inf, -np.inf],
            np.nan,
        )
        .fillna(0)
        .astype(float)
    )

    probabilities = (
        model.predict_proba(X)
    )

    result[
        "rf_anomaly_probability"
    ] = probabilities * 100

    result[
        "rf_anomaly_prediction"
    ] = (
        probabilities >= 0.5
    ).astype(int)

    return result


# ============================================================
# EVALUATION
# ============================================================

def evaluate_model(
    y_true,
    y_pred,
):
    """
    Calculate classification metrics without sklearn.
    """

    y_true = np.asarray(
        y_true,
        dtype=int,
    )

    y_pred = np.asarray(
        y_pred,
        dtype=int,
    )

    true_positive = int(
        np.sum(
            (y_true == 1)
            & (y_pred == 1)
        )
    )

    true_negative = int(
        np.sum(
            (y_true == 0)
            & (y_pred == 0)
        )
    )

    false_positive = int(
        np.sum(
            (y_true == 0)
            & (y_pred == 1)
        )
    )

    false_negative = int(
        np.sum(
            (y_true == 1)
            & (y_pred == 0)
        )
    )

    accuracy = (
        true_positive
        + true_negative
    ) / max(len(y_true), 1)

    precision = (
        true_positive
        / max(
            true_positive
            + false_positive,
            1,
        )
    )

    recall = (
        true_positive
        / max(
            true_positive
            + false_negative,
            1,
        )
    )

    f1 = (
        2
        * precision
        * recall
        / max(
            precision + recall,
            1e-12,
        )
    )

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "true_positive": true_positive,
        "true_negative": true_negative,
        "false_positive": false_positive,
        "false_negative": false_negative,
    }


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

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

    print("Loading project data...")

    data = load_and_preprocess_data()

    # --------------------------------------------------------
    # Generate the three existing risk signals
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

    result = data[
        [
            "unique_work_number",
            "work_name",
            "sanction_amount",
        ]
    ].copy()

    result = result.merge(
        cost[
            [
                "unique_work_number",
                "cost_deviation_pct",
            ]
        ],
        on="unique_work_number",
        how="inner",
    )

    result = result.merge(
        contractor[
            [
                "unique_work_number",
                "contractor_concentration",
            ]
        ],
        on="unique_work_number",
        how="inner",
    )

    result = result.merge(
        text[
            [
                "unique_work_number",
                "text_similarity",
            ]
        ],
        on="unique_work_number",
        how="inner",
    )

    print(
        f"Projects loaded: {len(result)}"
    )

    # ========================================================
    # LEAK-FREE VALIDATION
    # ========================================================

    print(
        "\nCreating leak-free train/test split..."
    )

    rng = np.random.default_rng(
        42
    )

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

    print(
        "Original training projects:",
        len(train_projects),
    )

    print(
        "Original test projects:",
        len(test_projects),
    )

    # --------------------------------------------------------
    # Create controlled anomalies separately
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

    print(
        "Training samples:",
        len(X_train),
    )

    print(
        "Test samples:",
        len(X_test),
    )

    print(
        "Training normal samples:",
        int(
            (y_train == 0).sum()
        ),
    )

    print(
        "Training controlled anomalies:",
        int(
            (y_train == 1).sum()
        ),
    )

    print(
        "Test normal samples:",
        int(
            (y_test == 0).sum()
        ),
    )

    print(
        "Test controlled anomalies:",
        int(
            (y_test == 1).sum()
        ),
    )

    # --------------------------------------------------------
    # Train on training projects only
    # --------------------------------------------------------

    print(
        "\nTraining Random Forest..."
    )

    validation_model = train_random_forest(
        X_train,
        y_train,
    )

    print(
        "Trees trained:",
        len(
            validation_model.estimators_
        ),
    )

    # --------------------------------------------------------
    # Evaluate on unseen test projects
    # --------------------------------------------------------

    test_predictions = (
        validation_model.predict(
            X_test
        )
    )

    metrics = evaluate_model(
        y_test,
        test_predictions,
    )

    print(
        "\nLeak-free Random Forest evaluation:"
    )

    print(
        f"Accuracy : "
        f"{metrics['accuracy']:.4f}"
    )

    print(
        f"Precision: "
        f"{metrics['precision']:.4f}"
    )

    print(
        f"Recall   : "
        f"{metrics['recall']:.4f}"
    )

    print(
        f"F1 Score : "
        f"{metrics['f1']:.4f}"
    )

    print(
        "\nConfusion matrix:"
    )

    print(
        f"TN={metrics['true_negative']} "
        f"FP={metrics['false_positive']}"
    )

    print(
        f"FN={metrics['false_negative']} "
        f"TP={metrics['true_positive']}"
    )

    print(
        "\nValidation feature importance:"
    )

    for feature, importance in zip(
        FEATURE_COLUMNS,
        validation_model.feature_importances_,
    ):

        print(
            f"{feature}: "
            f"{importance:.4f}"
        )

    # ========================================================
    # FINAL MODEL
    # ========================================================

    print(
        "\nTraining final Random Forest "
        "on all controlled training data..."
    )

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

    # --------------------------------------------------------
    # Predict on all 989 real projects
    # --------------------------------------------------------

    final_result = (
        predict_anomaly_probability(
            final_model,
            result,
        )
    )

    # --------------------------------------------------------
    # Save predictions
    # --------------------------------------------------------

    results_path = (
        "ai_ml/data/"
        "random_forest_results.csv"
    )

    os.makedirs(
        os.path.dirname(results_path),
        exist_ok=True,
    )

    final_result = (
        final_result
        .sort_values(
            "rf_anomaly_probability",
            ascending=False,
        )
        .reset_index(drop=True)
    )

    final_result.to_csv(
        results_path,
        index=False,
    )

    # --------------------------------------------------------
    # Save feature importance
    # --------------------------------------------------------

    importance_path = (
        "ai_ml/data/"
        "rf_feature_importance.csv"
    )

    importance_df = pd.DataFrame(
        {
            "feature": FEATURE_COLUMNS,
            "importance": (
                final_model
                .feature_importances_
            ),
        }
    ).sort_values(
        "importance",
        ascending=False,
    )

    importance_df.to_csv(
        importance_path,
        index=False,
    )

    # --------------------------------------------------------
    # Save validation metrics
    # --------------------------------------------------------

    metrics_path = (
        "ai_ml/data/"
        "rf_metrics.csv"
    )

    metrics_df = pd.DataFrame(
        [metrics]
    )

    metrics_df.to_csv(
        metrics_path,
        index=False,
    )

    # --------------------------------------------------------
    # Final output
    # --------------------------------------------------------

    print(
        "\nRandom Forest analysis successful"
    )

    print(
        "Results:",
        results_path,
    )

    print(
        "Feature importance:",
        importance_path,
    )

    print(
        "Metrics:",
        metrics_path,
    )

    print(
        "\nTop 10 RF anomaly probabilities:"
    )

    print(
        final_result[
            [
                "unique_work_number",
                "work_name",
                "rf_anomaly_probability",
                "rf_anomaly_prediction",
            ]
        ]
        .head(10)
        .to_string(index=False)
    )