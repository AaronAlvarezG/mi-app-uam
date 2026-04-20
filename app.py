import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# ─────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────
INPUT_FILE  = "zeroshot_predictions_uam.parquet"
SHEET_NAME  = "etiquetas_uam"
SCOPES      = [
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
    desc = CATEGORIES.get(code, "Categoría definida por usuario")
    return f"{code} — {desc}"

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
    """Devuelve dict {paper_id: etiqueta_experto} desde Google Sheets."""
    try:
        sheet  = get_sheet()
        records = sheet.get_all_records()
        return {str(r["paper_id"]): r["etiqueta_experto"] for r in records if r.get("etiqueta_experto")}
    except Exception as e:
        st.warning(f"No se pudieron cargar etiquetas previas: {e}")
        return {}


def save_label(paper_id, autor, titulo, pred, etiqueta):
    """Inserta o actualiza la fila correspondiente en Google Sheets."""
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
# CARGA DE DATOS
# ─────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_parquet(INPUT_FILE)
    if "etiqueta_experto" not in df.columns:
        df["etiqueta_experto"] = None
    return df


def apply_saved_labels(df, saved):
    """Fusiona etiquetas de Sheets en el DataFrame en memoria."""
    for pid, label in saved.items():
        try:
            df.loc[int(pid), "etiqueta_experto"] = label
        except Exception:
            pass
    return df

# ─────────────────────────────────────────
# ESTILOS GLOBALES
# ─────────────────────────────────────────
def inject_css():
    st.markdown("""
    <style>
    /* Fuente y fondo general */
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600&family=IBM+Plex+Mono&display=swap');
    html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }

    /* Ocultar menú hamburguesa y footer de Streamlit */
    #MainMenu {visibility: hidden;}
    footer     {visibility: hidden;}
    header     {visibility: hidden;}

    /* Contenedor principal más angosto y centrado */
    .block-container {
        max-width: 820px;
        padding-top: 2.5rem;
        padding-bottom: 3rem;
    }

    /* Tarjeta artículo */
    .paper-card {
        background: #FAFAF9;
        border: 1px solid #E5E3DE;
        border-radius: 12px;
        padding: 1.4rem 1.6rem;
        margin-bottom: 1rem;
    }

    /* Pill de predicción */
    .pred-pill {
        display: inline-block;
        background: #EAF3DE;
        color: #27500A;
        font-size: 0.82rem;
        font-weight: 500;
        padding: 4px 14px;
        border-radius: 20px;
        font-family: 'IBM Plex Mono', monospace;
        letter-spacing: .02em;
    }

    /* Barra de progreso custom */
    .prog-bar-bg {
        background: #E5E3DE;
        border-radius: 6px;
        height: 8px;
        width: 100%;
        margin: 6px 0 2px;
    }
    .prog-bar-fill {
        background: #1D9E75;
        border-radius: 6px;
        height: 8px;
        transition: width .4s ease;
    }

    /* Encabezado de sección */
    .section-head {
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: .08em;
        text-transform: uppercase;
        color: #888780;
        margin-bottom: .4rem;
    }

    /* Número grande de progreso */
    .big-number {
        font-size: 2.6rem;
        font-weight: 300;
        color: #1D9E75;
        line-height: 1;
    }

    /* Tarjeta de artículo en lista de progreso */
    .list-card {
        border-left: 3px solid #E5E3DE;
        padding: 6px 12px;
        margin-bottom: 6px;
        font-size: 0.88rem;
        color: #5F5E5A;
    }
    .list-card.done {
        border-left-color: #1D9E75;
        color: #085041;
    }

    /* Botón primario */
    div[data-testid="stButton"] button[kind="primary"] {
        background: #1D1C1A;
        color: #FAFAF9;
        border: none;
        border-radius: 8px;
        font-family: 'IBM Plex Sans', sans-serif;
        font-weight: 500;
        padding: .55rem 1.6rem;
        transition: background .15s;
    }
    div[data-testid="stButton"] button[kind="primary"]:hover {
        background: #3a3836;
    }

    /* Radio buttons más espaciados */
    div[data-testid="stRadio"] label {
        font-size: 0.9rem;
        padding: 4px 0;
    }

    /* Toast de éxito */
    .toast-ok {
        background: #E1F5EE;
        color: #085041;
        border-radius: 8px;
        padding: 10px 16px;
        font-size: 0.88rem;
        font-weight: 500;
        margin-top: .5rem;
    }
    </style>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────
# PANTALLAS
# ─────────────────────────────────────────

def screen_welcome(df):
    """Pantalla 1: selección de investigador."""
    st.markdown("## Validación de Artículos · UAM-A")
    st.markdown(
        "Bienvenido. Seleccione su nombre para revisar y validar "
        "las categorías asignadas automáticamente a sus artículos.",
        help=None,
    )
    st.markdown("---")

    authors = sorted(df["autor"].dropna().unique())
    author  = st.selectbox("Investigador", options=["— seleccione —"] + list(authors), label_visibility="collapsed")

    if author == "— seleccione —":
        st.caption("↑ Elija su nombre para continuar")
        return

    author_df = df[df["autor"] == author]
    total     = len(author_df)
    done      = author_df["etiqueta_experto"].notna().sum()

    col1, col2 = st.columns([1, 2])
    with col1:
        pct = int(done / total * 100) if total else 100
        st.markdown(f'<div class="big-number">{pct}%</div>', unsafe_allow_html=True)
        st.caption(f"{done} de {total} artículos revisados")
        bar = f'<div class="prog-bar-bg"><div class="prog-bar-fill" style="width:{pct}%"></div></div>'
        st.markdown(bar, unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="section-head">Tus artículos</div>', unsafe_allow_html=True)
        for _, row in author_df.iterrows():
            css = "list-card done" if pd.notna(row["etiqueta_experto"]) else "list-card"
            mark = "✓ " if pd.notna(row["etiqueta_experto"]) else ""
            st.markdown(f'<div class="{css}">{mark}{row["titulo"][:80]}{"…" if len(row["titulo"])>80 else ""}</div>', unsafe_allow_html=True)

    st.markdown("")
    col_a, col_b = st.columns([1, 3])
    with col_a:
        if done == total:
            if st.button("Ver resumen", type="primary", use_container_width=True):
                st.session_state.author  = author
                st.session_state.screen  = "done"
                st.rerun()
        else:
            if st.button("Comenzar revisión →", type="primary", use_container_width=True):
                st.session_state.author      = author
                st.session_state.paper_idx   = 0
                st.session_state.screen      = "validate"
                st.rerun()


def screen_validate(df):
    """Pantalla 2: validación artículo por artículo."""
    author       = st.session_state.author
    author_df    = df[df["autor"] == author].copy()
    pending      = author_df[author_df["etiqueta_experto"].isna()]
    total_author = len(author_df)
    done_count   = total_author - len(pending)

    if len(pending) == 0:
        st.session_state.screen = "done"
        st.rerun()
        return

    idx = st.session_state.get("paper_idx", 0)
    if idx >= len(pending):
        idx = 0
        st.session_state.paper_idx = 0

    paper        = pending.iloc[idx]
    original_idx = paper.name
    pred_code    = paper["pred_zeroshot"]

    # ── Encabezado ──
    col_left, col_right = st.columns([3, 1])
    with col_left:
        st.markdown(f"**{author}**")
        pct = int(done_count / total_author * 100)
        bar = f'<div class="prog-bar-bg"><div class="prog-bar-fill" style="width:{pct}%"></div></div>'
        st.markdown(bar, unsafe_allow_html=True)
        st.caption(f"{done_count} de {total_author} revisados · artículo {idx+1} de {len(pending)} pendientes")
    with col_right:
        if st.button("‹ Cambiar usuario", use_container_width=True):
            st.session_state.screen = "welcome"
            st.rerun()

    st.markdown("---")

    # ── Tarjeta del artículo ──
    st.markdown(f'<div class="paper-card">'
                f'<div class="section-head">Título</div>'
                f'<p style="font-size:1.05rem;font-weight:500;margin:4px 0 12px">{paper["titulo"]}</p>'
                f'<div class="section-head">Predicción del modelo</div>'
                f'<span class="pred-pill">{fmt(pred_code)}</span>'
                f'</div>', unsafe_allow_html=True)

    with st.expander("Ver resumen (abstract)"):
        st.write(paper["Resumen"])

    st.markdown("---")
    st.markdown('<div class="section-head">Seleccione la categoría correcta</div>', unsafe_allow_html=True)

    confirm_label = f"✓  Confirmar: {fmt(pred_code)}"
    other_labels  = [fmt(c) for c in CATEGORIES if c != pred_code]
    custom_label  = "Ninguna de las anteriores — ingresar nueva categoría"
    options       = [confirm_label] + other_labels + [custom_label]

    selection = st.radio("Categoría", options=options, label_visibility="collapsed")

    custom_input = ""
    if selection == custom_label:
        custom_input = st.text_input("Código de categoría arXiv (ej. cs.DB, cs.IR):", key="custom_input")

    st.markdown("")
    col_save, col_skip, _ = st.columns([1.2, 1, 3])

    with col_save:
        save_clicked = st.button("Guardar →", type="primary", use_container_width=True)
    with col_skip:
        if idx + 1 < len(pending):
            if st.button("Saltar", use_container_width=True):
                st.session_state.paper_idx += 1
                st.rerun()

    if save_clicked:
        if selection == custom_label:
            if not custom_input.strip():
                st.error("Escriba el código de categoría antes de guardar.")
                return
            final_label = custom_input.strip()
        elif selection.startswith("✓"):
            final_label = pred_code
        else:
            final_label = selection.split(" — ")[0]

        ok = save_label(
            paper_id=original_idx,
            autor=author,
            titulo=paper["titulo"],
            pred=pred_code,
            etiqueta=final_label,
        )
        if ok:
            df.loc[original_idx, "etiqueta_experto"] = final_label
            st.markdown('<div class="toast-ok">Guardado correctamente.</div>', unsafe_allow_html=True)
            st.session_state.paper_idx = idx  # pending se reduce, idx sigue apuntando al siguiente
            st.rerun()


def screen_done(df):
    """Pantalla 3: felicitación al terminar."""
    author    = st.session_state.author
    author_df = df[df["autor"] == author]
    total     = len(author_df)

    st.markdown("## ¡Revisión completada!")
    st.success(f"Ha validado los {total} artículos asignados a su perfil. Muchas gracias por su participación.")

    st.markdown("---")
    st.markdown('<div class="section-head">Resumen de sus etiquetas</div>', unsafe_allow_html=True)

    for _, row in author_df.iterrows():
        etq = row.get("etiqueta_experto", "—")
        match = "✓" if etq == row["pred_zeroshot"] else "✎"
        color = "#085041" if match == "✓" else "#633806"
        st.markdown(
            f'<div class="list-card done" style="display:flex;justify-content:space-between">'
            f'<span>{row["titulo"][:70]}{"…" if len(row["titulo"])>70 else ""}</span>'
            f'<span style="color:{color};font-family:monospace;font-size:.8rem;white-space:nowrap;margin-left:12px">{match} {etq}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("")
    if st.button("‹ Volver al inicio", type="primary"):
        st.session_state.screen = "welcome"
        st.session_state.author = None
        st.rerun()

# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────
def main():
    st.set_page_config(
        page_title="Validación UAM-A",
        page_icon="📄",
        layout="centered",
    )
    inject_css()

    # Inicializar estado de navegación
    if "screen" not in st.session_state:
        st.session_state.screen    = "welcome"
        st.session_state.author    = None
        st.session_state.paper_idx = 0

    # Cargar datos
    try:
        df = load_data()
    except FileNotFoundError:
        st.error(f"No se encontró el archivo: {INPUT_FILE}")
        return

    # Aplicar etiquetas guardadas en Sheets
    saved = load_saved_labels()
    df    = apply_saved_labels(df, saved)

    # Enrutador de pantallas
    screen = st.session_state.screen
    if screen == "welcome":
        screen_welcome(df)
    elif screen == "validate":
        screen_validate(df)
    elif screen == "done":
        screen_done(df)


if __name__ == "__main__":
    main()
