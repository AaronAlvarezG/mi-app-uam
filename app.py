import streamlit as st
import pandas as pd
import os

# --- CONFIGURACIÓN ---
# Archivos de entrada y salida
INPUT_FILE = "zeroshot_predictions_uam.parquet"
OUTPUT_FILE = "uam_a_etiquetado_final_expertos.parquet"

# Taxonomía permitida con descripciones completas
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
    "cs.SY": "Systems and Control"
}

# Función auxiliar para formatear la visualización (Código - Descripción)
def format_category(code):
    # Si el código no está en nuestro diccionario base (porque es uno nuevo ingresado por el usuario),
    # intentamos mantener el formato, o devolvemos solo el código si no hay descripción conocida.
    desc = CATEGORIES.get(code, "Categoria definida por usuario")
    return f"{code} - {desc}"

# --- FUNCIONES DE CARGA Y GUARDADO ---

@st.cache_data(ttl=60)
def load_data():
    """
    Carga el dataset original y aplica las etiquetas experto existentes
    del archivo de salida si este ya existe.
    """
    if not os.path.exists(INPUT_FILE):
        st.error(f"No se encontró el archivo de entrada: {INPUT_FILE}")
        return None

    df = pd.read_parquet(INPUT_FILE)
    
    if 'etiqueta_experto' not in df.columns:
        df['etiqueta_experto'] = None

    if os.path.exists(OUTPUT_FILE):
        try:
            df_saved = pd.read_parquet(OUTPUT_FILE)
            if 'etiqueta_experto' in df_saved.columns:
                df['etiqueta_experto'].update(df_saved['etiqueta_experto'])
        except Exception as e:
            st.warning(f"Error leyendo guardado previo: {e}")

    return df

def save_progress(df):
    """
    Guarda el estado actual del dataframe.
    """
    try:
        df.to_parquet(OUTPUT_FILE, index=True)
        return True
    except Exception as e:
        st.error(f"Error al guardar el progreso: {e}")
        return False

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Validacion de Articulos UAM-A",
    page_icon=":hat:",
    layout="wide"
)

st.title("Validacion de Clasificacion de Articulos")
st.markdown("""
Herramienta para que los investigadores validen las categorias asignadas automaticamente a sus articulos.
Seleccione su nombre para comenzar.
""")

# --- LÓGICA PRINCIPAL ---

df_main = load_data()

if df_main is not None:
    # 1. Sidebar: Selección de Usuario
    st.sidebar.header("Identificacion")
    
    authors = sorted(df_main['autor'].dropna().unique())
    
    if 'selected_author' not in st.session_state:
        st.session_state.selected_author = authors[0] if authors else None

    selected_author = st.sidebar.selectbox(
        "Seleccione su nombre:",
        options=authors,
        index=authors.index(st.session_state.selected_author) if st.session_state.selected_author in authors else 0,
        key="author_selector"
    )
    
    if selected_author != st.session_state.selected_author:
        st.session_state.selected_author = selected_author
        st.session_state.current_paper_idx = 0
        st.rerun()

    # 2. Filtrar datos del autor
    author_data = df_main[df_main['autor'] == selected_author].copy()
    
    labeled_papers = author_data[author_data['etiqueta_experto'].notna()]
    unlabeled_papers = author_data[author_data['etiqueta_experto'].isna()]

    total_papers = len(author_data)
    labeled_count = len(labeled_papers)
    progress_percent = (labeled_count / total_papers) * 100 if total_papers > 0 else 100

    # Mostrar progreso en Sidebar
    st.sidebar.markdown("---")
    st.sidebar.subheader("Tu Progreso")
    st.sidebar.metric("Articulos Revisados", f"{labeled_count} / {total_papers}")
    st.sidebar.progress(progress_percent / 100)
    
    if st.sidebar.button("Cerrar Sesion / Cambiar Usuario"):
        st.session_state.selected_author = None
        st.rerun()

    # 3. Interfaz de Validación
    if len(unlabeled_papers) == 0:
        st.success(f"Felicidades {selected_author}. Ha revisado todos sus articulos asignados.")
        st.info("No hay mas articulos pendientes de validacion para este perfil.")
    else:
        if 'current_paper_idx' not in st.session_state:
            st.session_state.current_paper_idx = 0
        
        if st.session_state.current_paper_idx >= len(unlabeled_papers):
            st.session_state.current_paper_idx = 0

        current_paper_rel_idx = st.session_state.current_paper_idx
        current_paper_series = unlabeled_papers.iloc[current_paper_rel_idx]
        original_index = current_paper_series.name

        st.markdown(f"### Articulo {current_paper_rel_idx + 1} de {len(unlabeled_papers)} pendientes")

        # --- TARJETA DEL ARTÍCULO ---
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.subheader("Titulo")
            st.write(current_paper_series['titulo'])
            
            with st.expander("Ver Resumen (Abstract)"):
                st.write(current_paper_series['Resumen'])

        with col2:
            st.subheader("Prediccion del Modelo")
            
            # Obtener código y descripción
            pred_code = current_paper_series['pred_zeroshot']
            pred_display = format_category(pred_code)
            
            # Mostrar la predicción completa
            st.markdown(f"<div style='background-color:#f0f2f6;padding:10px;border-radius:5px;text-align:center;font-weight:bold;font-size:1.1em;'>{pred_display}</div>", unsafe_allow_html=True)

        st.markdown("---")

        # --- SECCIÓN DE ACCIÓN ---
        st.subheader("Validacion Experto")

        # Construir opciones para el radio button
        confirm_option = f"Confirmar: {pred_display}"
        
        # Lista completa de categorías con descripción
        cat_options = [format_category(code) for code in CATEGORIES.keys()]
        
        # Nueva opción para agregar categoría personalizada
        custom_option = "Ninguna de las anteriores (Ingresar nueva categoria)"
        
        options = [confirm_option] + cat_options + [custom_option]
        
        selection = st.radio(
            "Seleccione la categoria correcta:",
            options=options,
            index=0,
            label_visibility="collapsed"
        )

        # Campo de entrada condicional para la categoría personalizada
        custom_category_input = ""
        if selection == custom_option:
            custom_category_input = st.text_input(
                "Ingrese la categoria correcta (ej. cs.DB, cs.IR, etc.):", 
                key="custom_cat_input",
                help="Escriba el codigo de la categoria arXiv o una descripcion breve."
            )

        # Botón de Guardar
        col_save, col_skip = st.columns([1, 4])
        with col_save:
            save_button = st.button("Guardar Evaluacion", type="primary", use_container_width=True)
        
        # Lógica al presionar guardar
        if save_button:
            final_label = None
            error = False
            
            if selection == custom_option:
                # Validar que el campo no este vacio
                if not custom_category_input or custom_category_input.strip() == "":
                    st.error("Por favor, escriba la categoria correcta en el campo de texto.")
                    error = True
                else:
                    final_label = custom_category_input.strip()
            
            elif selection.startswith("Confirmar"):
                final_label = pred_code 
            
            else:
                # Es una categoría de la taxonomía (formato "cs.AI - Artificial Intelligence")
                # Extraemos solo la parte antes del guion
                final_label = selection.split(" - ")[0]

            # Si no hay errores, guardamos
            if not error:
                # Actualizar el DataFrame principal
                df_main.loc[original_index, 'etiqueta_experto'] = final_label
                
                # Guardar en disco
                if save_progress(df_main):
                    st.toast("Guardado exitosamente!", icon="✅")
                    
                    # Avanzar al siguiente artículo
                    st.session_state.current_paper_idx += 1
                    
                    if st.session_state.current_paper_idx >= len(unlabeled_papers):
                        st.session_state.current_paper_idx = 0
                    
                    st.rerun()

else:
    st.error("No se pudieron cargar los datos. Verifique que el archivo .parquet exista.")