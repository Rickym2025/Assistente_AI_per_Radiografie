# -*- coding: utf-8 -*-

# ==================================================
# IMPORT NECESSARI - DEVONO STARE ALL'INIZIO DEL FILE
# ==================================================
import streamlit as st
from PIL import Image
import google.generativeai as genai
import os
import time
from io import BytesIO # <--- SPOSTATO QUI ALL'INIZIO!
import PyPDF2 # Assicurati sia nel requirements.txt se usi PDF
import tempfile # Assicurati sia nel requirements.txt se usi PDF
from google.api_core import exceptions # Assicurati sia nel requirements.txt

# --- Importa Configurazioni ---
try:
    # Assicurati che SYSTEM_PROMPT in configs.py chieda risposte in ITALIANO
    from configs import SYSTEM_PROMPT, SAFETY_SETTINGS, GENERATION_CONFIG, MODEL_NAME
except ImportError:
    st.warning("File 'configs.py' non trovato. Utilizzo valori predefiniti in ITALIANO.")
    MODEL_NAME = 'gemini-1.5-flash'
    SYSTEM_PROMPT = "Analizza l'immagine/immagini radiografica fornita. **Rispondi sempre e solo in ITALIANO.** Descrivi eventuali anomalie o punti di interesse visibili in modo strutturato. Sii cauto e ricorda esplicitamente alla fine della risposta che questa è un'analisi AI preliminare, puramente informativa e non una diagnosi medica, e che è necessario consultare un medico radiologo."
    SAFETY_SETTINGS = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    ]
    GENERATION_CONFIG = {
        "temperature": 0.45,
        "top_p": 1,
        "top_k": 32,
        "max_output_tokens": 4096,
    }

# --- Configura Modello Gemini ---
# (Codice configurazione Gemini invariato, usa st.secrets)
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
        system_instruction=SYSTEM_PROMPT
    )
except KeyError:
    st.error("Chiave API Gemini ('GEMINI_API_KEY') non trovata nei segreti di Streamlit.")
    st.error("Vai su 'Manage app' -> 'Settings' -> 'Secrets' e aggiungi: \nGEMINI_API_KEY = \"LA_TUA_CHIAVE_API\"")
    st.stop()
except Exception as e:
    st.error(f"Errore durante la configurazione dell'API Gemini: {e}")
    st.stop()

# --- Funzioni Helper (analizza_referto_medico, ecc. - Assicurati siano definite qui o importate) ---
# Incolla qui le definizioni delle funzioni analizza_referto_medico, analisi_fallback, estrai_testo_da_pdf
# (Se estrai_testo_da_pdf non serve perché carichi solo immagini, puoi ometterla insieme ai suoi import)

# Esempio funzione (assicurati che sia la tua versione completa)
def analizza_immagini_radiografiche(lista_immagini):
    """
    Invia una lista di immagini PIL a Gemini per l'analisi.
    Restituisce la risposta testuale o un messaggio di errore.
    """
    if not lista_immagini:
        return "Errore: Nessuna immagine valida fornita per l'analisi."

    # Costruisci il contenuto per l'API
    content_to_send = [
        "Analizza le seguenti immagini radiografiche in ITALIANO, fornendo osservazioni per ciascuna se possibile, o un'analisi complessiva:",
    ]
    content_to_send.extend(lista_immagini) # Aggiunge tutti gli oggetti PIL.Image

    # Logica di tentativo API (semplificata, puoi usare la tua versione più robusta)
    max_retries = 2
    for attempt in range(max_retries):
        try:
            response = model.generate_content(content_to_send)

            # Controllo risposta bloccata
            if hasattr(response, 'prompt_feedback') and response.prompt_feedback.block_reason:
                 reason = response.prompt_feedback.block_reason
                 st.error(f"L'analisi è stata bloccata dall'IA (Motivo: {reason}). Controlla le immagini o le impostazioni di sicurezza.")
                 return f"Errore: Bloccato dal sistema ({reason})."

            # Controllo testo valido
            if hasattr(response, 'text') and response.text:
                 # Aggiungi disclaimer finale dell'app
                 disclaimer_app = "\n\n---\n**⚠️⚠️ DISCLAIMER FINALE (DA APP) ⚠️⚠️**\n*Ricorda ancora una volta: questa analisi, per quanto dettagliata, è **AUTOMATICA**, **NON PERSONALIZZATA** e **NON SOSTITUISCE IL MEDICO**. Errori, omissioni o interpretazioni imprecise sono possibili. **Consulta SEMPRE il tuo medico** per una valutazione corretta e completa.*"
                 return response.text.strip() + disclaimer_app
            else:
                 st.warning(f"Risposta inattesa o vuota dall'IA (Tentativo {attempt + 1}).")
                 # Non ritornare subito, riprova

        except exceptions.GoogleAPIError as e:
            st.warning(f"Errore API Google (Tentativo {attempt + 1}): {str(e)}")
            if "quota" in str(e).lower():
                 st.error("Limite richieste API superato (Quota).")
                 return "Errore: Quota API superata."
            # Aspetta prima di riprovare (tranne l'ultimo tentativo)
            if attempt < max_retries - 1:
                 time.sleep(2) # Pausa di 2 secondi
            else:
                 st.error("Errore API persistente dopo vari tentativi.")
                 return "Errore: Impossibile contattare l'IA dopo vari tentativi."
        except Exception as e:
            st.error(f"Errore imprevisto durante l'analisi AI: {str(e)}")
            # Non ritornare subito, ma registra l'errore
            if attempt == max_retries - 1:
                return f"Errore: Analisi fallita ({type(e).__name__})."

    # Se tutti i tentativi falliscono
    st.error("Impossibile completare l'analisi dopo tutti i tentativi.")
    return "Errore: Analisi fallita dopo multipli tentativi."


# --- Funzione Principale dell'App ---
def main():

    # Inizializza session state (come prima)
    if 'analysis_result' not in st.session_state:
        st.session_state.analysis_result = None
    if 'processed_files_info' not in st.session_state: # Usiamo info invece di ID
        st.session_state.processed_files_info = []

    # --- IMMAGINE DI INTESTAZIONE ---
    header_image_url = "https://cdn.leonardo.ai/users/b9c4238e-d77c-4148-bef5-4a02da79edff/generations/c75c937c-f984-4904-8a7f-e0449604d70b/Leonardo_Phoenix_10_Create_an_image_for_a_mobile_apps_landing_3.jpg"
    try:
        st.image(header_image_url) # Rimosso use_container_width
    except Exception as img_err:
        st.warning(f"Avviso: Impossibile caricare l'immagine di intestazione. ({img_err})", icon="🖼️")

    st.title('🩺 Assistente AI per Radiografie')
    st.markdown("Carica le tue immagini radiografiche per un'analisi preliminare basata su IA.")
    st.markdown("---")

    # --- Disclaimer Medico ESSENZIALE ---
    st.error("""
    **⚠️ ATTENZIONE: Strumento AI NON Diagnostico! ⚠️**
    *   Questa applicazione fornisce un'analisi preliminare automatica e **NON sostituisce** il parere di un **medico radiologo qualificato**.
    *   L'IA può commettere errori. **NON utilizzare** questo strumento per autodiagnosi o decisioni mediche.
    *   Consulta **SEMPRE** un medico per l'interpretazione ufficiale delle tue radiografie e per qualsiasi consiglio sulla tua salute.
    """)
    st.markdown("---")

    # --- PASSO 1: CARICAMENTO IMMAGINI ---
    st.header("Passo 1: Carica le Radiografie 📤") # Usato header per più visibilità
    st.info("""
        **Come caricare le immagini:**
        *   Clicca sul pulsante "Browse files" qui sotto.
        *   Oppure, trascina uno o più file immagine (PNG, JPG) nell'area grigia.
    """)

    uploaded_files = st.file_uploader(
        'Seleziona o trascina le immagini qui:',
        type=['png', 'jpg', 'jpeg'],
        accept_multiple_files=True,
        label_visibility="collapsed",
        key="file_uploader" # Aggiunta key per reset
    )

    # --- Logica per gestire il cambiamento dei file caricati ---
    current_files_info = [(f.name, f.size) for f in uploaded_files] if uploaded_files else []
    # Se la lista di file caricati è cambiata rispetto all'ultima volta, resetta l'analisi
    if current_files_info != st.session_state.processed_files_info:
        st.session_state.analysis_result = None
        st.session_state.processed_files_info = current_files_info
        # Forza un rerun per aggiornare correttamente lo stato del pulsante e le anteprime
        if uploaded_files or st.session_state.analysis_result is not None : # Rerun solo se necessario
             st.rerun()


    # --- Visualizzazione Anteprime (se ci sono file) ---
    images_data = [] # Lista degli oggetti PIL.Image validi
    preview_placeholder = st.empty() # Placeholder per le anteprime

    if uploaded_files:
        with preview_placeholder.container():
            st.markdown("---")
            st.markdown("**Immagini Pronte per l'Analisi:**")
            cols = st.columns(min(len(uploaded_files), 5)) # Fino a 5 anteprime per riga
            col_idx = 0
            images_data_buffer = [] # Buffer temporaneo
            valid_images_found = False
            for uploaded_file in uploaded_files:
                try:
                    img_bytes = uploaded_file.getvalue()
                    img = Image.open(BytesIO(img_bytes))
                    images_data_buffer.append(img) # Aggiungi solo se l'apertura ha successo
                    with cols[col_idx % len(cols)]:
                        st.image(img_bytes, caption=f"{uploaded_file.name[:20]}...", use_column_width='auto')
                    col_idx += 1
                    valid_images_found = True # Trovata almeno un'immagine valida
                except Exception as e:
                    st.warning(f"Ignorata '{uploaded_file.name}': {e}", icon="⚠️")

            images_data = images_data_buffer # Aggiorna lista principale con immagini valide

            if not valid_images_found and uploaded_files:
                 st.warning("Nessuna delle immagini caricate è valida o leggibile.")


    # --- PASSO 2: AVVIO ANALISI (Pulsante Visibile) ---
    st.markdown("---")
    st.header("Passo 2: Avvia l'Analisi 🔬") # Header per il passo 2

    # Il pulsante è sempre visibile, ma disabilitato se non ci sono immagini
    submit_btn_pressed = st.button(
        '✨ Analizza le Immagini Caricate! ✨', # Testo più accattivante
        key='analyze_button',
        use_container_width=True, # Occupa tutta la larghezza
        type="primary",
        disabled=not images_data # Disabilita se la lista images_data è vuota
    )

    # Spiegazione se il pulsante è disabilitato
    if not images_data and uploaded_files:
        st.caption("Il pulsante 'Analizza' è disabilitato perché nessuna immagine valida è stata caricata o letta correttamente.")
    elif not images_data and not uploaded_files:
         st.caption("☝️ Carica almeno un'immagine valida per abilitare l'analisi.")


    # --- Esecuzione Analisi e Visualizzazione Risultati ---
    analysis_results_placeholder = st.empty() # Placeholder per i risultati

    # Se l'analisi è stata triggerata E ci sono immagini valide
    if submit_btn_pressed and images_data:
        with analysis_results_placeholder.container(): # Mostra i risultati qui
            st.markdown("---")
            st.subheader("Risultato Analisi IA 🤖")
            with st.spinner("Elaborazione IA in corso... Attendere prego..."):
                try:
                    # Chiama la funzione di analisi (assicurati sia definita correttamente)
                    analisi_output = analizza_immagini_radiografiche(images_data)
                    st.markdown(analisi_output) # Mostra il risultato (include già il disclaimer app)
                    # Salva il risultato nello stato per mostrarlo anche dopo rerun
                    st.session_state.analysis_result = analisi_output

                except Exception as e:
                     st.error(f"Errore critico durante il processo di analisi: {e}")
                     st.session_state.analysis_result = "Errore: Analisi fallita."
                     st.markdown(st.session_state.analysis_result)


    # Mostra il risultato precedente se esiste e non è stato premuto il pulsante ora
    elif not submit_btn_pressed and st.session_state.analysis_result:
         with analysis_results_placeholder.container():
              st.markdown("---")
              st.subheader("Risultato Analisi IA (Precedente) 🤖")
              st.markdown(st.session_state.analysis_result)


    # --- IMMAGINE FINALE IN BASSO ---
    st.markdown("---")
    footer_image_url = "https://cdn.leonardo.ai/users/b9c4238e-d77c-4148-bef5-4a02da79edff/generations/e7758e5e-ed2e-487c-9c55-382ed6d28106/Leonardo_Phoenix_10_Create_a_modern_welldefined_and_illustrati_3.jpg"
    try:
        st.image(footer_image_url) # Rimosso use_container_width
    except Exception as img_err:
        st.warning(f"Avviso: Impossibile caricare l'immagine finale. ({img_err})", icon="🖼️")

    st.caption("Applicazione sviluppata con Streamlit e Google Gemini. Ricorda: consulta sempre un medico qualificato.")

# --- Chiamata finale ---
if __name__ == '__main__':
    main()
