"""
ACR MRI Phantom: Streamlit Web Interface
=============================================
Run from the same directory as the test modules:
    streamlit run acr_qa_app.py

Workflow:
    1. The user uploads a single ZIP file containing every DICOM file for
       the study (localizer plus all ACR phantom slices).
    2. dicom_loader.py extracts the ZIP and reads each file's header to
       group files into series and index every slice by its InstanceNumber.
    3. Each test page automatically pulls the DICOM file(s) it needs from
       that index. No per-test file uploads. The user is only prompted for
       input where it genuinely cannot be automated: picking between
       multiple candidate series, and the visual-inspection measurements
       (bar differences, spoke counts, resolved hole size).

This still calls the compute() / get_insert_image() / get_slice_image()
functions that live in the original test modules. Every original main()
function remains untouched and still works via the tkinter desktop app.
"""

import sys, os, hashlib
import streamlit as st
import matplotlib
matplotlib.use("Agg")          # must come before pyplot import
import matplotlib.pyplot as plt

# ── Make sure the test modules are importable ─────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))

import dicom_loader
import test_geom_acc
import SNR
import Uniformity
import Percent_Signal_Ghosting
import SliceThicknessFWHM
import Slice_Position_Accuracy
import Low_Contrast_Detectability
import High_Contrast_Spatial_Res

# ──────────────────────────────────────────────────────────────────────────
#  Helpers
# ──────────────────────────────────────────────────────────────────────────

def render_table(rows):
    """
    rows: list of (name, value_str, range_str, passed)
    passed = True | False | None
    """
    html = """
    <table style="width:100%;border-collapse:collapse;margin-top:10px">
    <thead><tr>
      <th style="padding:9px 14px;text-align:left;font-family:monospace;font-size:11px;
                 letter-spacing:.1em;text-transform:uppercase;color:#3B82F6;
                 background:#0B1628;border-bottom:1px solid #1E3A5F">Measurement</th>
      <th style="padding:9px 14px;text-align:left;font-family:monospace;font-size:11px;
                 letter-spacing:.1em;text-transform:uppercase;color:#3B82F6;
                 background:#0B1628;border-bottom:1px solid #1E3A5F">Measured Value</th>
      <th style="padding:9px 14px;text-align:left;font-family:monospace;font-size:11px;
                 letter-spacing:.1em;text-transform:uppercase;color:#3B82F6;
                 background:#0B1628;border-bottom:1px solid #1E3A5F">ACR Range</th>
      <th style="padding:9px 14px;text-align:left;font-family:monospace;font-size:11px;
                 letter-spacing:.1em;text-transform:uppercase;color:#3B82F6;
                 background:#0B1628;border-bottom:1px solid #1E3A5F">Status</th>
    </tr></thead><tbody>
    """
    for name, val, rng, passed in rows:
        if passed is not None and bool(passed):
            badge = ('<span style="padding:3px 10px;background:#052E16;color:#4ADE80;'
                     'border:1px solid #16A34A;border-radius:4px;font-family:monospace;'
                     'font-size:11px;font-weight:700">&#10003; PASS</span>')
        elif passed is not None and not bool(passed):
            badge = ('<span style="padding:3px 10px;background:#450A0A;color:#FCA5A5;'
                     'border:1px solid #EF4444;border-radius:4px;font-family:monospace;'
                     'font-size:11px;font-weight:700">&#10007; FAIL</span>')
        else:
            badge = ('<span style="padding:3px 10px;background:#1E293B;color:#94A3B8;'
                     'border:1px solid #334155;border-radius:4px;font-family:monospace;'
                     'font-size:11px">N/A</span>')
        html += (
            f'<tr>'
            f'<td style="padding:11px 14px;border-bottom:1px solid #0F2044;color:#CBD5E1">{name}</td>'
            f'<td style="padding:11px 14px;border-bottom:1px solid #0F2044;color:#F1F5F9;'
            f'    font-family:monospace;font-weight:700">{val}</td>'
            f'<td style="padding:11px 14px;border-bottom:1px solid #0F2044;color:#64748B;'
            f'    font-family:monospace;font-size:12px">{rng}</td>'
            f'<td style="padding:11px 14px;border-bottom:1px solid #0F2044">{badge}</td>'
            f'</tr>'
        )
    html += "</tbody></table>"
    st.markdown(html, unsafe_allow_html=True)

def store(key, rows):
    passed_vals = [r[3] for r in rows if r[3] is not None]
    st.session_state.qa_results[key] = {
        "passed":       all(passed_vals) if passed_vals else None,
        "measurements": rows,
    }

INFO_BOX = (
    'background:#0F2044;border:1px solid #1E3A5F;border-left:3px solid #3B82F6;'
    'border-radius:6px;padding:12px 16px;margin-bottom:16px;font-size:13px;color:#94A3B8'
)
WARN_BOX = (
    'background:#2B1B0E;border:1px solid #7C4A12;border-left:3px solid #F59E0B;'
    'border-radius:6px;padding:12px 16px;margin-bottom:16px;font-size:13px;color:#FCD9A8'
)

# ──────────────────────────────────────────────────────────────────────────
#  Study loading (ZIP upload → extracted, header-indexed series)
# ──────────────────────────────────────────────────────────────────────────

def load_study(zip_file):
    """Extract + scan a newly uploaded ZIP, but only if it's actually new."""
    file_hash = hashlib.md5(zip_file.getvalue()).hexdigest()
    if st.session_state.get("study", {}).get("zip_hash") == file_hash:
        return  # same file already loaded — nothing to do

    dicom_loader.cleanup_dir(st.session_state.get("study", {}).get("extract_dir"))

    with st.spinner("Extracting ZIP and reading DICOM headers…"):
        extract_dir = dicom_loader.extract_zip(zip_file.getvalue())
        series = dicom_loader.scan_and_group(extract_dir)
    sel_uid, loc_uid = dicom_loader.default_selection(series)

    st.session_state.study = {
        "zip_hash":      file_hash,
        "extract_dir":   extract_dir,
        "series":        series,
        "selected_uid":  sel_uid,
        "localizer_uid": loc_uid,
    }
    st.session_state.qa_results = {}


def clear_study():
    dicom_loader.cleanup_dir(st.session_state.get("study", {}).get("extract_dir"))
    st.session_state.study = {}
    st.session_state.qa_results = {}


def require_study():
    """Call at the top of every test page. Returns the study dict, or None
    (after rendering a helpful message) if nothing has been uploaded yet."""
    study = st.session_state.get("study")
    if not study or not study.get("series"):
        st.markdown(
            f'<div style="{INFO_BOX}">No study loaded yet. Upload a ZIP file containing your '
            'DICOM study in the sidebar to begin.</div>',
            unsafe_allow_html=True,
        )
        return None
    return study


def active_series_caption(study):
    series, sel_uid = study["series"], study["selected_uid"]
    if sel_uid and sel_uid in series:
        st.caption(f"Active series: {dicom_loader.series_label(series[sel_uid])}")
    else:
        st.markdown(f'<div style="{WARN_BOX}">No axial series selected. '
                    'Choose one in the sidebar.</div>', unsafe_allow_html=True)


def missing_warning(missing):
    if missing:
        st.markdown(
            f'<div style="{WARN_BOX}">Missing from the active series: <b>{", ".join(missing)}</b>. '
            'This test cannot run until those slices are available.</div>',
            unsafe_allow_html=True,
        )

# ──────────────────────────────────────────────────────────────────────────
#  Page config
# ──────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ACR MRI Phantom QA",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(f"""
<style>
.stApp                        {{ background:#070F1C; color:#CBD5E1; }}
section[data-testid="stSidebar"] {{ background:#0B1628; border-right:1px solid #1E3A5F; }}
.stButton > button            {{ background:#1D4ED8; color:#fff; border:none;
                                 border-radius:6px; font-weight:600; }}
.stButton > button:hover      {{ background:#2563EB; }}
.stButton > button:disabled   {{ background:#1E3A5F; color:#475569; }}
</style>
""", unsafe_allow_html=True)

TEST_KEYS = {
    "geometric":       "Geometric Accuracy",
    "slice_position":  "Slice Position Accuracy",
    "slice_thickness": "Slice Thickness",
    "uniformity":      "Image Uniformity",
    "snr":             "SNR",
    "ghosting":        "% Signal Ghosting",
    "low_contrast":    "Low Contrast Detect.",
    "high_contrast":   "High Contrast Res.",
}

if "qa_results" not in st.session_state:
    st.session_state.qa_results = {}
if "study" not in st.session_state:
    st.session_state.study = {}

# ──────────────────────────────────────────────────────────────────────────
#  Sidebar — upload, series selection, navigation, progress
# ──────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ACR MRI QA")
    st.caption("American College of Radiology\nPhantom Accreditation Pipeline")
    st.divider()

    st.markdown("**Study Upload**")
    zip_file = st.file_uploader("DICOM study (.zip)", type=["zip"], key="study_zip")
    if zip_file is not None:
        try:
            load_study(zip_file)
        except Exception as e:
            st.error(f"Could not read this ZIP file: {e}")

    study = st.session_state.study
    if study.get("series"):
        series = study["series"]
        non_local = {u: s for u, s in series.items() if not s["is_localizer"] and s["count"] > 0}
        localizers = {u: s for u, s in series.items() if s["is_localizer"] and s["count"] > 0}

        st.success(f"{len(series)} series found, {sum(s['count'] for s in series.values())} images")

        # Axial series picker (only prompt if there's a real choice to make)
        if len(non_local) > 1:
            opts = list(non_local.keys())
            labels = {u: dicom_loader.series_label(non_local[u]) for u in opts}
            current = study["selected_uid"] if study["selected_uid"] in opts else opts[0]
            choice = st.selectbox("Series to validate", opts, index=opts.index(current),
                                   format_func=lambda u: labels[u], key="series_picker")
            if choice != study["selected_uid"]:
                study["selected_uid"] = choice
                st.session_state.qa_results = {}
                st.rerun()
        elif len(non_local) == 1:
            st.caption("Series: " + dicom_loader.series_label(next(iter(non_local.values()))))
        else:
            st.warning("No axial image series detected in this ZIP.")

        # Localizer picker (only prompt if there's a real choice to make)
        if len(localizers) > 1:
            opts = list(localizers.keys())
            labels = {u: dicom_loader.series_label(localizers[u]) for u in opts}
            current = study["localizer_uid"] if study["localizer_uid"] in opts else opts[0]
            choice = st.selectbox("Localizer series", opts, index=opts.index(current),
                                   format_func=lambda u: labels[u], key="localizer_picker")
            if choice != study["localizer_uid"]:
                study["localizer_uid"] = choice
                st.rerun()
        elif len(localizers) == 1:
            st.caption("Localizer: " + dicom_loader.series_label(next(iter(localizers.values()))))
        else:
            st.caption("No localizer series detected (needed for Geometric Accuracy only).")

        if st.button("Clear study / upload another"):
            clear_study()
            st.rerun()
    else:
        st.caption("No study uploaded yet.")

    st.divider()
    page = st.radio("Select test", [
        "Dashboard",
        "Geometric Accuracy",
        "Slice Position Accuracy",
        "Slice Thickness (FWHM)",
        "Image Uniformity",
        "Signal-to-Noise Ratio",
        "Percent Signal Ghosting",
        "Low Contrast Detectability",
        "High Contrast Resolution",
    ], label_visibility="hidden")

    st.divider()
    res    = st.session_state.qa_results
    done   = len(res)
    passes = sum(1 for v in res.values() if v.get("passed") is True)
    fails  = sum(1 for v in res.values() if v.get("passed") is False)
    st.markdown(f"**Progress:** {done} / 8 tests")
    if done:
        colour = "#4ADE80" if fails == 0 else "#FCA5A5"
        st.markdown(f'<span style="color:{colour};font-weight:700">'
                    f'{"✓" if fails==0 else "⚠"} {passes} pass / {fails} fail</span>',
                    unsafe_allow_html=True)
    for key, label in TEST_KEYS.items():
        if key in res:
            v = res[key].get("passed")
            dot = "🟢" if (v is not None and bool(v)) else ("🔴" if (v is not None and not bool(v)) else "⚪")
            st.caption(f"{dot} {label}")


# ══════════════════════════════════════════════════════════════════════════
#  DASHBOARD
# ══════════════════════════════════════════════════════════════════════════
if "Dashboard" in page:
    st.markdown("## ACR MRI Phantom Quality Assurance")
    st.caption("American College of Radiology · Accreditation Pipeline")

    if study.get("series"):
        st.markdown("### Detected Series")
        rows_html = '<table style="width:100%;border-collapse:collapse;margin-bottom:20px">'
        rows_html += ('<thead><tr>' +
                      ''.join(f'<th style="padding:8px 12px;text-align:left;font-family:monospace;'
                              f'font-size:11px;letter-spacing:.08em;text-transform:uppercase;'
                              f'color:#3B82F6;background:#0B1628;border-bottom:1px solid #1E3A5F">{h}</th>'
                              for h in ["Description", "Series #", "Images", "Role"]) +
                      '</tr></thead><tbody>')
        for uid, s in study["series"].items():
            role = "Localizer" if s["is_localizer"] else "Axial"
            active = " (active)" if uid in (study["selected_uid"], study["localizer_uid"]) else ""
            rows_html += (
                f'<tr><td style="padding:9px 12px;border-bottom:1px solid #0F2044;color:#CBD5E1">'
                f'{s["description"]}{active}</td>'
                f'<td style="padding:9px 12px;border-bottom:1px solid #0F2044;color:#94A3B8">{s["number"]}</td>'
                f'<td style="padding:9px 12px;border-bottom:1px solid #0F2044;color:#94A3B8">{s["count"]}</td>'
                f'<td style="padding:9px 12px;border-bottom:1px solid #0F2044;color:#38BDF8">{role}</td></tr>'
            )
        rows_html += "</tbody></table>"
        st.markdown(rows_html, unsafe_allow_html=True)

    if not res:
        if not study.get("series"):
            st.markdown(f'<div style="{INFO_BOX}">No study loaded yet. Upload a ZIP file containing '
                        'your DICOM study in the sidebar, then step through each test below.</div>',
                        unsafe_allow_html=True)
        overview = [
            ("Geometric Accuracy",      "Localizer + Slices 1 & 5",  "Diameter 190 ± 2 mm · Localizer 148 ± 2 mm"),
            ("Slice Position Accuracy", "Slices 1 & 11",             "Bar length difference < 5 mm"),
            ("Slice Thickness",         "Slice 1",                   "FWHM = 5 ± 0.7 mm"),
            ("Image Uniformity",        "Slice 7",                   "PIU ≥ 87.5 %"),
            ("Signal-to-Noise Ratio",   "Slice 7",                   "≥ 90 % of site baseline"),
            ("Percent Signal Ghosting", "Slice 7 (ACR T1 only)",     "Ghosting ratio < 2.5 %"),
            ("Low Contrast Detect.",    "Slices 8–11",               "≥ 9 spokes per insert · ≥ 37 total"),
            ("High Contrast Res.",      "Slice 1",                   "Resolve ≤ 1.0 mm hole arrays"),
        ]
        cols = st.columns(2)
        card = ('background:#0B1628;border:1px solid #1E3A5F;border-radius:8px;'
                'padding:14px 16px;margin-bottom:10px')
        for i, (name, inp, crit) in enumerate(overview):
            with cols[i % 2]:
                st.markdown(
                    f'<div style="{card}">'
                    f'<b style="color:#E2E8F0"> {name}</b><br>'
                    f'<span style="color:#64748B;font-size:12px">Slices used: {inp}</span><br>'
                    f'<span style="color:#38BDF8;font-size:12px">Criterion: {crit}</span>'
                    f'</div>', unsafe_allow_html=True)
    else:
        st.markdown("### Results Summary")
        all_rows = [m for key in TEST_KEYS if key in res for m in res[key].get("measurements", [])]
        if all_rows:
            render_table(all_rows)


# ══════════════════════════════════════════════════════════════════════════
#  GEOMETRIC ACCURACY  -  test_geom_acc.compute()
# ══════════════════════════════════════════════════════════════════════════
elif "Geometric Accuracy" in page:
    st.markdown("## Geometric Accuracy")
    st.markdown(f'<div style="{INFO_BOX}">ACR T1 series only. Uses the localizer plus slices 1 and 5 '
                'from the active series, detected automatically from the uploaded ZIP.</div>',
                unsafe_allow_html=True)

    study = require_study()
    if study:
        active_series_caption(study)
        series = study["series"]
        loc_path = dicom_loader.get_localizer_path(series, study["localizer_uid"])
        s1_path  = dicom_loader.get_instance_path(series, study["selected_uid"], 1)
        s5_path  = dicom_loader.get_instance_path(series, study["selected_uid"], 5)
        missing = [n for n, p in [("Localizer", loc_path), ("Slice 1", s1_path), ("Slice 5", s5_path)] if not p]
        missing_warning(missing)

        if st.button("▶  Run Geometric Accuracy", disabled=bool(missing)):
            try:
                with st.spinner("Analysing images…"):
                    geo, figs = test_geom_acc.compute(loc_path, s1_path, s5_path)
                R = geo
                rows = [
                    ("Localizer Length",     f"{R['localizer_length']:.2f} mm",  "146 – 150 mm", 146 <= R["localizer_length"] <= 150),
                    ("Slice 1 Vertical Ø",   f"{R['slice1_vertical']:.2f} mm",   "188 – 192 mm", 188 <= R["slice1_vertical"] <= 192),
                    ("Slice 1 Horizontal Ø", f"{R['slice1_horizontal']:.2f} mm", "188 – 192 mm", 188 <= R["slice1_horizontal"] <= 192),
                    ("Slice 5 Vertical Ø",   f"{R['slice5_vertical']:.2f} mm",   "188 – 192 mm", 188 <= R["slice5_vertical"] <= 192),
                    ("Slice 5 Horizontal Ø", f"{R['slice5_horizontal']:.2f} mm", "188 – 192 mm", 188 <= R["slice5_horizontal"] <= 192),
                    ("Slice 5 Diagonal 1",   f"{R['slice5_diag1']:.2f} mm",      "188 – 192 mm", 188 <= R["slice5_diag1"] <= 192),
                    ("Slice 5 Diagonal 2",   f"{R['slice5_diag2']:.2f} mm",      "188 – 192 mm", 188 <= R["slice5_diag2"] <= 192),
                ]
                store("geometric", rows)
                st.markdown("### Results"); render_table(rows)
                st.markdown("### Images")
                for fig in figs:
                    st.pyplot(fig); plt.close(fig)
            except Exception as e:
                st.error(f"Processing error: {e}")

        if "geometric" in st.session_state.qa_results:
            st.markdown("### Results (last run)")
            render_table(st.session_state.qa_results["geometric"]["measurements"])


# ══════════════════════════════════════════════════════════════════════════
#  SLICE POSITION ACCURACY  -  Slice_Position_Accuracy.get_insert_image()
# ══════════════════════════════════════════════════════════════════════════
elif "Slice Position" in page:
    st.markdown("## Slice Position Accuracy")
    st.markdown(f'<div style="{INFO_BOX}">Uses slices 1 and 11 from the active series, detected '
                'automatically. Examine the zoomed bar inserts, then enter the measured bar length '
                'difference for each slice.</div>', unsafe_allow_html=True)

    study = require_study()
    if study:
        active_series_caption(study)
        series = study["series"]
        s1_path  = dicom_loader.get_instance_path(series, study["selected_uid"], 1)
        s11_path = dicom_loader.get_instance_path(series, study["selected_uid"], 11)
        missing = [n for n, p in [("Slice 1", s1_path), ("Slice 11", s11_path)] if not p]
        missing_warning(missing)

        if s1_path or s11_path:
            ic1, ic2 = st.columns(2)
            for col, path, label in [(ic1, s1_path, "Slice 1"), (ic2, s11_path, "Slice 11")]:
                if path:
                    fig = Slice_Position_Accuracy.get_insert_image(path)
                    with col:
                        st.pyplot(fig); plt.close(fig)
                        st.caption(f"{label} — bar position insert")

        st.markdown("**Enter bar length differences** measured from the images above:")
        d1c, d2c = st.columns(2)
        with d1c: diff1 = st.number_input("Slice 1 bar difference (mm)",  min_value=0.0, step=0.1, key="spa_d1")
        with d2c: diff2 = st.number_input("Slice 11 bar difference (mm)", min_value=0.0, step=0.1, key="spa_d2")

        if st.button("▶  Record Results", disabled=bool(missing)):
            rows = [
                ("Slice 1 Bar Difference",  f"{diff1:.2f} mm", "< 5 mm", diff1 < 5.0),
                ("Slice 11 Bar Difference", f"{diff2:.2f} mm", "< 5 mm", diff2 < 5.0),
            ]
            store("slice_position", rows)
            st.markdown("### Results"); render_table(rows)

        if "slice_position" in st.session_state.qa_results:
            st.markdown("### Results (last run)")
            render_table(st.session_state.qa_results["slice_position"]["measurements"])


# ══════════════════════════════════════════════════════════════════════════
#  SLICE THICKNESS  -  SliceThicknessFWHM.compute()
# ══════════════════════════════════════════════════════════════════════════
elif "Slice Thickness" in page:
    st.markdown("## Slice Thickness (FWHM)")
    st.markdown(f'<div style="{INFO_BOX}">ACR Criterion: 5 ± 0.7 mm (4.3 – 5.7 mm). Uses slice 1 '
                'from the active series, detected automatically.</div>', unsafe_allow_html=True)

    study = require_study()
    if study:
        active_series_caption(study)
        series = study["series"]
        s1_path = dicom_loader.get_instance_path(series, study["selected_uid"], 1)
        missing = [n for n, p in [("Slice 1", s1_path)] if not p]
        missing_warning(missing)

        if st.button("▶  Run Slice Thickness", disabled=bool(missing)):
            try:
                with st.spinner("Computing FWHM…"):
                    results, figs = SliceThicknessFWHM.compute(s1_path)
                if results is None:
                    st.error("Could not compute slice thickness — check the DICOM file.")
                else:
                    st_mm = results["slice_thickness"]
                    rows  = [("Slice Thickness (FWHM)", f"{st_mm:.2f} mm", "4.3 – 5.7 mm", 4.3 <= st_mm <= 5.7)]
                    store("slice_thickness", rows)
                    st.markdown("### Results"); render_table(rows)
                    st.markdown("### Images")
                    for fig in figs:
                        st.pyplot(fig); plt.close(fig)
            except Exception as e:
                st.error(f"Error: {e}")

        if "slice_thickness" in st.session_state.qa_results:
            st.markdown("### Results (last run)")
            render_table(st.session_state.qa_results["slice_thickness"]["measurements"])


# ══════════════════════════════════════════════════════════════════════════
#  UNIFORMITY  -  Uniformity.compute()
# ══════════════════════════════════════════════════════════════════════════
elif "Uniformity" in page:
    st.markdown("## Image Intensity Uniformity")
    st.markdown(f'<div style="{INFO_BOX}">ACR Criterion: Percent Integral Uniformity (PIU) ≥ 87.5 %. '
                'Uses slice 7 from the active series, detected automatically.</div>', unsafe_allow_html=True)

    study = require_study()
    if study:
        active_series_caption(study)
        series = study["series"]
        s7_path = dicom_loader.get_instance_path(series, study["selected_uid"], 7)
        missing = [n for n, p in [("Slice 7", s7_path)] if not p]
        missing_warning(missing)

        if st.button("▶  Run Uniformity", disabled=bool(missing)):
            try:
                with st.spinner("Computing PIU…"):
                    results, fig = Uniformity.compute(s7_path)
                if results is None:
                    st.error("Could not compute uniformity — check the DICOM file.")
                else:
                    PIU  = results["PIU"]
                    rows = [("Percent Integral Uniformity (PIU)", f"{PIU:.2f} %", "≥ 87.5 %", PIU >= 87.5)]
                    store("uniformity", rows)
                    st.markdown("### Results"); render_table(rows)
                    if fig: st.pyplot(fig); plt.close(fig)
            except Exception as e:
                st.error(f"Error: {e}")

        if "uniformity" in st.session_state.qa_results:
            st.markdown("### Results (last run)")
            render_table(st.session_state.qa_results["uniformity"]["measurements"])


# ══════════════════════════════════════════════════════════════════════════
#  SNR  -  SNR.compute()
# ══════════════════════════════════════════════════════════════════════════
elif "Signal-to-Noise" in page:
    st.markdown("## Signal-to-Noise Ratio (SNR)")
    st.markdown(f'<div style="{INFO_BOX}">NEMA formula: SNR = 0.655 × (Signal / Noise SD). Uses slice 7 '
                'from the active series, detected automatically. ACR compares against a site-specific '
                'baseline — enter yours below for pass/fail.</div>', unsafe_allow_html=True)

    study = require_study()
    if study:
        active_series_caption(study)
        series = study["series"]
        s7_path = dicom_loader.get_instance_path(series, study["selected_uid"], 7)
        missing = [n for n, p in [("Slice 7", s7_path)] if not p]
        missing_warning(missing)

        baseline = st.number_input("Site baseline SNR (leave 0 to skip pass/fail)", min_value=0.0, step=1.0)

        if st.button("▶  Run SNR", disabled=bool(missing)):
            try:
                with st.spinner("Computing SNR…"):
                    results, fig = SNR.compute(s7_path)
                if results is None:
                    st.error("Could not compute SNR — check the DICOM file.")
                else:
                    snr = results["snr"]
                    if baseline > 0:
                        passed = snr >= baseline * 0.90
                        rng    = f"≥ {baseline*0.90:.1f}  (90 % of {baseline:.1f} baseline)"
                    else:
                        passed = None
                        rng    = "Site-specific"
                    rows = [("Signal-to-Noise Ratio (NEMA)", f"{snr:.2f}", rng, passed)]
                    store("snr", rows)
                    st.markdown("### Results"); render_table(rows)
                    if fig: st.pyplot(fig); plt.close(fig)
            except Exception as e:
                st.error(f"Error: {e}")

        if "snr" in st.session_state.qa_results:
            st.markdown("### Results (last run)")
            render_table(st.session_state.qa_results["snr"]["measurements"])


# ══════════════════════════════════════════════════════════════════════════
#  GHOSTING  -  Percent_Signal_Ghosting.compute()
# ══════════════════════════════════════════════════════════════════════════
elif "Ghosting" in page:
    st.markdown("## Percent Signal Ghosting")
    st.markdown(f'<div style="{INFO_BOX}">ACR T1 series only. ACR Criterion: ghosting ratio < 2.5 %. '
                'Uses slice 7 from the active series, detected automatically.</div>', unsafe_allow_html=True)

    study = require_study()
    if study:
        active_series_caption(study)
        series = study["series"]
        sel_uid = study["selected_uid"]
        if sel_uid and "T1" not in series.get(sel_uid, {}).get("description", "").upper():
            st.markdown(f'<div style="{WARN_BOX}">The active series description does not obviously '
                        'mention T1. Ghosting is an ACR T1-only test — double check this is the right '
                        'series before trusting the result.</div>', unsafe_allow_html=True)

        s7_path = dicom_loader.get_instance_path(series, sel_uid, 7)
        missing = [n for n, p in [("Slice 7", s7_path)] if not p]
        missing_warning(missing)

        if st.button("▶  Run Ghosting Analysis", disabled=bool(missing)):
            try:
                with st.spinner("Computing ghosting ratio…"):
                    results, fig = Percent_Signal_Ghosting.compute(s7_path)
                if results is None:
                    st.error("Could not compute ghosting — check the DICOM file.")
                else:
                    ratio = results["ghosting_ratio"]
                    pct   = ratio * 100
                    rows  = [("Percent Signal Ghosting", f"{pct:.4f} %", "< 2.5 %", pct < 2.5)]
                    store("ghosting", rows)
                    st.markdown("### Results"); render_table(rows)
                    if fig: st.pyplot(fig); plt.close(fig)
            except Exception as e:
                st.error(f"Error: {e}")

        if "ghosting" in st.session_state.qa_results:
            st.markdown("### Results (last run)")
            render_table(st.session_state.qa_results["ghosting"]["measurements"])


# ══════════════════════════════════════════════════════════════════════════
#  LOW CONTRAST  -  Low_Contrast_Detectability.get_slice_image()
# ══════════════════════════════════════════════════════════════════════════
elif "Low Contrast" in page:
    st.markdown("## Low Contrast Detectability")
    st.markdown(f'<div style="{INFO_BOX}">Uses slices 8–11 from the active series, detected '
                'automatically. Count the fully resolved spokes on each low-contrast insert, then '
                'enter the counts below.</div>', unsafe_allow_html=True)

    study = require_study()
    if study:
        active_series_caption(study)
        series = study["series"]
        slice_nums  = [11, 10, 9, 8]
        slice_paths = {sl: dicom_loader.get_instance_path(series, study["selected_uid"], sl) for sl in slice_nums}
        missing = [f"Slice {sl}" for sl, p in slice_paths.items() if not p]
        missing_warning(missing)

        found = {sl: p for sl, p in slice_paths.items() if p}
        if found:
            st.markdown("### Images")
            img_cols = st.columns(len(found))
            for i, (sl, path) in enumerate(found.items()):
                fig = Low_Contrast_Detectability.get_slice_image(path)
                with img_cols[i]:
                    st.pyplot(fig); plt.close(fig)

        st.markdown("---")
        st.markdown("**Count fully resolved spokes for each insert:**")
        cnt_cols   = st.columns(4)
        spoke_cnt  = {}
        for i, sl in enumerate(slice_nums):
            with cnt_cols[i]:
                spoke_cnt[sl] = st.number_input(f"Slice {sl}", min_value=0, max_value=40, step=1,
                                                 key=f"lcd_cnt_{sl}", disabled=sl not in found)

        if st.button("▶  Record Low Contrast Results", disabled=bool(missing)):
            total = sum(spoke_cnt.values())
            rows  = [(f"Slice {sl} — Spokes Resolved", str(spoke_cnt[sl]), "≥ 9", spoke_cnt[sl] >= 9)
                     for sl in slice_nums]
            rows.append(("Total Spokes Resolved", str(total), "≥ 37", total >= 37))
            store("low_contrast", rows)
            st.markdown("### Results"); render_table(rows)

        if "low_contrast" in st.session_state.qa_results:
            st.markdown("### Results (last run)")
            render_table(st.session_state.qa_results["low_contrast"]["measurements"])


# ══════════════════════════════════════════════════════════════════════════
#  HIGH CONTRAST  -  High_Contrast_Spatial_Res.get_insert_image()
# ══════════════════════════════════════════════════════════════════════════
elif "High Contrast" in page:
    st.markdown("## High Contrast Spatial Resolution")
    st.markdown(f'<div style="{INFO_BOX}">Uses slice 1 from the active series, detected automatically. '
                'Examine the magnified spatial resolution insert — upper-left array = <b>horizontal</b>, '
                'lower-right = <b>vertical</b>. Enter the smallest hole size you can fully resolve.</div>',
                unsafe_allow_html=True)

    study = require_study()
    if study:
        active_series_caption(study)
        series = study["series"]
        s1_path = dicom_loader.get_instance_path(series, study["selected_uid"], 1)
        missing = [n for n, p in [("Slice 1", s1_path)] if not p]
        missing_warning(missing)

        if s1_path:
            fig = High_Contrast_Spatial_Res.get_insert_image(s1_path)
            st.pyplot(fig); plt.close(fig)

        st.markdown("---")
        st.markdown("**Enter the smallest resolved hole size** (e.g. 1.0, 1.1, 1.25 mm):")
        h_col, v_col = st.columns(2)
        with h_col: horiz = st.number_input("Horizontal resolution (mm)", min_value=0.5, max_value=5.0, step=0.05, value=1.0, key="hcsr_h")
        with v_col: vert  = st.number_input("Vertical resolution (mm)",   min_value=0.5, max_value=5.0, step=0.05, value=1.0, key="hcsr_v")

        if st.button("▶  Record Spatial Resolution Results", disabled=bool(missing)):
            rows = [
                ("Horizontal Resolution", f"{horiz:.2f} mm", "≤ 1.0 mm", horiz <= 1.0),
                ("Vertical Resolution",   f"{vert:.2f} mm",  "≤ 1.0 mm", vert  <= 1.0),
            ]
            store("high_contrast", rows)
            st.markdown("### Results"); render_table(rows)

        if "high_contrast" in st.session_state.qa_results:
            st.markdown("### Results (last run)")
            render_table(st.session_state.qa_results["high_contrast"]["measurements"])
