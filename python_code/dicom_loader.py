"""
dicom_loader.py
================
Handles the upload workflow: the user uploads a single ZIP file
containing a study's worth of DICOM files. This module extracts the ZIP,
reads each file's header (no pixel data, so it is fast), and groups the
files into series using SeriesInstanceUID. Each series is tagged as a
localizer or not, based on ImageType / SeriesDescription, and every file
found is indexed by its InstanceNumber (the ACR "slice number").

Nothing in the original compute() functions changes: they still just take
a file path. This module's only job is figuring out which path on disk
corresponds to "slice 7", "slice 11", the localizer, and so on, so the
rest of the app never has to ask the user to upload individual files.
"""

import os
import shutil
import tempfile
import zipfile
from pathlib import Path

import pydicom


def extract_zip(zip_bytes: bytes) -> str:
    """Extract a ZIP (given as raw bytes) to a fresh temp directory; return its path."""
    extract_dir = tempfile.mkdtemp(prefix="acr_dicom_")
    zip_path = os.path.join(extract_dir, "_upload.zip")
    with open(zip_path, "wb") as f:
        f.write(zip_bytes)
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(extract_dir)
    os.unlink(zip_path)
    return extract_dir


def _is_localizer(ds) -> bool:
    image_type = [str(s).upper() for s in getattr(ds, "ImageType", [])]
    desc = str(getattr(ds, "SeriesDescription", "")).upper()
    return ("LOCALIZER" in image_type) or ("LOCALIZER" in desc) or ("SCOUT" in desc)


def scan_and_group(root_dir: str) -> dict:
    """
    Walk every file under root_dir, read DICOM headers only (fast), and
    group them by SeriesInstanceUID.

    Returns:
        {
          series_uid: {
              "description":  str,
              "number":       str,
              "is_localizer": bool,
              "instances":    { instance_number(int): filepath(str) },
              "count":        int,
          },
          ...
        }
    """
    series = {}
    for path in Path(root_dir).rglob("*"):
        if not path.is_file():
            continue
        if "__MACOSX" in path.parts or path.name.startswith("."):
            continue
        try:
            ds = pydicom.dcmread(str(path), force=True, stop_before_pixels=True)
        except Exception:
            continue
        if not hasattr(ds, "SeriesInstanceUID"):
            continue
        suid = str(ds.SeriesInstanceUID)
        try:
            inst = int(ds.InstanceNumber)
        except Exception:
            inst = None

        if suid not in series:
            series[suid] = {
                "description":  str(getattr(ds, "SeriesDescription", "Unnamed Series")).strip() or "Unnamed Series",
                "number":       str(getattr(ds, "SeriesNumber", "")),
                "is_localizer": _is_localizer(ds),
                "instances":    {},
            }
        if inst is not None:
            series[suid]["instances"][inst] = str(path)

    for s in series.values():
        s["count"] = len(s["instances"])

    return series


def default_selection(series: dict):
    """
    Pick sensible defaults when there is only one obvious candidate.

    Returns (selected_series_uid_or_None, localizer_uid_or_None)
    """
    localizers = {uid: s for uid, s in series.items() if s["is_localizer"] and s["count"] > 0}
    non_local  = {uid: s for uid, s in series.items() if not s["is_localizer"] and s["count"] > 0}

    loc_uid = next(iter(localizers)) if len(localizers) == 1 else None
    sel_uid = next(iter(non_local)) if len(non_local) == 1 else None
    return sel_uid, loc_uid


def series_label(s: dict) -> str:
    role = "Localizer" if s["is_localizer"] else "Axial series"
    return f'{s["description"]} — Series {s["number"]} ({s["count"]} images, {role})'


def get_instance_path(series: dict, series_uid: str, instance_number: int):
    if not series_uid or series_uid not in series:
        return None
    return series[series_uid]["instances"].get(instance_number)


def get_localizer_path(series: dict, localizer_uid: str):
    if not localizer_uid or localizer_uid not in series:
        return None
    instances = series[localizer_uid]["instances"]
    if not instances:
        return None
    # A localizer series is usually a single image; just take the first one.
    return instances[sorted(instances.keys())[0]]


def cleanup_dir(path):
    if path and os.path.isdir(path):
        shutil.rmtree(path, ignore_errors=True)
