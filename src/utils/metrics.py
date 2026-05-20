import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    confusion_matrix,
)


def binary_classification_metrics(y_true, y_pred, y_proba=None):
    """
    Calcula un conjunto de métricas para clasificación binaria.

    Parameters
    ----------
    y_true  : array-like, etiquetas reales (0/1).
    y_pred  : array-like, predicciones discretas (0/1).
    y_proba : array-like opcional, probabilidad de la clase positiva.

    Returns
    -------
    dict con accuracy, balanced_accuracy, precision, recall, f1,
    roc_auc, pr_auc y los conteos de la matriz de confusión.
    """
    metrics = {
        "accuracy":          accuracy_score(y_true, y_pred),
        "balanced_accuracy": balanced_accuracy_score(y_true, y_pred),
        "precision":         precision_score(y_true, y_pred, zero_division=0),
        "recall":            recall_score(y_true, y_pred, zero_division=0),
        "f1":                f1_score(y_true, y_pred, zero_division=0),
    }

    if y_proba is not None:
        metrics["roc_auc"] = roc_auc_score(y_true, y_proba)
        metrics["pr_auc"]  = average_precision_score(y_true, y_proba)
    else:
        metrics["roc_auc"] = np.nan
        metrics["pr_auc"]  = np.nan

    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    metrics.update({"tn": tn, "fp": fp, "fn": fn, "tp": tp})

    return metrics


def metrics_table(results_dict):
    """
    Convierte un dict {nombre_modelo: dict_metricas} en un DataFrame ordenado.
    """
    df = pd.DataFrame(results_dict).T
    cols_order = [
        "accuracy", "balanced_accuracy",
        "precision", "recall", "f1",
        "roc_auc", "pr_auc",
        "tn", "fp", "fn", "tp",
    ]
    cols_order = [c for c in cols_order if c in df.columns]
    return df[cols_order].round(4)