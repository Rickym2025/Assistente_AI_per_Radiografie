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

# Carica variabili d'ambiente (per uso locale)
load_dotenv()

# ==================================================
# CONFIGURAZIONE PAGINA
# ==================================================
st.set_page_config(
    page_title="Assistente AI Radiografie",
    page_icon="",
    layout="wide"
)

# ==================================================
# CONFIGURAZIONE MODELLO E PROMPT
# ==================================================

# 1. Nome Modello (Gratuito e Multimodale)
MODEL_NAME = 'gemini-1.5-flash'

# 2. Prompt di Sistema (Istruzioni base per l'IA)
SYSTEM_PROMPT = """
Sei un assistente IA esperto in imaging biomedico. Il tuo compito è analizzare le immagini radiografiche fornite.
RISPONDI SEMPRE IN ITALIANO.

Linee guida:
1. Identifica la parte anatomica visibile.
2. Descrivi in modo strutturato eventuali anomalie, fratture, opacità o punti di interesse visibili.
3. Se l'immagine non è chiara o non è una radiografia, dillo chiaramente.
4. Usa un tono professionale ma cauto.

IMPORTANTE: Non fare diagnosi definitive. Concludi sempre invitando a consultare un radiologo.
"""

# 3. Configurazione Sicurezza (CRUCIALE PER RADIOGRAFIE)
# Le immagini mediche spesso vengono bloccate dai filtri standard. 
# Qui li rilassiamo per permettere l'analisi.
SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
]

# 4. Inizializzazione API
try:
    api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        st.error("❌ Chiave API Gemini mancante. Impostala nei Secrets o nel file .env")
        st.stop()
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        safety_settings=SAFETY_SETTINGS,
        system_instruction=SYSTEM_PROMPT
    )
except Exception as e:
    st.error(f"Errore configurazione Gemini: {e}")
    st.stop()

# ==================================================
# FUNZIONI HELPER
# ==================================================

def analizza_immagini_radiografiche(lista_immagini):
    """
    Invia le immagini a Gemini per l'analisi.
    """
    if not lista_immagini:
        return "Nessuna immagine fornita."

    # Costruzione messaggio: Testo + Immagini
    content = ["Analizza dettagliatamente queste immagini radiografiche."]
    content.extend(lista_immagini)

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = model.generate_content(content)

            if hasattr(response, 'text') and response.text:
                disclaimer = "\n\n---\n**⚠️ DISCLAIMER AI:** *Questa analisi è generata automaticamente. Non sostituisce il parere del medico radiologo.*"
                return response.text.strip() + disclaimer
            
            elif hasattr(response, 'prompt_feedback') and response.prompt_feedback.block_reason:
                return f"⚠️ Analisi bloccata dai filtri di sicurezza (Motivo: {response.prompt_feedback.block_reason}). Le immagini mediche a volte vengono erroneamente filtrate."

        except exceptions.GoogleAPIError as e:
            if "quota" in str(e).lower():
                return "❌ Errore: Quota API gratuita superata per oggi."
            time.sleep(2)
        except Exception as e:
            return f"❌ Errore imprevisto: {str(e)}"

    return "❌ Impossibile completare l'analisi dopo vari tentativi."

# ==================================================
# MAIN APP
# ==================================================
def main():
    if 'analysis_result' not in st.session_state:
        st.session_state.analysis_result = None
    if 'processed_files_info' not in st.session_state:
        st.session_state.processed_files_info = []

    # --- Header ---
    # Immagine di intestazione (gestione errori se il link non va)
    header_url = "https://cdn.leonardo.ai/users/b9c4238e-d77c-4148-bef5-4a02da79edff/generations/c75c937c-f984-4904-8a7f-e0449604d70b/Leonardo_Phoenix_10_Create_an_image_for_a_mobile_apps_landing_3.jpg"
    try:
        st.image(header_url, use_container_width=True)
    except:
        pass

    st.title('🩺 Assistente AI per Radiografie')
    st.markdown("Carica immagini radiografiche (Raggi X, TAC, Risonanze) per un'analisi preliminare.")
    
    st.warning("""
    **⚠️ ATTENZIONE:** Questo strumento usa l'Intelligenza Artificiale. 
    **NON È UN DISPOSITIVO MEDICO DIAGNOSTICO.** Consulta sempre uno specialista.
    """)

    # --- Upload ---
    st.markdown("### 1. Carica Immagini")
    uploaded_files = st.file_uploader(
        'Trascina qui le radiografie (JPG, PNG)',
        type=['png', 'jpg', 'jpeg'],
        accept_multiple_files=True
    )

    # --- Gestione Anteprime e Stato ---
    current_files_info = [(f.name, f.size) for f in uploaded_files] if uploaded_files else []
    
    # Se cambiano i file, resetto il risultato precedente
    if current_files_info != st.session_state.processed_files_info:
        st.session_state.analysis_result = None
        st.session_state.processed_files_info = current_files_info

    images_to_analyze = []
    
    if uploaded_files:
        st.markdown("---")
        st.write(f"**Anteprima ({len(uploaded_files)} immagini):**")
        cols = st.columns(min(len(uploaded_files), 4))
        
        for idx, uploaded_file in enumerate(uploaded_files):
            try:
                img = Image.open(uploaded_file)
                images_to_analyze.append(img)
                with cols[idx % 4]:
                    st.image(img, caption=uploaded_file.name, use_container_width=True)
            except Exception as e:
                st.error(f"File non valido: {uploaded_file.name}")

    # --- Bottone Analisi ---
    st.markdown("### 2. Risultati")
    analyze_btn = st.button('✨ Analizza con AI', type="primary", disabled=not images_to_analyze)

    if analyze_btn and images_to_analyze:
        with st.spinner("🧠 Analisi radiografica in corso..."):
            risultato = analizza_immagini_radiografiche(images_to_analyze)
            st.session_state.analysis_result = risultato

    # --- Output ---
    if st.session_state.analysis_result:
        st.markdown("---")
        st.subheader("📋 Referto IA Preliminare")
        st.markdown(st.session_state.analysis_result)

    # --- Footer ---
    st.markdown("---")
    st.caption("Powered by Gemini 1.5 Flash - Dicembre 2025")

if __name__ == '__main__':
    main()
