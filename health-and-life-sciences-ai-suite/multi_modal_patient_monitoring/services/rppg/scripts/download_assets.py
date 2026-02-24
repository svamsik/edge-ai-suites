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

    def _present(p: pathlib.Path) -> bool:
        return p.exists() and p.stat().st_size > 0

    # If any XML+BIN already exist at final location, nothing to do
    existing_xml = list(MODELS_ROOT.glob("*.xml"))
    existing_bin = list(MODELS_ROOT.glob("*.bin"))
    if existing_xml and existing_bin:
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

    def _present_any(paths):
        return any(p.exists() and p.stat().st_size > 0 for p in paths)

    timeout = int(os.getenv("MODEL_WAIT_TIMEOUT", "1200"))
    elapsed = 0
    hls_xml_paths = []
    hls_bin_paths = []
    hls_hdf5_paths = []

    while elapsed < timeout:
        hls_xml_paths = list(hls_dir.glob("*.xml"))
        hls_bin_paths = list(hls_dir.glob("*.bin"))
        hls_hdf5_paths = list(hls_dir.glob("*.hdf5"))

        if _present_any(hls_xml_paths) and _present_any(hls_bin_paths):
            break

        print(f"[rppg] Waiting for model in {hls_dir}... ({elapsed}/{timeout}s)")
        time.sleep(5)
        elapsed += 5

    if not _present_any(hls_xml_paths) or not _present_any(hls_bin_paths):
        raise RuntimeError("RPPG model did not appear within timeout in hls_assets")

    # Copy all discovered IR (XML+BIN) and original HDF5 into the service-specific models directory
    for src_xml in hls_xml_paths:
        if src_xml.exists() and src_xml.stat().st_size > 0:
            dst_xml = MODELS_ROOT / src_xml.name
            shutil.copy2(src_xml, dst_xml)

    for src_bin in hls_bin_paths:
        if src_bin.exists() and src_bin.stat().st_size > 0:
            dst_bin = MODELS_ROOT / src_bin.name
            shutil.copy2(src_bin, dst_bin)

    for src_hdf5 in hls_hdf5_paths:
        if src_hdf5.exists() and src_hdf5.stat().st_size > 0:
            dst_hdf5 = MODELS_ROOT / src_hdf5.name
            shutil.copy2(src_hdf5, dst_hdf5)


def ensure_video() -> None:
    """Download demo RPPG video if missing."""
    VIDEOS_ROOT.mkdir(parents=True, exist_ok=True)
    video_path = VIDEOS_ROOT / VIDEO_NAME
    _download(VIDEO_URL, video_path)


def validate_assets() -> None:
    """Final sanity check: required RPPG model and video must exist."""
    xml_paths = list(MODELS_ROOT.glob("*.xml"))
    bin_paths = list(MODELS_ROOT.glob("*.bin"))
    video_path = VIDEOS_ROOT / VIDEO_NAME

    def _present(p: pathlib.Path) -> bool:
        return p.exists() and p.stat().st_size > 0

    missing = [
        str(p)
        for p in (xml_paths + bin_paths + [video_path])
        if not _present(p)
    ]
    # Require at least one XML and one BIN file, all non-empty, plus the video
    if not xml_paths or not bin_paths or missing:
        raise RuntimeError(f"RPPG assets missing after download: {missing or 'no XML/BIN files found'}")

    print("[rppg] Model and demo video are present.")


if __name__ == "__main__":
    ensure_model()
    ensure_video()
    validate_assets()
