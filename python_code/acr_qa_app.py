"""
ACR MRI Phantom: Streamlit Web Interface
=============================================
Run from the same directory as the test modules:
    streamlit run acr_qa_app.py

"""

import sys, os, tempfile
import streamlit as st
import matplotlib
matplotlib.use("Agg")         
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(__file__))

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

def save_tmp(uploaded_file) -> str:
    """Save an UploadedFile to a named temp file; return the path."""
    suffix = os.path.splitext(uploaded_file.name)[-1] or ".dcm"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
        f.write(uploaded_file.read())
        return f.name

def cleanup(*paths):
    for p in paths:
        try:
            os.unlink(p)
        except Exception:
            pass

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
        if passed is True:
            badge = ('<span style="padding:3px 10px;background:#052E16;color:#4ADE80;'
                     'border:1px solid #16A34A;border-radius:4px;font-family:monospace;'
                     'font-size:11px;font-weight:700">&#10003; PASS</span>')
        elif passed is False:
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

# ──────────────────────────────────────────────────────────────────────────
#  Sidebar
# ──────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ACR MRI QA")
    st.caption("American College of Radiology\nPhantom Accreditation Pipeline")
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
            dot = "🟢" if v else ("🔴" if v is False else "⚪")
            st.caption(f"{dot} {label}")


# ══════════════════════════════════════════════════════════════════════════
#  DASHBOARD
# ══════════════════════════════════════════════════════════════════════════
if "Dashboard" in page:
    st.markdown("## ACR MRI Phantom Quality Assurance")
    st.caption("American College of Radiology · Accreditation Pipeline")

    if not res:
        st.markdown(f'<div style="{INFO_BOX}">No tests completed yet. '
                    'Select a test from the sidebar to begin uploading DICOM files.</div>',
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
                    f'<span style="color:#64748B;font-size:12px">Input: {inp}</span><br>'
                    f'<span style="color:#38BDF8;font-size:12px">Criterion: {crit}</span>'
                    f'</div>', unsafe_allow_html=True)
    else:
        st.markdown("### Results Summary")
        all_rows = [m for key in TEST_KEYS if key in res for m in res[key].get("measurements", [])]
        if all_rows:
            render_table(all_rows)


# ══════════════════════════════════════════════════════════════════════════
#  GEOMETRIC ACCURACY  →  test_geom_acc.compute()
# ══════════════════════════════════════════════════════════════════════════
elif "Geometric Accuracy" in page:
    st.markdown("## Geometric Accuracy")
    st.markdown(f'<div style="{INFO_BOX}">ACR T1 series only. '
                'Upload one localizer and slices 1 and 5.</div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1: loc_f = st.file_uploader("Localizer (.dcm)", type=["dcm"], key="ga_loc")
    with c2: s1_f  = st.file_uploader("Slice 1 (.dcm)",   type=["dcm"], key="ga_s1")
    with c3: s5_f  = st.file_uploader("Slice 5 (.dcm)",   type=["dcm"], key="ga_s5")

    if st.button("▶  Run Geometric Accuracy", disabled=not (loc_f and s1_f and s5_f)):
        loc_p = s1_p = s5_p = None
        try:
            with st.spinner("Analysing images…"):
                loc_p = save_tmp(loc_f)
                s1_p  = save_tmp(s1_f)
                s5_p  = save_tmp(s5_f)
                geo, figs = test_geom_acc.compute(loc_p, s1_p, s5_p)

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
        finally:
            cleanup(loc_p, s1_p, s5_p)

    if "geometric" in res and not (loc_f and s1_f and s5_f):
        st.markdown("### Results (last run)"); render_table(res["geometric"]["measurements"])


# ══════════════════════════════════════════════════════════════════════════
#  SLICE POSITION ACCURACY  →  Slice_Position_Accuracy.get_insert_image()
# ══════════════════════════════════════════════════════════════════════════
elif "Slice Position" in page:
    st.markdown("## Slice Position Accuracy")
    st.markdown(f'<div style="{INFO_BOX}">Upload slices 1 and 11. '
                'Examine the zoomed bar inserts, then enter the measured bar length difference for each slice.</div>',
                unsafe_allow_html=True)

    c1, c2, c3 = st.columns([2, 2, 1])
    with c1: s1_f  = st.file_uploader("Slice 1 (.dcm)",  type=["dcm"], key="spa_s1")
    with c2: s11_f = st.file_uploader("Slice 11 (.dcm)", type=["dcm"], key="spa_s11")
    with c3: st.selectbox("Series", ["ACR T1", "ACR T2"], key="spa_ser")

    if s1_f or s11_f:
        ic1, ic2 = st.columns(2)
        for col, uf, label in [(ic1, s1_f, "Slice 1"), (ic2, s11_f, "Slice 11")]:
            if uf:
                p = None
                try:
                    p   = save_tmp(uf)
                    fig = Slice_Position_Accuracy.get_insert_image(p)
                    with col:
                        st.pyplot(fig); plt.close(fig)
                        st.caption(f"{label} — bar position insert")
                finally:
                    cleanup(p)

    st.markdown("**Enter bar length differences** measured from the images above:")
    d1c, d2c = st.columns(2)
    with d1c: diff1 = st.number_input("Slice 1 bar difference (mm)",  min_value=0.0, step=0.1, key="spa_d1")
    with d2c: diff2 = st.number_input("Slice 11 bar difference (mm)", min_value=0.0, step=0.1, key="spa_d2")

    if st.button("▶  Record Results"):
        rows = [
            ("Slice 1 Bar Difference",  f"{diff1:.2f} mm", "< 5 mm", diff1 < 5.0),
            ("Slice 11 Bar Difference", f"{diff2:.2f} mm", "< 5 mm", diff2 < 5.0),
        ]
        store("slice_position", rows)
        st.markdown("### Results"); render_table(rows)

    if "slice_position" in res:
        st.markdown("### Results (last run)"); render_table(res["slice_position"]["measurements"])


# ══════════════════════════════════════════════════════════════════════════
#  SLICE THICKNESS  →  SliceThicknessFWHM.compute()
# ══════════════════════════════════════════════════════════════════════════
elif "Slice Thickness" in page:
    st.markdown("## Slice Thickness (FWHM)")
    st.markdown(f'<div style="{INFO_BOX}">ACR Criterion: 5 ± 0.7 mm (4.3 – 5.7 mm)</div>',
                unsafe_allow_html=True)

    c1, c2 = st.columns([3, 1])
    with c1: s1_f   = st.file_uploader("Slice 1 (.dcm)", type=["dcm"], key="st_s1")
    with c2: st.selectbox("Series", ["ACR T1", "ACR T2"], key="st_ser")

    if st.button(" Run Slice Thickness", disabled=not s1_f):
        p = None
        try:
            with st.spinner("Computing FWHM…"):
                p = save_tmp(s1_f)
                results, figs = SliceThicknessFWHM.compute(p)
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
        finally:
            cleanup(p)

    if "slice_thickness" in res and not s1_f:
        st.markdown("### Results (last run)"); render_table(res["slice_thickness"]["measurements"])


# ══════════════════════════════════════════════════════════════════════════
#  UNIFORMITY  →  Uniformity.compute()
# ══════════════════════════════════════════════════════════════════════════
elif "Uniformity" in page:
    st.markdown("## Image Intensity Uniformity")
    st.markdown(f'<div style="{INFO_BOX}">ACR Criterion: Percent Integral Uniformity (PIU) ≥ 87.5 %</div>',
                unsafe_allow_html=True)

    c1, c2 = st.columns([3, 1])
    with c1: s7_f   = st.file_uploader("Slice 7 (.dcm)", type=["dcm"], key="uni_s7")
    with c2: st.selectbox("Series", ["ACR T1", "ACR T2"], key="uni_ser")

    if st.button(" Run Uniformity", disabled=not s7_f):
        p = None
        try:
            with st.spinner("Computing PIU…"):
                p = save_tmp(s7_f)
                results, fig = Uniformity.compute(p)
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
        finally:
            cleanup(p)

    if "uniformity" in res and not s7_f:
        st.markdown("### Results (last run)"); render_table(res["uniformity"]["measurements"])


# ══════════════════════════════════════════════════════════════════════════
#  SNR  →  SNR.compute()
# ══════════════════════════════════════════════════════════════════════════
elif "Signal-to-Noise" in page:
    st.markdown("## 📡 Signal-to-Noise Ratio (SNR)")
    st.markdown(f'<div style="{INFO_BOX}">NEMA formula: SNR = 0.655 × (Signal / Noise SD). '
                'ACR compares against a site-specific baseline — enter yours below for pass/fail.</div>',
                unsafe_allow_html=True)

    c1, c2 = st.columns([3, 1])
    with c1: s7_f    = st.file_uploader("Slice 7 (.dcm)", type=["dcm"], key="snr_s7")
    with c2: st.selectbox("Series", ["ACR T1", "ACR T2", "Site T1", "Site T2"], key="snr_ser")
    baseline = st.number_input("Site baseline SNR (leave 0 to skip pass/fail)", min_value=0.0, step=1.0)

    if st.button("▶  Run SNR", disabled=not s7_f):
        p = None
        try:
            with st.spinner("Computing SNR…"):
                p = save_tmp(s7_f)
                results, fig = SNR.compute(p)
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
        finally:
            cleanup(p)

    if "snr" in res and not s7_f:
        st.markdown("### Results (last run)"); render_table(res["snr"]["measurements"])


# ══════════════════════════════════════════════════════════════════════════
#  GHOSTING  →  Percent_Signal_Ghosting.compute()
# ══════════════════════════════════════════════════════════════════════════
elif "Ghosting" in page:
    st.markdown("## Percent Signal Ghosting")
    st.markdown(f'<div style="{INFO_BOX}">ACR T1 series only. '
                'ACR Criterion: ghosting ratio < 2.5 %</div>', unsafe_allow_html=True)

    s7_f = st.file_uploader("Slice 7 (.dcm)", type=["dcm"], key="ghost_s7")

    if st.button(" Run Ghosting Analysis", disabled=not s7_f):
        p = None
        try:
            with st.spinner("Computing ghosting ratio…"):
                p = save_tmp(s7_f)
                results, fig = Percent_Signal_Ghosting.compute(p)
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
        finally:
            cleanup(p)

    if "ghosting" in res and not s7_f:
        st.markdown("### Results (last run)"); render_table(res["ghosting"]["measurements"])


# ══════════════════════════════════════════════════════════════════════════
#  LOW CONTRAST  →  Low_Contrast_Detectability.get_slice_image()
# ══════════════════════════════════════════════════════════════════════════
elif "Low Contrast" in page:
    st.markdown("## Low Contrast Detectability")
    st.markdown(f'<div style="{INFO_BOX}">Upload slices 8–11. '
                'Count the fully resolved spokes on each low-contrast insert, then enter the counts below.</div>',
                unsafe_allow_html=True)

    st.selectbox("Series", ["ACR T1", "ACR T2", "Site T1", "Site T2"], key="lcd_ser")

    slice_nums  = [11, 10, 9, 8]
    up_cols     = st.columns(4)
    slice_files = {}
    for i, sl in enumerate(slice_nums):
        with up_cols[i]:
            f = st.file_uploader(f"Slice {sl} (.dcm)", type=["dcm"], key=f"lcd_s{sl}")
            if f:
                slice_files[sl] = f

    if slice_files:
        st.markdown("### Images")
        img_cols = st.columns(len(slice_files))
        for i, (sl, uf) in enumerate(slice_files.items()):
            p = None
            try:
                p   = save_tmp(uf)
                fig = Low_Contrast_Detectability.get_slice_image(p)
                with img_cols[i]:
                    st.pyplot(fig); plt.close(fig)
            finally:
                cleanup(p)

    st.markdown("---")
    st.markdown("**Count fully resolved spokes for each insert:**")
    cnt_cols   = st.columns(4)
    spoke_cnt  = {}
    for i, sl in enumerate(slice_nums):
        with cnt_cols[i]:
            spoke_cnt[sl] = st.number_input(f"Slice {sl}", min_value=0, max_value=40, step=1, key=f"lcd_cnt_{sl}")

    if st.button("▶  Record Low Contrast Results"):
        total = sum(spoke_cnt.values())
        rows  = [(f"Slice {sl} — Spokes Resolved", str(spoke_cnt[sl]), "≥ 9", spoke_cnt[sl] >= 9)
                 for sl in slice_nums]
        rows.append(("Total Spokes Resolved", str(total), "≥ 37", total >= 37))
        store("low_contrast", rows)
        st.markdown("### Results"); render_table(rows)

    if "low_contrast" in res:
        st.markdown("### Results (last run)"); render_table(res["low_contrast"]["measurements"])


# ══════════════════════════════════════════════════════════════════════════
#  HIGH CONTRAST  →  High_Contrast_Spatial_Res.get_insert_image()
# ══════════════════════════════════════════════════════════════════════════
elif "High Contrast" in page:
    st.markdown("## High Contrast Spatial Resolution")
    st.markdown(f'<div style="{INFO_BOX}">Upload slice 1. Examine the magnified spatial resolution insert — '
                'upper-left array = <b>horizontal</b>, lower-right = <b>vertical</b>. '
                'Enter the smallest hole size you can fully resolve.</div>', unsafe_allow_html=True)

    c1, c2 = st.columns([3, 1])
    with c1: s1_f   = st.file_uploader("Slice 1 (.dcm)", type=["dcm"], key="hcsr_s1")
    with c2: st.selectbox("Series", ["ACR T1", "ACR T2"], key="hcsr_ser")

    if s1_f:
        p = None
        try:
            p   = save_tmp(s1_f)
            fig = High_Contrast_Spatial_Res.get_insert_image(p)
            st.pyplot(fig); plt.close(fig)
        finally:
            cleanup(p)

    st.markdown("---")
    st.markdown("**Enter the smallest resolved hole size** (e.g. 1.0, 1.1, 1.25 mm):")
    h_col, v_col = st.columns(2)
    with h_col: horiz = st.number_input("Horizontal resolution (mm)", min_value=0.5, max_value=5.0, step=0.05, value=1.0, key="hcsr_h")
    with v_col: vert  = st.number_input("Vertical resolution (mm)",   min_value=0.5, max_value=5.0, step=0.05, value=1.0, key="hcsr_v")

    if st.button(" Record Spatial Resolution Results"):
        rows = [
            ("Horizontal Resolution", f"{horiz:.2f} mm", "≤ 1.0 mm", horiz <= 1.0),
            ("Vertical Resolution",   f"{vert:.2f} mm",  "≤ 1.0 mm", vert  <= 1.0),
        ]
        store("high_contrast", rows)
        st.markdown("### Results"); render_table(rows)

    if "high_contrast" in res:
        st.markdown("### Results (last run)"); render_table(res["high_contrast"]["measurements"])
