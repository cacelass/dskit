"""
check_copier.py — Valida que copier.yml es YAML válido y contiene las variables mínimas.
"""

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).parent.parent.parent

try:
    cfg = yaml.safe_load((ROOT / "copier.yml").read_text())
except Exception as e:
    print(f"ERROR: copier.yml no es YAML válido: {e}")
    sys.exit(1)

if not isinstance(cfg, dict):
    print("ERROR: copier.yml está vacío o no es un diccionario YAML válido")
    sys.exit(1)

REQUIRED = [
    "project_name",
    "project_slug",
    "project_author_name",
    "project_author_email",
    "project_description",
    "project_version",
    "project_open_source_license",
    "python_version",
    "ml_type",
    "task_type",
    "nn_model",
    "optimizer_type",
    "nn_loss_fn",
    "model_type",
    "cluster_model",
    "use_api",
    "use_docker",
    "use_duckdb",
    "use_mlflow",
    "use_monitoring",
    "use_optuna",
    "use_integration",
    "use_calibration",
    "use_conformal",
    "use_rag",
    "use_sdd",
    "use_mcp",
    "use_demo",
    "use_shap",
    "use_xgboost",
    "use_lightgbm",
    "use_catboost",
    "graphify_mode",
    "mcp_servers",
    "proyecto_perfil",
]

missing = [k for k in REQUIRED if k not in cfg]
if missing:
    print(f"ERROR: variables ausentes en copier.yml: {missing}")
    sys.exit(1)

print(f"copier.yml OK — {len(cfg)} variables definidas")
