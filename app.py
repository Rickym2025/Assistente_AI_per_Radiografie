# -*- coding: utf-8 -*-

from PIL import Image
import streamlit as st
import google.generativeai as genai
import os # Necessario per gestire API Key da secrets o env vars

# --- Importa Configurazioni ---
# Assicurati di avere un file 'configs.py' nel tuo repository
# contenente le costanti: SYSTEM_PROMPT, SAFETY_SETTINGS, GENERATION_CONFIG, MODEL_NAME
# Esempio di configs.py:
# SYSTEM_PROMPT = "Sei un assistente AI specializzato nell'analisi preliminare di immagini radiografiche. Fornisci osservazioni generali sui possibili risultati visibili nell'immagine. NON FARE DIAGNOSI. Sottolinea sempre che l'analisi è preliminare e richiede conferma da un radiologo qualificato."
# SAFETY_SETTINGS = [...] # Impostazioni di sicurezza appropriate per contenuti medici
# GENERATION_CONFIG = {...} # Configurazione per la generazione del testo (es. temperature, max_tokens)
# MODEL_NAME = 'gemini-1.5-flash' # o 'gemini-pro-vision' se usi la versione precedente specifica per vision

try:
    from configs import SYSTEM_PROMPT, SAFETY_SETTINGS, GENERATION_CONFIG, MODEL_NAME
except ImportError:
    st.warning("File 'configs.py' non trovato. Utilizzo valori predefiniti. È consigliato creare 'configs.py'.")
    # Valori predefiniti di ESEMPIO se configs.py non esiste
    MODEL_NAME = 'gemini-1.5-flash' # Modello multimodale più recente
    SYSTEM_PROMPT = "Analizza l'immagine radiografica fornita. Descrivi eventuali anomalie o punti di interesse visibili. Sii cauto e ricorda che questa è un'analisi AI preliminare e non una diagnosi medica."
    # Esempio (molto restrittivo, da adattare): https://ai.google.dev/docs/safety_setting_gemini
    SAFETY_SETTINGS = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    ]
    GENERATION_CONFIG = {
        "temperature": 0.4,
        "top_p": 1,
        "top_k": 32,
        "max_output_tokens": 4096, # Adatta se necessario
    }

# --- Configura Modello Gemini ---
try:
    # Metodo sicuro per ottenere la API Key con Streamlit Sharing
    api_key = st.secrets["GEMINI_API_KEY"]
    if not api_key:
        st.error("Chiave API Gemini ('GEMINI_API_KEY') vuota trovata nei segreti. Impostala correttamente.")
        st.stop()
    genai.configure(api_key=api_key)

    # Istanzia il modello
    model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        safety_settings=SAFETY_SETTINGS,
        generation_config=GENERATION_CONFIG,
        system_instruction=SYSTEM_PROMPT
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
    st.set_page_config(page_title='Assistente AI per Radiografie') # Titolo Tab Browser
    st.title('🩺 Assistente AI per Radiografie') # Titolo Principale Pagina
    st.subheader("Analizza immagini radiografiche con l'IA (Gemini)") # Sottotitolo

    # --- Disclaimer Medico ESSENZIALE ---
    st.error("""
    **⚠️ ATTENZIONE: Strumento AI NON Diagnostico! ⚠️**
    *   Questa applicazione fornisce un'analisi preliminare automatica e **NON sostituisce** il parere di un **medico radiologo qualificato**.
    *   L'IA può commettere errori. **NON utilizzare** questo strumento per autodiagnosi o decisioni mediche.
    *   Consulta **SEMPRE** un medico per l'interpretazione ufficiale delle tue radiografie e per qualsiasi consiglio sulla tua salute.
    """)
    st.markdown("---") # Separatore

    # --- Layout Caricamento e Pulsante ---
    col1, col2 = st.columns([1, 4]) # Colonna pulsante più piccola, colonna upload più grande
    # Pulsante nella prima colonna
    submit_btn = col1.button('ANALIZZA  Radiology️', use_container_width=True) # Pulsante di avvio analisi
    # Uploader nella seconda colonna
    uploaded_file = col2.file_uploader('Carica Radiografia (PNG, JPG, JPEG):', type=['png', 'jpg', 'jpeg'], accept_multiple_files=False, label_visibility="collapsed")

    # --- Layout Visualizzazione Immagine e Risposta ---
    col3, col4 = st.columns(2) # Due colonne di uguale larghezza

    # Variabile per memorizzare l'immagine caricata
    image_data = None
    if uploaded_file:
        try:
            image_data = Image.open(uploaded_file)
            # Mostra immagine nella colonna sinistra
            col3.image(image_data, caption=f"Radiografia Caricata: {uploaded_file.name}", use_column_width=True)
        except Exception as e:
            st.error(f"Errore nell'apertura dell'immagine: {e}")
            image_data = None # Resetta se c'è errore

        # Prepara l'area per la risposta nella colonna destra
        message_placeholder = col4.empty() # Usa un placeholder per scrivere dopo
        message = message_placeholder.chat_message("assistant", avatar="🤖") # Avatar IA

    # --- Logica di Analisi (quando il pulsante viene premuto E un'immagine è caricata) ---
    if submit_btn and image_data:
        # Mostra uno spinner durante l'analisi
        with st.spinner("🤖 Analisi IA in corso..."):
            try:
                # --- Prepara contenuto per Gemini ---
                # (Non sembra esserci una vera cronologia qui, invia solo l'immagine)
                # Se volessi una chat più complessa, dovresti gestire la history diversamente
                content_to_send = [
                    # Puoi aggiungere un prompt testuale specifico qui se necessario,
                    # altrimenti si basa solo sul SYSTEM_PROMPT e sull'immagine.
                    # Esempio: "Descrivi i risultati principali visibili in questa radiografia.",
                    image_data
                ]

                # --- Chiama Gemini API ---
                # NOTA: model.start_chat() e chat_session.send_message() sono per chat multi-turno.
                # Per una singola analisi di immagine, model.generate_content() è più diretto.
                # Uso generate_content per semplicità e coerenza con l'uso comune per analisi singole.
                response = model.generate_content(content_to_send)

                # --- Mostra Risposta ---
                message.write(response.text) # Scrive la risposta nel placeholder

                # Gestione (opzionale) della history se vuoi evolvere in una chat
                # if 'history' not in st.session_state:
                #     st.session_state['history'] = []
                # st.session_state['history'].append({"role": "user", "parts": ["Analisi richiesta per immagine."]}) # Semplificato
                # st.session_state['history'].append({"role": "model", "parts": [response.text]})

            except Exception as e:
                 st.error(f"Errore durante l'analisi AI: {e}")
                 message.error("Impossibile completare l'analisi.") # Scrive errore nel placeholder

    elif submit_btn and not image_data:
        st.warning("Per favore, carica un'immagine prima di premere 'ANALIZZA'.")
