# Validación de Artículos UAM-A

App Streamlit para que investigadores validen las categorías arXiv
asignadas automáticamente a sus artículos.

## Estructura del repositorio

```
├── app.py
├── requirements.txt
├── zeroshot_predictions_uam.parquet
└── .streamlit/
    └── secrets.toml          ← solo para pruebas locales, NO subir a GitHub
```

## Configuración local

1. Instala dependencias:
   ```bash
   pip install -r requirements.txt
   ```

2. Crea `.streamlit/secrets.toml` con tus credenciales de Google:
   ```toml
   [gcp_service_account]
   type = "service_account"
   project_id = "tu-proyecto"
   private_key_id = "..."
   private_key = "-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----\n"
   client_email = "tu-service-account@tu-proyecto.iam.gserviceaccount.com"
   client_id = "..."
   auth_uri = "https://accounts.google.com/o/oauth2/auth"
   token_uri = "https://oauth2.googleapis.com/token"
   ```

3. Ejecuta:
   ```bash
   streamlit run app.py
   ```

## Despliegue en Streamlit Community Cloud

1. Sube este repositorio a GitHub (sin el archivo `secrets.toml`)
2. Ve a [share.streamlit.io](https://share.streamlit.io) y conecta el repo
3. En **Settings → Secrets** pega el contenido de tu `secrets.toml`
4. Despliega — la URL pública estará lista en ~2 minutos

## Google Sheets esperado

La hoja debe llamarse `etiquetas_uam` y tener estos encabezados en la fila 1:

| paper_id | autor | titulo | pred_zeroshot | etiqueta_experto | timestamp |

Comparte la hoja con el `client_email` de tu Service Account (permisos de Editor).

## Flujo de la app

```
Bienvenida → selección de investigador → progreso visible
     ↓
Validación → un artículo a la vez → guardar en Google Sheets
     ↓
Cierre → resumen de etiquetas asignadas
```
