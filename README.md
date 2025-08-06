# 🧠 MI Chatbots

This repository contains two Motivational Interviewing (MI) chatbot applications built using Streamlit:

- `HPV.py`: Practice MI skills related to **HPV vaccine**  
- `OHI.py`: Practice MI skills for **Oral Hygiene**

These chatbots simulate realistic patient interactions and provide **automated MI feedback** based on example transcripts stored in `*.txt` format.

---

## 📁 Project Structure
anwesha-umn/
├── .devcontainer/ # Dev Container setup (for VS Code Remote/Containers)
├── hpv_rubrics/ # HPV MI example transcripts + rubric feedback (.txt format)
├── ohi_rubrics/ # Oral Hygiene MI transcripts + rubric feedback (.txt format)
├── HPV.py # Streamlit app for HPV vaccine MI chatbot
├── OHI.py # Streamlit app for Oral Health MI chatbot
├── README.md # Instructions to set up and run the app
├── requirements.txt # Python dependencies for the chatbot
└── runtime.txt # (Optional) Python version for deployment environments (e.g., Streamlit Cloud)

> You can add more `.txt` transcripts with MI feedback in the `hpv_rubrics/` or `ohi_rubrics/` folders to improve the RAG-based evaluation.

---

## HPV MI Practice App

### Overview
This app simulates a realistic patient interaction to practice Motivational Interviewing (MI) skills for HPV vaccination discussions. Users can play the role of a patient or provider to engage in a conversation that focuses on exploring thoughts and feelings about the HPV vaccine.


[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://hpv-mi-chatbot.streamlit.app/)

## Setup Instructions
To run this app on your own computer, follow these steps:

### Prerequisites
- Python installed on your machine (Python 3.10 recommended)
- Pip package manager installed

### Installation
1. Clone or download the repository to your local machine:
   ```bash
   git clone https://github.com/anwesha-umn/MI_chatbots.git
   cd MI_chatbots

### How to run it on your own machine

2. Install the requirements 

   ```
   $ pip install -r requirements.txt
   ```

3. Run the app on local machine 

   ```
   $ streamlit run HPV.py
   ```
