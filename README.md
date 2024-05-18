# AI X-Ray Assistant (Gemini Pro)

## 1.0 About
This project leverages advanced machine learning techniques to assist radiologists in analyzing X-ray images, offering diagnostic suggestions and highlighting areas of concern. By combining Google's *Gemini Pro* model with medical imaging, we aim to improve the accuracy and efficiency of radiological diagnoses.

### 1.1 Features
* **Automated Diagnosis:** The AI model provides diagnostic suggestions based on input X-ray images.
* **Anomaly Detection:** Highlights potential areas of concern in the X-ray images for further review.
* **User-Friendly Interface:** Easy-to-use interface designed for seamless integration into radiological workflows.
* **Continuous Learning:** The model is designed to improve over time with continuous input and validation from radiologists.

![image](https://github.com/lloydaxeph/ai_xray_assistant_gemini/assets/158691653/9b3f58e8-f4aa-4849-b0f1-54dab13d4a6b)

*This project uses [streamlit](https://docs.streamlit.io/) for demonstration*

## 2.0 Getting Started

### 2.1 Installation
Install the required packages.
```
pip3 install -r requirements.txt
```
### 2.2 Create an API key
This project requires you to have your own **Google AI Studio API key**. To learn how to create your own API Key, please check [Google AI Studio - Get API key](https://aistudio.google.com/app/apikey). 
Once you have the API Key, use it to configure `google.generativeai` at [app.py#L10](https://github.com/lloydaxeph/ai_xray_assistant_gemini/blob/master/app.py#L10).
```
genai.configure(api_key='{YOUR_GOOGLE_GEMINI_API}')
```

### 2.3 Run the app
To run the [streamlit](https://docs.streamlit.io/) app, enter the following command on the terminal.
```
streamlit run app.py
```

