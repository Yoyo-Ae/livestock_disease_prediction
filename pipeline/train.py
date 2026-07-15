#IMPORTS
import joblib
import mlflow
import mlflow.sklearn
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")
import os
import json
from datetime import datetime
from dotenv import load_dotenv
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.metrics import(
    classification_report,
    roc_auc_score,
    f1_score,
    accuracy_score,
    precision_score,
    recall_score,
    confusion_matrix,
    ConfusionMatrixDisplay,
    RocCurveDisplay
)
from xgboost import XGBClassifier
import shap

load_dotenv()

#LOAD SPLITS

splits = joblib.load("models/splits.pkl")
x_train = splits["x_train"]
x_test = splits["x_test"]
y_train = splits["y_train"]
y_test = splits["y_test"]
x_test_raw = splits["x_test_raw"]
FEATURES = splits["features_names"]

#SETUP MLFLOW
mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("livestock_disease_prediction")
os.makedirs("models",exist_ok = True)
os.makedirs("models/plot", exist_ok=True)

#DEFINE MODELS AND HYPERPARAMETERS GRID
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
neg = (y_train == 0).sum()
pos = (y_train == 1).sum()
spw = neg/pos

model_configs = {
 
 "LogisticRegression": {
    "model": LogisticRegression(
        max_iter=1000,
        random_state=42,
        class_weight="balanced"
    ),
    "params": {
        "C": [0.01, 0.1, 1, 10],
        "solver" : ["lbfgs", "liblinear"]
    }
 },
 "RandomForest": {
    "model": RandomForestClassifier(
        random_state=42,
        class_weight="balanced",
        n_jobs=-1
    ),
    "params": {
        "n_estimators": [100,200],
        "max_depth": [10,20,None],
        "min_samples_split": [2,5],
        "min_samples_leaf": [1,2]
    }
 },
 "XGBoost": {
     "model":XGBClassifier(
            eval_metric="logloss",
            random_state=42,
            n_jobs=-1,
            verbosity=0,
            scale_pos_weight = spw
     ),
     "params": {
            "n_estimators": [100,200],
            "max_depth":[4,6,8],
            "learning_rate": [0.05,0.1],
            "subsample": [0.8,1.0],
            "colsample_bytree":[0.8,1.0]
     }
 }
}

#TRAIN AND EVALUATE EACH MODEL
results = {}
best_f1 = 0
best_model = None
best_model_name = ""

for model_name, config in model_configs.items():
    print(f"CURRENTLY TRAINING: {model_name}\n")

    with mlflow.start_run(run_name=model_name):
        print(f"  Running GridSearchCV ({cv.n_splits} - fold)....")

        gs = GridSearchCV(
            estimator=config["model"],
            param_grid=config["params"],
            cv=cv,
            scoring = "f1",
            n_jobs = -1,
            verbose=0,
            refit=True
        )

        gs.fit(x_train, y_train)
        model = gs.best_estimator_

        print(f" Best Param: {gs.best_params_}\n")
        print(f" Best CV F1: {gs.best_score_:.4f}\n")

        #evaluate on test set
        preds = model.predict(x_test)
        proba = model.predict_proba(x_test)[:,1]

        acc = accuracy_score(y_test, preds)
        prec = precision_score(y_test, preds, zero_division=0)
        rec = recall_score(y_test, preds, zero_division=0)
        f1 = f1_score(y_test, preds, zero_division=0)
        auc = roc_auc_score(y_test, proba)


        print(
            f"Test set Results: "
            f"Accuracy: {acc:.4f}\n"
            f"Prcision: {prec:.4f}\n"
            f"Recall: {rec:.4f}\n"
            f"f1_score: {f1:.4f}\n"
            f"AUC-ROC: {auc:.4f}\n"
            f"Classification Report: \n"
             )
        print(classification_report(y_test,preds, target_names=["No Outbreak", "Outbreak"]))

        #LOG TO MLFLOW
        mlflow.log_params(gs.best_params_)
        mlflow.log_metric("accuracy", acc)
        mlflow.log_metric("Precision", prec)
        mlflow.log_metric("Recall", rec)
        mlflow.log_metric("F1_score", f1)
        mlflow.log_metric("auc_roc", auc)
        mlflow.log_metric("cv_f1", gs.best_score_ )
        mlflow.sklearn.log_model(
            sk_model=model, name=model_name, skops_trusted_types=['xgboost.core.Booster','xgboost.sklearn.XGBClassifier'])

        #CONFUSION MATRIX PLOT
        fig, ax = plt.subplots(figsize=(6,5))
        cm = confusion_matrix(y_test, preds)
        disp = ConfusionMatrixDisplay(
            confusion_matrix==cm,
            display_labels=["No outbreak", "Outbreak"]
        )
        disp.plot(ax=ax, colorbar=True, cmap="Greens")
        ax.set_title(f"{model_name} - Confusion Matrix")
        cm_path = f"models/plots/{model_name}_confusion_matrix.png"
        os.makedirs(os.path.dirname(cm_path), exist_ok=True)
        fig.savefig(cm_path, dpi=150,bbox_inches="tight")
        mlflow.log_artifact(cm_path)
        plt.close()
        print(f" Confusion matrix saved")

        #ROC curve plot
        fig, ax = plt.subplots(figsize=(6,5))
        RocCurveDisplay.from_predictions(
            y_test, proba,
            ax=ax,
            name=model_name,
            curve_kwargs= dict(color="green")
        )
        ax.set_title(f"{model_name} - ROC Curve (AUC={auc:.3f})")
        ax.plot([0,1],[0,1], "k--", label="Random classifier")
        ax.legend()
        roc_path = f"models/plots/{model_name}_roc_curve.png"
        os.makedirs(os.path.dirname(roc_path), exist_ok=True)
        fig.savefig(roc_path, dpi=150, bbox_inches="tight")
        mlflow.log_artifacts(roc_path)
        plt.close()
        print(f"ROC curve saved")

        #Save results
        results[model_name] = {
            "model": model,
            "accuracy": acc,
            "precision": prec,
            "recall": rec,
            "f1-score": f1,
            "auc-roc": auc,
            "cv_f1": gs.best_score_,
            "best_params": gs.best_params_
        }

        #Track best model
        if f1 > best_f1:
            best_f1 = f1
            best_model = model
            best_model_name = model_name

print("MODEL COMPARSION RESULTS")
print(f"\n{'Model':<25} {'Accuracy':>10} {'Precison':>10} {'Recall':>10} {'F1':>10} {'AUC_ROC':>10}\n")

for name, r in results.items():
    marker = " BEST: " if name == best_model_name else ""
    print(f"{name:<25} {r['accuracy']:>10.4f} {r['precision']:>10.4f} {r['recall']:>10.4f} {r['f1-score']:>10.4f} {r['auc-roc']:>10.4f}{marker}\n")

print(f"Best Model: {best_model_name} (F1: {best_f1:.4f})\n")

#SAVE THE MODEL
joblib.dump(best_model, "models/best_model.pkl")

metadata = {
    "model_name": best_model_name,
    "accuracy": results[best_model_name]['accuracy'],
    "precision": results[best_model_name]['precision'],
    "recall": results[best_model_name]['recall'],
    "f1-score": best_f1,
    "auc-roc": results[best_model_name]["auc-roc"],
    "features": FEATURES,
    "best_params": results[best_model_name]['best_params'],
    "trained_at": datetime.now().isoformat()
}

with open("models/model_metadata.json", "w") as f:
    json.dump(metadata, f, indent=2)
print("Metadata saved to models/model_metadata.json\n")

#SHAP
try:
    if best_model_name == "LogisticRgression":
        explainer = shap.LinearExplainer(best_model, x_train)
        shap_values = explainer.shap_values(x_test)
    else:
        explainer = shap.TreeExplainer(best_model)
        shap_values = explainer.shap_values(x_test)

    if isinstance(shap_values, list):
        shap_vals = shap_values[1]
    elif isinstance(shap_values,np.ndarray) and shap_values.ndim == 3:
        shap_vals = shap_values[:,:,1]
    else:
        shap_vals = shap_values

    print(f"shap_values after selection shape: {shap_vals.shape}")

    
    fig, ax = plt.subplots(figsize=(10,6))
    shap.summary_plot(
        shap_vals,
        x_test_raw,
        feature_names=FEATURES,
        plot_type="bar", 
        show=False,
        max_display=len(FEATURES)
    )

    plt.title(f"{best_model_name} = Feature Importance (SHAP)")
    plt.tight_layout()
    shap_bar_path = "models/plots/shap_feature_importance_bar.png"
    os.makedirs(os.path.dirname(shap_bar_path), exist_ok=True)
    plt.savefig(shap_bar_path, dpi=500, bbox_inches="tight")
    plt.close()
    print("SHAP bar plot saved\n")

    fig, ax = plt.subplots(figsize=(10,6))
    shap.summary_plot(
        shap_vals,
        x_test_raw, 
        feature_names = FEATURES,
        show= False,
        max_display=len(FEATURES)
    )
    plt.title(f"{best_model_name} - SHAP Summary Plot")
    plt.tight_layout()
    shap_dot_path = "models/plots/shap_summary_plot.png"
    os.makedirs(os.path.dirname(shap_dot_path), exist_ok=True)
    plt.savefig(shap_dot_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f" SHAP summary plot saved\n")

    mean_abs_shap = np.abs(shap_vals).mean(axis=0)
    print("features shape", np.shape(FEATURES))
    print("mean shape", np.shape(mean_abs_shap))
    feature_importance = pd.DataFrame({
        "feature":FEATURES,
        "mean_abs_shap": mean_abs_shap
    }).sort_values("mean_abs_shap", ascending=False)

    print(f"\n Top features by SHAP importance: ")

    print(feature_importance.to_string(index=False))

    feature_importance.to_csv(
        "models/feature_importance.csv", index=False
    )
    print( "Feature importance saved to models/feature_importance.csv")
except Exception as e:
    print(f" SHAP failed: {e}")
    print(f"Skipping SHAP - continuing without it\n")

    if hasattr(best_model, "feature_importances_"):
        fi = pd.DataFrame({
            "feature": FEATURES,
            "importance": best_model.feature_importances_
        }).sort_values("importance", ascending=False)
        print("\n Fallback -Built-in features importances: ")
        print(fi.to_string(index=False))

        fig, ax = plt.subplots(figsize=(10,6))
        ax.barh(fi["feature"][::-1], fi["importance"][::-1], color="green")
        ax.set_xlabel("feature Impotance")
        ax.set_title(f"{best_model_name} - Feature Impotance")
        plt.tight_layout()
        fi_path = "models/plots/feature_importance_builtin.png"
        os.makedirs(os.path.dirname(fi_path), exist_ok=True)
        plt.savefig(fi_path, dpi=500, bbox_inches="tight")
        plt.close()
        f1.to_csv("models/feature_importance.csv", index=False)
        print(f"\nFEATURE IMPORTANCE PLOT SAVED\n")

#SUMMARY
print(f"Best model:{best_model_name}\nF1-score: {results[best_model_name]['f1-score']:.4f}\nAUC-ROC: {results[best_model_name]['auc-roc']:.4f}\nRecall: {results[best_model_name]['recall']:.4f}\nPrecision: {results[best_model_name]['precision']:.4f}\n")
print(f"\nFiles Saved include models/\nbest_model.pkl\nmodel_metadata.json\nfeature_importance.csv\nplots/(confusion matrices, ROC curves, SHAP plots)\n")
print("View MLflow results at:http//localhost:5000")



