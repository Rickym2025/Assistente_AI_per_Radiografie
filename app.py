# -*- coding: utf-8 -*-

from PIL import Image
import streamlit as st
import google.generativeai as genai
import os

# --- Importa Configurazioni ---
# Assicurati di avere un file 'configs.py' con le costanti appropriate.
# Esempio di modifiche a configs.py per l'italiano:
# SYSTEM_PROMPT = "Sei un assistente AI specializzato nell'analisi preliminare di immagini radiografiche. **Rispondi sempre in ITALIANO.** Fornisci osservazioni generali sui possibili risultati visibili nell'immagine/immagini. NON FARE DIAGNOSI. Sottolinea sempre che l'analisi è preliminare e richiede conferma da un radiologo qualificato."
# SAFETY_SETTINGS = [...] # Adatte a contesto medico
# GENERATION_CONFIG = {...} # Adatte a risposte descrittive
# MODEL_NAME = 'gemini-1.5-flash'

try:
    from configs import SYSTEM_PROMPT, SAFETY_SETTINGS, GENERATION_CONFIG, MODEL_NAME
except ImportError:
    st.warning("File 'configs.py' non trovato. Utilizzo valori predefiniti in ITALIANO.")
    MODEL_NAME = 'gemini-1.5-flash'
    # --- MODIFICATO SYSTEM_PROMPT DEFAULT PER ITALIANO ---
    SYSTEM_PROMPT = "Analizza l'immagine/immagini radiografica fornita. **Rispondi sempre e solo in ITALIANO.** Descrivi eventuali anomalie o punti di interesse visibili in modo strutturato. Sii cauto e ricorda esplicitamente alla fine della risposta che questa è un'analisi AI preliminare, puramente informativa e non una diagnosi medica, e che è necessario consultare un medico radiologo."
    SAFETY_SETTINGS = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    ]
    GENERATION_CONFIG = {
        "temperature": 0.45, # Leggermente più creativo ma ancora fattuale
        "top_p": 1,
        "top_k": 32,
        "max_output_tokens": 4096,
    }

# --- Configura Modello Gemini ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    if not api_key:
        st.error("Chiave API Gemini ('GEMINI_API_KEY') vuota trovata nei segreti. Impostala correttamente.")
        st.stop()
    genai.configure(api_key=api_key)

    model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        safety_settings=SAFETY_SETTINGS,
        generation_config=GENERATION_CONFIG,
        system_instruction=SYSTEM_PROMPT # Il prompt di sistema ora chiede l'italiano
    )
except KeyError:
    st.error("Chiave API Gemini ('GEMINI_API_KEY') non trovata nei segreti di Streamlit.")
    st.error("Vai su 'Manage app' -> 'Settings' -> 'Secrets' e aggiungi: \nGEMINI_API_KEY = \"LA_TUA_CHIAVE_API\"")
    st.stop()
except Exception as e:
    st.error(f"Errore durante la configurazione dell'API Gemini: {e}")
    st.stop()


# --- Funzione Principale dell'App ---
if __name__ == '__main__':

    # --- Impostazione Pagina ---
    st.set_page_config(page_title='Assistente AI per Radiografie')
    st.title('🩺 Assistente AI per Radiografie')
    st.subheader("Analizza immagini radiografiche con l'IA (Gemini)")

    # --- Disclaimer Medico ESSENZIALE ---
    st.error("""
    **⚠️ ATTENZIONE: Strumento AI NON Diagnostico! ⚠️**
    *   Questa applicazione fornisce un'analisi preliminare automatica e **NON sostituisce** il parere di un **medico radiologo qualificato**.
    *   L'IA può commettere errori. **NON utilizzare** questo strumento per autodiagnosi o decisioni mediche.
    *   Consulta **SEMPRE** un medico per l'interpretazione ufficiale delle tue radiografie e per qualsiasi consiglio sulla tua salute.
    """)
    st.markdown("---")

    # --- Layout Caricamento e Pulsante ---
    col1, col2 = st.columns([1, 4])

    # --- MODIFICA: Pulsante Italiano, più visibile (tipo 'primary') ---
    with col1:
        submit_btn = st.button(
            'Analizza Radiografie ☢️',
            use_container_width=True,
            type="primary" # Rende il pulsante più prominente
        )

    # --- MODIFICA: File uploader per file MULTIPLI ---
    with col2:
        uploaded_files = st.file_uploader( # Rinominato da uploaded_file a uploaded_files
            'Carica UNA o PIÙ Radiografie (PNG, JPG, JPEG):',
            type=['png', 'jpg', 'jpeg'],
            accept_multiple_files=True, # <-- MODIFICATO QUI
            label_visibility="collapsed" # Nasconde etichetta duplicata
        )

    # --- Layout Visualizzazione Immagini e Risposta ---
    col3, col4 = st.columns(2)

    # Lista per memorizzare le immagini caricate e processate
    images_data = []
    if uploaded_files: # Controlla se la lista non è vuota
        with col3:
            st.subheader("Immagini Caricate:")
            # --- MODIFICA: Ciclo per mostrare tutte le immagini ---
            for uploaded_file in uploaded_files:
                try:
                    img = Image.open(uploaded_file)
                    images_data.append(img) # Aggiungi l'oggetto Immagine alla lista
                    st.image(img, caption=f"Caricata: {uploaded_file.name}", use_column_width=True)
                    st.markdown("---") # Separatore tra immagini
                except Exception as e:
                    st.error(f"Errore nell'apertura dell'immagine '{uploaded_file.name}': {e}")

        # Prepara l'area per la risposta nella colonna destra (solo una volta)
        message_placeholder = col4.empty()
        # --- MODIFICA: Testo chat_message in italiano ---
        message = message_placeholder.chat_message("assistant", avatar="🤖")

    # --- Logica di Analisi (quando il pulsante viene premuto E almeno un'immagine è caricata) ---
    # --- MODIFICA: Usa 'uploaded_files' e 'images_data' ---
    if submit_btn and images_data: # Se il pulsante è premuto e abbiamo immagini valide
        with st.spinner("🤖 Analisi IA in corso..."):
            try:
                # --- MODIFICA: Prepara contenuto con testo e TUTTE le immagini ---
                content_to_send = [
                    # Aggiunto prompt specifico in italiano per rafforzare la richiesta
                    "Analizza le seguenti immagini radiografiche in ITALIANO, fornendo osservazioni per ciascuna se possibile, o un'analisi complessiva:",
                ]
                content_to_send.extend(images_data) # Aggiunge tutti gli oggetti PIL.Image

                # --- Chiama Gemini API ---
                response = model.generate_content(content_to_send)

                # --- Mostra Risposta ---
                message.write(response.text) # Scrive la risposta (in italiano, si spera)

            except Exception as e:
                 st.error(f"Errore durante l'analisi AI: {e}")
                 message.error("Impossibile completare l'analisi.")

    elif submit_btn and not images_data: # Modificato per controllare images_data
        st.warning("Per favore, carica almeno un'immagine valida prima di premere 'Analizza Radiografie'.")
