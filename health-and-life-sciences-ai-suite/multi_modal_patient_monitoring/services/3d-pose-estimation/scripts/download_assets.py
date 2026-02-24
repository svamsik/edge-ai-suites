import os
import pathlib
import urllib.request
import json
import time
import shutil
import yaml

MODELS_ROOT = pathlib.Path(os.getenv("MODELS_ROOT", "/models")) / "3d-pose"
VIDEOS_ROOT = pathlib.Path(os.getenv("VIDEOS_ROOT", "/videos")) / "3d-pose"
VIDEO_URL = "https://storage.openvinotoolkit.org/data/test_data/videos/face-demographics-walking.mp4"
VIDEO_NAME = "face-demographics-walking.mp4"


def _download(url: str, dst: pathlib.Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() and dst.stat().st_size > 0:
        return
    urllib.request.urlretrieve(url, dst)


def ensure_model() -> None:
    """Trigger 3D pose model download via model-download API and wait until ready.

    Model name/type/hub come from model-config.yaml (pose-3d section).
    """
    MODELS_ROOT.mkdir(parents=True, exist_ok=True)

    xml_path = MODELS_ROOT / "human-pose-estimation-3d-0001.xml"
    bin_path = MODELS_ROOT / "human-pose-estimation-3d-0001.bin"

    def _present(p: pathlib.Path) -> bool:
        return p.exists() and p.stat().st_size > 0

    # If both XML and BIN already exist at final location, nothing to do
    if _present(xml_path) and _present(bin_path):
        return

    config_path = pathlib.Path("/configs/model-config.yaml")
    with config_path.open("r", encoding="utf-8") as f:
        full_cfg = yaml.safe_load(f)

    models_cfg = full_cfg.get("pose-3d", {}).get("models", [])
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

    # Model-download service writes under hls_assets/3d-pose inside the shared models volume
    hls_dir = pathlib.Path(os.getenv("MODELS_ROOT", "/models")) / "hls_assets" / "3d-pose"
    hls_xml_path = hls_dir / "human-pose-estimation-3d-0001.xml"
    hls_bin_path = hls_dir / "human-pose-estimation-3d-0001.bin"

    timeout = 500
    elapsed = 0
    while (not _present(hls_xml_path) or not _present(hls_bin_path)) and elapsed < timeout:
        print(f"[3d-pose] Waiting for model in {hls_dir}... ({elapsed}/{timeout}s)")
        time.sleep(5)
        elapsed += 5

    if not _present(hls_xml_path) or not _present(hls_bin_path):
        raise RuntimeError("3D pose model did not appear within timeout in hls_assets")

    # Copy from hls_assets into the service-specific models directory (XML + BIN)
    shutil.copy2(hls_xml_path, xml_path)
    shutil.copy2(hls_bin_path, bin_path)


def ensure_video() -> None:
    """Download demo 3D pose video if missing."""
    VIDEOS_ROOT.mkdir(parents=True, exist_ok=True)
    video_path = VIDEOS_ROOT / VIDEO_NAME
    _download(VIDEO_URL, video_path)


def validate_assets() -> None:
    """Final sanity check: required 3D pose model and video must exist."""
    xml_path = MODELS_ROOT / "human-pose-estimation-3d-0001.xml"
    bin_path = MODELS_ROOT / "human-pose-estimation-3d-0001.bin"
    video_path = VIDEOS_ROOT / VIDEO_NAME

    def _present(p: pathlib.Path) -> bool:
        return p.exists() and p.stat().st_size > 0

    missing = [
        str(p)
        for p in (xml_path, bin_path, video_path)
        if not _present(p)
    ]
    if missing:
        raise RuntimeError(f"3D pose assets missing after download: {missing}")

    print("[3d-pose] Model and demo video are present.")


if __name__ == "__main__":
    ensure_model()
    ensure_video()
    validate_assets()
