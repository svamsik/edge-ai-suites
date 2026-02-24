import os
import pathlib
import urllib.request
import json
import time
import shutil
import yaml

# Base directory where models are mounted
MODELS_ROOT = pathlib.Path(os.getenv("MODELS_ROOT", "/models")) / "ai-ecg"


def ensure_models() -> None:
    """Trigger ECG IR model download via model-download API and wait until ready.

    Model name/type/hub come from model-config.yaml (ai-ecg section).
    """
    MODELS_ROOT.mkdir(parents=True, exist_ok=True)

    def _all_present(paths):
        return all(p.exists() and p.stat().st_size > 0 for p in paths)

    config_path = pathlib.Path("/configs/model-config.yaml")
    with config_path.open("r", encoding="utf-8") as f:
        full_cfg = yaml.safe_load(f)

    models_cfg = full_cfg.get("ai-ecg", {}).get("models", [])
    # Derive expected IR filenames from config (ir_file field)
    ecg_xml_names = [m.get("ir_file") for m in models_cfg if m.get("ir_file")]

    # If XML+BIN already exist at final location for all configured models, nothing to do
    xml_paths = [MODELS_ROOT / name for name in ecg_xml_names]
    bin_paths = [MODELS_ROOT / name.replace(".xml", ".bin") for name in ecg_xml_names]
    if _all_present(xml_paths) and _all_present(bin_paths):
        return

    payload = {
        "models": [
            {
                "name": m["name"],
                "hub": m.get("hub", "hls"),
                "type": m["type"],
            }
            for m in models_cfg
        ],
        "parallel_downloads": False,
    }

    base_url = os.getenv("MODEL_DOWNLOAD_URL", "http://localhost:8000")
    req = urllib.request.Request(
        f"{base_url}/api/v1/models/download?download_path=hls_assets",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        resp.read()

    # Model-download service writes under hls_assets/ai-ecg inside the shared models volume
    hls_dir = pathlib.Path(os.getenv("MODELS_ROOT", "/models")) / "hls_assets" / "ai-ecg"
    hls_xml_paths = [hls_dir / name for name in ecg_xml_names]
    hls_bin_paths = [hls_dir / name.replace(".xml", ".bin") for name in ecg_xml_names]

    timeout = int(os.getenv("MODEL_WAIT_TIMEOUT", "1200"))
    elapsed = 0
    stable_checks = 0
    prev_sizes = None

    while elapsed < timeout:
        if _all_present(hls_xml_paths) and _all_present(hls_bin_paths):
            sizes = [p.stat().st_size for p in hls_xml_paths + hls_bin_paths]
            if sizes == prev_sizes:
                stable_checks += 1
            else:
                stable_checks = 1
                prev_sizes = sizes

            if stable_checks >= 3:
                break
        else:
            stable_checks = 0

        print(f"[ai-ecg] Waiting for ECG models in {hls_dir}... ({elapsed}/{timeout}s)")
        time.sleep(5)
        elapsed += 5

    if not (_all_present(hls_xml_paths) and _all_present(hls_bin_paths)) or stable_checks < 3:
        raise RuntimeError("ECG models did not appear complete within timeout in hls_assets")

    # Always copy from hls_assets into the service-specific models directory (XML + BIN)
    for src, dst in zip(hls_xml_paths, xml_paths):
        shutil.copy2(src, dst)
    for src, dst in zip(hls_bin_paths, bin_paths):
        shutil.copy2(src, dst)


def validate_assets() -> None:
    """Final sanity check: required ECG models must exist under MODELS_ROOT."""
    config_path = pathlib.Path("/configs/model-config.yaml")
    with config_path.open("r", encoding="utf-8") as f:
        full_cfg = yaml.safe_load(f)

    models_cfg = full_cfg.get("ai-ecg", {}).get("models", [])
    ecg_xml_names = [m.get("ir_file") for m in models_cfg if m.get("ir_file")]

    xml_paths = [MODELS_ROOT / name for name in ecg_xml_names]
    bin_paths = [MODELS_ROOT / name.replace(".xml", ".bin") for name in ecg_xml_names]

    def _all_present(paths):
        return all(p.exists() and p.stat().st_size > 0 for p in paths)

    if not _all_present(xml_paths) or not _all_present(bin_paths):
        missing = [
            str(p)
            for p in xml_paths + bin_paths
            if not (p.exists() and p.stat().st_size > 0)
        ]
        raise RuntimeError(f"ai-ecg assets missing after download: {missing}")

    print("[ai-ecg] All required model assets are present.")


if __name__ == "__main__":
    ensure_models()
    validate_assets()
