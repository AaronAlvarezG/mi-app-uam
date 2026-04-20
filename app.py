import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# ─────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────
INPUT_FILE = "zeroshot_predictions_uam.parquet"
SHEET_NAME = "etiquetas_uam"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

CATEGORIES = {
    "cs.AI": "Artificial Intelligence",
    "cs.CL": "Computation and Language",
    "cs.CR": "Cryptography and Security",
    "cs.CV": "Computer Vision and Pattern Recognition",
    "cs.DS": "Data Structures and Algorithms",
    "cs.IT": "Information Theory",
    "cs.LG": "Machine Learning",
    "cs.NA": "Numerical Analysis",
    "cs.RO": "Robotics",
    "cs.SY": "Systems and Control",
}

def fmt(code):
    return f"{code} — {CATEGORIES.get(code, 'Categoría definida por usuario')}"

# Descripciones oficiales de arXiv (arxiv.org/category_taxonomy)
CATEGORIES_DESC = {
    "cs.AI": "Covers all areas of AI except Vision, Robotics, Machine Learning, Multiagent Systems, and Computation and Language. Includes Expert Systems, Theorem Proving, Knowledge Representation, Planning, and Uncertainty in AI.",
    "cs.CL": "Covers natural language processing. Includes computational approaches to human language: parsing, generation, machine translation, dialogue, information extraction, and related topics.",
    "cs.CR": "Covers all aspects of cryptography, data security and access control, network security, security protocols, and privacy. Includes both theoretical and applied work.",
    "cs.CV": "Covers image processing, computer vision, pattern recognition, and scene understanding. Includes object detection, image segmentation, 3D vision, video analysis, and visual learning.",
    "cs.DS": "Covers design, analysis, and experimental evaluation of data structures and algorithms. Includes complexity analysis, combinatorial optimization, and graph algorithms.",
    "cs.IT": "Covers theoretical and experimental aspects of information theory and coding. Includes channel capacity, source coding, error-correcting codes, and information-theoretic security.",
    "cs.LG": "Papers on all aspects of machine learning research: supervised, unsupervised, reinforcement learning, bandit problems, robustness, explanation, fairness, and methodology. Also appropriate as primary category for applications of ML methods.",
    "cs.NA": "Covers numerical methods, scientific computing, numerical linear algebra, approximation theory, and mathematical software. Includes error analysis and computational complexity of numerical algorithms.",
    "cs.RO": "Covers robotics: manipulation, locomotion, sensors, perception, planning, control, learning, and human-robot interaction. Includes both theoretical and applied work on autonomous systems.",
    "cs.SY": "Covers control theory and engineering, dynamical systems, stability analysis, optimization, and their applications. Includes networked control, hybrid systems, and real-time systems.",
}

# ─────────────────────────────────────────
# GOOGLE SHEETS
# ─────────────────────────────────────────
@st.cache_resource
def get_sheet():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=SCOPES
    )
    client = gspread.authorize(creds)
    return client.open(SHEET_NAME).sheet1


def load_saved_labels():
    try:
        records = get_sheet().get_all_records()
        return {str(r["paper_id"]): r["etiqueta_experto"] for r in records if r.get("etiqueta_experto")}
    except Exception as e:
        st.warning(f"No se pudieron cargar etiquetas previas: {e}")
        return {}


def save_label(paper_id, autor, titulo, pred, etiqueta):
    try:
        sheet     = get_sheet()
        ids       = sheet.col_values(1)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row       = [str(paper_id), autor, titulo, pred, etiqueta, timestamp]
        if str(paper_id) in ids:
            idx = ids.index(str(paper_id)) + 1
            sheet.update(f"A{idx}:F{idx}", [row])
        else:
            sheet.append_row(row)
        return True
    except Exception as e:
        st.error(f"Error al guardar: {e}")
        return False

# ─────────────────────────────────────────
# DATOS
# ─────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_parquet(INPUT_FILE)
    if "etiqueta_experto" not in df.columns:
        df["etiqueta_experto"] = None
    return df


def apply_saved_labels(df, saved):
    for pid, label in saved.items():
        try:
            df.loc[int(pid), "etiqueta_experto"] = label
        except Exception:
            pass
    return df

# ─────────────────────────────────────────
# CSS
# ─────────────────────────────────────────
def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600&family=IBM+Plex+Mono&display=swap');
    html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }
    #MainMenu {visibility:hidden;} footer {visibility:hidden;} header {visibility:hidden;}
    .block-container { max-width:1080px; padding-top:1rem !important; padding-bottom:1rem !important; }

    .prog-bg   { background:#E5E3DE; border-radius:6px; height:6px; width:100%; margin:4px 0; }
    .prog-fill { background:#1D9E75; border-radius:6px; height:6px; }

    .sec { font-size:.68rem; font-weight:600; letter-spacing:.09em; text-transform:uppercase;
           color:#888780; margin-bottom:4px; margin-top:2px; }

    .pill      { display:inline-block; background:#EAF3DE; color:#27500A; font-size:.76rem;
                 font-weight:500; padding:3px 11px; border-radius:20px;
                 font-family:'IBM Plex Mono',monospace; }
    .pill-warn { background:#FAEEDA; color:#633806; }

    .paper-card { background:#FAFAF9; border:1px solid #E5E3DE; border-radius:10px;
                  padding:.9rem 1.1rem; margin-bottom:.5rem; }

    /* Botones laterales de artículos */
    div[data-testid="stButton"] button {
        text-align:left; white-space:normal; word-break:break-word;
        font-size:.8rem; line-height:1.3; padding:5px 8px;
    }

    /* Botón primario */
    div[data-testid="stButton"] button[kind="primary"] {
        background:#1D1C1A; color:#FAFAF9; border:none; border-radius:7px;
        font-family:'IBM Plex Sans',sans-serif; font-weight:500;
        font-size:.85rem; transition:background .15s;
    }
    div[data-testid="stButton"] button[kind="primary"]:hover { background:#3a3836; }

    /* Radio compacto */
    div[data-testid="stRadio"] label { font-size:.83rem; padding:1px 0; }
    div[data-testid="stRadio"] > div { gap:1px !important; }

    /* Tabla admin */
    .admin-row { display:grid; grid-template-columns:1fr 60px 120px 90px;
                 gap:8px; align-items:center; padding:6px 10px;
                 border-bottom:0.5px solid #E5E3DE; font-size:.83rem; }
    .admin-row.head { font-weight:600; font-size:.68rem; text-transform:uppercase;
                      letter-spacing:.06em; color:#888780; }
    .chip-done    { background:#EAF3DE; color:#27500A; border-radius:20px;
                    padding:2px 10px; font-size:.72rem; font-weight:500; text-align:center; display:inline-block; }
    .chip-partial { background:#FAEEDA; color:#633806; border-radius:20px;
                    padding:2px 10px; font-size:.72rem; font-weight:500; text-align:center; display:inline-block; }
    .chip-none    { background:#F1EFE8; color:#888780; border-radius:20px;
                    padding:2px 10px; font-size:.72rem; font-weight:500; text-align:center; display:inline-block; }

    details summary { font-size:.8rem; color:#888780; cursor:pointer; }

    /* Tooltip nativo: mostrar cursor de ayuda sobre opciones de radio */
    div[data-testid="stRadio"] label { cursor:help; }
    </style>
    """, unsafe_allow_html=True)


def prog_bar(pct):
    return f'<div class="prog-bg"><div class="prog-fill" style="width:{pct}%"></div></div>'

# ─────────────────────────────────────────
# PANTALLA 0 — BIENVENIDA
# ─────────────────────────────────────────
def screen_welcome(df):
    h1, h2 = st.columns([4, 1])
    with h1:
        st.markdown("### Validación de Artículos · UAM-A")
    with h2:
        if st.button("Vista general →", use_container_width=True):
            st.session_state.screen = "admin"
            st.rerun()

    st.markdown("Seleccione su nombre para comenzar.")
    authors = sorted(df["autor"].dropna().unique())
    author  = st.selectbox("", options=["— seleccione —"] + list(authors))

    if author == "— seleccione —":
        st.caption("Elija su nombre en la lista para ver su progreso.")
        return

    author_df = df[df["autor"] == author]
    total     = len(author_df)
    done      = int(author_df["etiqueta_experto"].notna().sum())
    pct       = int(done / total * 100) if total else 100

    st.markdown("---")
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        st.markdown(f'<div style="font-size:2rem;font-weight:300;color:#1D9E75;line-height:1">{pct}%</div>', unsafe_allow_html=True)
        st.caption(f"{done} / {total} revisados")
        st.markdown(prog_bar(pct), unsafe_allow_html=True)
    with c2:
        st.metric("Pendientes", total - done)
        st.metric("Completados", done)
    with c3:
        st.markdown('<div class="sec">Tus artículos</div>', unsafe_allow_html=True)
        for _, row in author_df.iterrows():
            if pd.notna(row["etiqueta_experto"]):
                st.markdown(f'<div style="font-size:.8rem;color:#085041;padding:2px 0">✓ {row["titulo"][:72]}{"…" if len(row["titulo"])>72 else ""}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div style="font-size:.8rem;color:#888780;padding:2px 0">○ {row["titulo"][:72]}{"…" if len(row["titulo"])>72 else ""}</div>', unsafe_allow_html=True)

    st.markdown("")
    btn_label = "Ver resumen" if done == total else "Comenzar revisión →"
    target    = "done" if done == total else "validate"
    cb, _ = st.columns([1, 3])
    with cb:
        if st.button(btn_label, type="primary", use_container_width=True):
            st.session_state.author    = author
            st.session_state.paper_idx = 0
            st.session_state.edit_idx  = None
            st.session_state.screen    = target
            st.rerun()

# ─────────────────────────────────────────
# PANTALLA 1 — ADMIN
# ─────────────────────────────────────────
def screen_admin(df):
    h1, h2 = st.columns([4, 1])
    with h1:
        st.markdown("### Avance general · UAM-A")
    with h2:
        if st.button("‹ Volver", use_container_width=True):
            st.session_state.screen = "welcome"
            st.rerun()

    total_p  = len(df)
    total_d  = int(df["etiqueta_experto"].notna().sum())
    glob_pct = int(total_d / total_p * 100) if total_p else 0

    m1, m2, m3 = st.columns(3)
    m1.metric("Total artículos", total_p)
    m2.metric("Validados", total_d)
    m3.metric("Avance global", f"{glob_pct}%")
    st.markdown(prog_bar(glob_pct), unsafe_allow_html=True)
    st.markdown("---")

    st.markdown(
        '<div class="admin-row head">'
        '<span>Investigador</span><span>Arts.</span><span>Progreso</span><span>Estado</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    authors = sorted(df["autor"].dropna().unique())
    for author in authors:
        a_df = df[df["autor"] == author]
        tot  = len(a_df)
        done = int(a_df["etiqueta_experto"].notna().sum())
        pct  = int(done / tot * 100) if tot else 0

        if done == tot:
            chip = '<span class="chip-done">Completo</span>'
        elif done == 0:
            chip = '<span class="chip-none">Sin iniciar</span>'
        else:
            chip = f'<span class="chip-partial">{pct}%</span>'

        bar  = f'<div class="prog-bg" style="margin:0"><div class="prog-fill" style="width:{pct}%"></div></div>'
        st.markdown(
            f'<div class="admin-row"><span>{author}</span>'
            f'<span style="text-align:center">{done}/{tot}</span>'
            f'{bar}{chip}</div>',
            unsafe_allow_html=True,
        )

# ─────────────────────────────────────────
# PANTALLA 2 — VALIDACIÓN
# ─────────────────────────────────────────
def screen_validate(df):
    author    = st.session_state.author
    author_df = df[df["autor"] == author].copy()
    pending   = author_df[author_df["etiqueta_experto"].isna()]
    done_df   = author_df[author_df["etiqueta_experto"].notna()]
    total_a   = len(author_df)
    done_n    = len(done_df)

    # Sin pendientes: si llegamos desde "Corregir etiquetas" mostramos el primer
    # artículo clasificado en modo edición; si no hay ninguno, volvemos a done.
    if len(pending) == 0:
        if len(done_df) == 0:
            st.session_state.screen = "done"
            st.rerun()
            return
        if st.session_state.get("edit_idx") is None:
            st.session_state.edit_idx = done_df.index[0]

    edit_idx = st.session_state.get("edit_idx", None)
    if edit_idx is not None:
        paper        = author_df.loc[edit_idx]
        is_edit_mode = True
    else:
        idx = st.session_state.get("paper_idx", 0)
        if idx >= len(pending):
            idx = 0
            st.session_state.paper_idx = 0
        paper        = pending.iloc[idx]
        is_edit_mode = False

    original_idx = paper.name
    pred_code    = paper["pred_zeroshot"]

    # ── Layout 2 columnas ──
    col_list, col_form = st.columns([1, 2.6], gap="medium")

    # ── LISTA LATERAL ──
    with col_list:
        pct = int(done_n / total_a * 100)
        st.markdown(f'<div style="font-size:.82rem;font-weight:500">{author.split(",")[0]}</div>', unsafe_allow_html=True)
        st.markdown(prog_bar(pct), unsafe_allow_html=True)
        st.markdown(f'<div style="font-size:.7rem;color:#888780;margin-bottom:.5rem">{done_n}/{total_a} revisados</div>', unsafe_allow_html=True)

        st.markdown('<div class="sec">Pendientes</div>', unsafe_allow_html=True)
        for i, (ridx, row) in enumerate(pending.iterrows()):
            active = (not is_edit_mode) and (i == st.session_state.get("paper_idx", 0))
            label  = ("▶ " if active else "") + row["titulo"][:52] + ("…" if len(row["titulo"]) > 52 else "")
            if st.button(label, key=f"p_{ridx}", use_container_width=True):
                st.session_state.paper_idx = i
                st.session_state.edit_idx  = None
                st.rerun()

        if len(done_df) > 0:
            st.markdown('<div class="sec" style="margin-top:.5rem">Clasificados</div>', unsafe_allow_html=True)
            for ridx, row in done_df.iterrows():
                active = is_edit_mode and (ridx == edit_idx)
                label  = ("✎ " if active else "✓ ") + row["titulo"][:52] + ("…" if len(row["titulo"]) > 52 else "")
                if st.button(label, key=f"d_{ridx}", use_container_width=True):
                    st.session_state.edit_idx = ridx
                    st.rerun()

        st.markdown("")
        if st.button("‹ Salir", use_container_width=True):
            st.session_state.screen   = "welcome"
            st.session_state.edit_idx = None
            st.rerun()

    # ── FORMULARIO ──
    with col_form:
        if is_edit_mode:
            st.markdown(
                '<div style="font-size:.7rem;background:#FAEEDA;color:#633806;'
                'border-radius:5px;padding:3px 10px;display:inline-block;margin-bottom:.4rem">'
                '✎ Modo corrección — editando artículo ya clasificado</div>',
                unsafe_allow_html=True,
            )

        cur_etq = paper.get("etiqueta_experto", "")
        st.markdown(
            f'<div class="paper-card">'
            f'<div class="sec">Título</div>'
            f'<p style="font-size:.93rem;font-weight:500;margin:3px 0 8px;line-height:1.35">{paper["titulo"]}</p>'
            f'<div class="sec">Predicción del modelo</div>'
            f'<span class="pill">{fmt(pred_code)}</span>'
            f'{"<span style=margin-left:8px class=pill pill-warn>Actual: " + str(cur_etq) + "</span>" if is_edit_mode and cur_etq else ""}'
            f'</div>',
            unsafe_allow_html=True,
        )

        with st.expander("Ver abstract"):
            st.write(paper["Resumen"])

        # ── Tarjeta de selección de categoría ──
        # Determinar preselección:
        #   modo edición  → etiqueta ya guardada
        #   modo normal   → pred_zeroshot del modelo
        custom_val = "__custom__"
        cat_codes  = list(CATEGORIES.keys())

        if is_edit_mode and pd.notna(cur_etq) and cur_etq:
            preselect = cur_etq
        else:
            preselect = pred_code

        # Opciones del combo: todos los códigos + opción personalizada
        combo_options = cat_codes + [custom_val]
        combo_labels  = {c: f"{c} — {CATEGORIES[c]}" for c in cat_codes}
        combo_labels[custom_val] = "Otra — ingresar código manualmente"

        # default_idx para el selectbox
        if preselect in cat_codes:
            default_idx = cat_codes.index(preselect)
        else:
            default_idx = len(cat_codes)  # personalizada

        # Clave única por artículo para que el estado se inicialice correctamente
        sel_key = f"sel_{original_idx}"
        if sel_key not in st.session_state:
            st.session_state[sel_key] = combo_options[default_idx]

        # Cabecera de la tarjeta: categoría actualmente seleccionada
        sel_code = st.session_state.get(sel_key, combo_options[default_idx])
        if sel_code == custom_val:
            sel_display = "Categoría personalizada"
            sel_desc    = "Ingrese el código arXiv en el campo de texto."
        else:
            sel_display = combo_labels.get(sel_code, sel_code)
            sel_desc    = CATEGORIES_DESC.get(sel_code, "")

        st.markdown(
            f'<div style="background:#FAFAF9;border:1.5px solid #1D9E75;border-radius:10px;padding:.9rem 1.1rem;margin-top:.4rem">'
            f'<div class="sec">Categoría seleccionada</div>'
            f'<div style="font-size:1rem;font-weight:500;color:#1D1C1A;margin:4px 0 2px">{sel_display}</div>'
            f'<div style="font-size:.75rem;color:#5F5E5A;line-height:1.5;min-height:1.2rem">{sel_desc}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # Combo de selección
        selection = st.selectbox(
            "Cambiar categoría",
            options=combo_options,
            format_func=lambda v: combo_labels[v],
            index=combo_options.index(sel_code) if sel_code in combo_options else default_idx,
            label_visibility="collapsed",
            key=sel_key,
        )

        # Campo personalizado (solo si se elige "Otra")
        custom_input = ""
        if selection == custom_val:
            default_custom = str(cur_etq) if (is_edit_mode and cur_etq and cur_etq not in CATEGORIES) else ""
            custom_input = st.text_input("Código arXiv (ej. cs.DB, cs.IR):", value=default_custom, key="custom_in")

        # Botones acción
        ba1, ba2, _ = st.columns([1.3, 1, 2])
        with ba1:
            save_clicked = st.button("Guardar →", type="primary", use_container_width=True)
        with ba2:
            if is_edit_mode:
                if st.button("Cancelar", use_container_width=True):
                    st.session_state.edit_idx = None
                    st.rerun()
            elif st.session_state.get("paper_idx", 0) + 1 < len(pending):
                if st.button("Saltar", use_container_width=True):
                    st.session_state.paper_idx += 1
                    st.rerun()

        if save_clicked:
            if selection == custom_val:
                if not custom_input.strip():
                    st.error("Escriba el código de categoría.")
                    return
                final_label = custom_input.strip()
            else:
                final_label = selection  # directamente el código arXiv (ej. "cs.LG")

            ok = save_label(
                paper_id=original_idx,
                autor=author,
                titulo=paper["titulo"],
                pred=pred_code,
                etiqueta=final_label,
            )
            if ok:
                df.loc[original_idx, "etiqueta_experto"] = final_label
                st.session_state.edit_idx = None
                st.rerun()

# ─────────────────────────────────────────
# PANTALLA 3 — COMPLETADO
# ─────────────────────────────────────────
def screen_done(df):
    author    = st.session_state.author
    author_df = df[df["autor"] == author]
    total     = len(author_df)

    st.markdown("### ¡Revisión completada!")
    st.success(f"Ha validado los {total} artículos asignados. Muchas gracias por su participación.")
    st.markdown("---")

    st.markdown('<div class="sec">Resumen de etiquetas asignadas</div>', unsafe_allow_html=True)
    for _, row in author_df.iterrows():
        etq   = row.get("etiqueta_experto", "—")
        match = etq == row["pred_zeroshot"]
        icon  = "✓" if match else "✎"
        color = "#085041" if match else "#633806"
        st.markdown(
            f'<div style="display:flex;justify-content:space-between;align-items:center;'
            f'padding:5px 8px;border-left:3px solid #1D9E75;margin-bottom:4px;font-size:.82rem">'
            f'<span style="color:#1D1C1A">{row["titulo"][:75]}{"…" if len(row["titulo"])>75 else ""}</span>'
            f'<span style="color:{color};font-family:monospace;font-size:.72rem;white-space:nowrap;margin-left:10px">{icon} {etq}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("")
    c1, c2, _ = st.columns([1, 1.4, 2])
    with c1:
        if st.button("‹ Inicio", type="primary", use_container_width=True):
            st.session_state.screen = "welcome"
            st.session_state.author = None
            st.rerun()
    with c2:
        if st.button("Corregir etiquetas", use_container_width=True):
            st.session_state.screen   = "validate"
            st.session_state.edit_idx = None
            st.rerun()

# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────
def main():
    st.set_page_config(
        page_title="Validación UAM-A",
        page_icon="📄",
        layout="wide",
    )
    inject_css()

    if "screen" not in st.session_state:
        st.session_state.screen    = "welcome"
        st.session_state.author    = None
        st.session_state.paper_idx = 0
        st.session_state.edit_idx  = None

    try:
        df = load_data()
    except FileNotFoundError:
        st.error(f"No se encontró el archivo: {INPUT_FILE}")
        return

    saved = load_saved_labels()
    df    = apply_saved_labels(df, saved)

    screen = st.session_state.screen
    if screen == "welcome":
        screen_welcome(df)
    elif screen == "admin":
        screen_admin(df)
    elif screen == "validate":
        screen_validate(df)
    elif screen == "done":
        screen_done(df)


if __name__ == "__main__":
    main()
