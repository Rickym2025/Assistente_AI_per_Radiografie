# -*- coding: utf-8 -*-

# ==================================================
# IMPORT NECESSARI
# ==================================================
import streamlit as st
from PIL import Image
import google.generativeai as genai
import os
import time
from io import BytesIO
from google.api_core import exceptions
from dotenv import load_dotenv

load_dotenv()

# ==================================================
# CONFIGURAZIONE PAGINA
# ==================================================
st.set_page_config(
    page_title="Assistente AI Radiografie",
    layout="wide"
)

# ==================================================
# CONFIGURAZIONE MODELLO (AGGIORNATO GEMINI 2.5)
# ==================================================
MODEL_NAME = 'gemini-2.5-flash' # <--- AGGIORNATO QUI

SYSTEM_PROMPT = """
Sei un assistente IA esperto in imaging biomedico. Analizza le immagini radiografiche fornite.
RISPONDI SEMPRE IN ITALIANO.
Identifica la parte anatomica, descrivi anomalie visibili e fratture.
IMPORTANTE: Non fare diagnosi definitive. Concludi invitando a consultare un radiologo.
"""

# SICUREZZA CRUCIALE PER RAGGI X
SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
]

try:
    api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        st.error("❌ Chiave API mancante.")
        st.stop()
    
    genai.configure(api_key=api_key)
except Exception as e:
    st.error(f"Errore config: {e}")
    st.stop()

# ==================================================
# FUNZIONI
# ==================================================

def analizza_immagini_radiografiche(lista_immagini):
    if not lista_immagini: return "Nessuna immagine."

    content = ["Analizza dettagliatamente queste immagini radiografiche."]
    content.extend(lista_immagini)

    max_retries = 2
    for attempt in range(max_retries):
        try:
            # Istanza modello fresca per Gemini 2.5
            model = genai.GenerativeModel(
                model_name=MODEL_NAME,
                safety_settings=SAFETY_SETTINGS,
                system_instruction=SYSTEM_PROMPT
            )

            response = model.generate_content(content)

            if hasattr(response, 'text') and response.text:
                return response.text.strip() + "\n\n**⚠️ DISCLAIMER AI:** *Analisi automatica. Consulta il radiologo.*"
            
            elif hasattr(response, 'prompt_feedback') and response.prompt_feedback.block_reason:
                return f"⚠️ Blocco Sicurezza: {response.prompt_feedback.block_reason}"

        except exceptions.GoogleAPIError as e:
            if "not found" in str(e).lower(): return f"❌ Errore Modello: {MODEL_NAME} non disponibile."
            time.sleep(1)
        except Exception as e:
            return f"❌ Errore imprevisto: {str(e)}"

    return "❌ Impossibile completare l'analisi."

# ==================================================
# MAIN APP
# ==================================================
def main():
    if 'analysis_result' not in st.session_state: st.session_state.analysis_result = None
    if 'processed_files_info' not in st.session_state: st.session_state.processed_files_info = []

    st.title('🩺 Assistente AI per Radiografie (Gemini 2.5)')
    st.warning("**ATTENZIONE:** NON È UN DISPOSITIVO MEDICO. Consulta sempre uno specialista.")

    uploaded_files = st.file_uploader('Trascina qui le radiografie', type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)

    current_files_info = [(f.name, f.size) for f in uploaded_files] if uploaded_files else []
    
    if current_files_info != st.session_state.processed_files_info:
        st.session_state.analysis_result = None
        st.session_state.processed_files_info = current_files_info

    images_to_analyze = []
    
    if uploaded_files:
        st.write(f"**Anteprima:**")
        cols = st.columns(min(len(uploaded_files), 4))
        for idx, uploaded_file in enumerate(uploaded_files):
            try:
                img = Image.open(uploaded_file)
                images_to_analyze.append(img)
                with cols[idx % 4]: st.image(img, use_container_width=True)
            except: pass

    analyze_btn = st.button('✨ Analizza con AI', type="primary", disabled=not images_to_analyze)

    if analyze_btn and images_to_analyze:
        with st.spinner("🧠 Analisi Gemini 2.5 in corso..."):
            st.session_state.analysis_result = analizza_immagini_radiografiche(images_to_analyze)

    if st.session_state.analysis_result:
        st.markdown("---")
        st.subheader("📋 Referto IA")
        st.markdown(st.session_state.analysis_result)

if __name__ == '__main__':
    main()
