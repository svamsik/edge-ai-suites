import os
import pathlib
import urllib.request
import json
import time
import shutil
import yaml

MODELS_ROOT = pathlib.Path(os.getenv("MODELS_ROOT", "/models")) / "rppg"
VIDEOS_ROOT = pathlib.Path(os.getenv("VIDEOS_ROOT", "/videos")) / "rppg"
VIDEO_URL = "https://github.com/opencv/opencv/raw/master/samples/data/vtest.avi"
VIDEO_NAME = "sample.mp4"


def _download(url: str, dst: pathlib.Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() and dst.stat().st_size > 0:
        return
    urllib.request.urlretrieve(url, dst)


def ensure_model() -> None:
    """Trigger RPPG model download via model-download API and wait until ready.

    Model name/type/hub come from model-config.yaml (rppg section).
    """
    MODELS_ROOT.mkdir(parents=True, exist_ok=True)
    xml_path = MODELS_ROOT / "mtts_can.xml"
    bin_path = MODELS_ROOT / "mtts_can.bin"
    hdf5_path = MODELS_ROOT / "mtts_can.hdf5"

    def _present(p: pathlib.Path) -> bool:
        return p.exists() and p.stat().st_size > 0

    # If XML and BIN already exist at final location, nothing to do
    if _present(xml_path) and _present(bin_path):
        return

    config_path = pathlib.Path("/configs/model-config.yaml")
    with config_path.open("r", encoding="utf-8") as f:
        full_cfg = yaml.safe_load(f)

    models_cfg = full_cfg.get("rppg", {}).get("models", [])
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

    # Model-download service writes under hls_assets/rppg inside the shared models volume
    hls_dir = pathlib.Path(os.getenv("MODELS_ROOT", "/models")) / "hls_assets" / "rppg"
    hls_xml_path = hls_dir / "mtts_can.xml"
    hls_bin_path = hls_dir / "mtts_can.bin"
    hls_hdf5_path = hls_dir / "mtts_can.hdf5"

    timeout = 500
    elapsed = 0
    while (not _present(hls_xml_path) or not _present(hls_bin_path)) and elapsed < timeout:
        print(f"[rppg] Waiting for model in {hls_dir}... ({elapsed}/{timeout}s)")
        time.sleep(5)
        elapsed += 5

    if not _present(hls_xml_path) or not _present(hls_bin_path):
        raise RuntimeError("RPPG model did not appear within timeout in hls_assets")

    # Copy IR (XML+BIN) and original HDF5 into the service-specific models directory
    shutil.copy2(hls_xml_path, xml_path)
    shutil.copy2(hls_bin_path, bin_path)
    if _present(hls_hdf5_path):
        shutil.copy2(hls_hdf5_path, hdf5_path)


def ensure_video() -> None:
    """Download demo RPPG video if missing."""
    VIDEOS_ROOT.mkdir(parents=True, exist_ok=True)
    video_path = VIDEOS_ROOT / VIDEO_NAME
    _download(VIDEO_URL, video_path)


def validate_assets() -> None:
    """Final sanity check: required RPPG model and video must exist."""
    xml_path = MODELS_ROOT / "mtts_can.xml"
    bin_path = MODELS_ROOT / "mtts_can.bin"
    video_path = VIDEOS_ROOT / VIDEO_NAME

    def _present(p: pathlib.Path) -> bool:
        return p.exists() and p.stat().st_size > 0

    missing = [
        str(p)
        for p in (xml_path, bin_path, video_path)
        if not _present(p)
    ]
    if missing:
        raise RuntimeError(f"RPPG assets missing after download: {missing}")

    print("[rppg] Model and demo video are present.")


if __name__ == "__main__":
    ensure_model()
    ensure_video()
    validate_assets()
