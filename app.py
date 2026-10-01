from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics.pairwise import cosine_similarity


DATASET_PATH = Path(__file__).parent / "AI-Powered Chatbot.xlsx"
WELCOME_MESSAGE = (
    "Hello! I'm UniBot, your AI campus assistant. Ask me about courses, "
    "schedules, facilities, financial aid, and more."
)

st.set_page_config(
    page_title="UniBot - AI Campus Assistant",
    page_icon="🎓",
    layout="centered",
)


@st.cache_resource(show_spinner="Loading the campus assistant...")
def load_chatbot():
    if not DATASET_PATH.is_file():
        raise FileNotFoundError(f"Dataset file was not found: {DATASET_PATH}")

    dataset = pd.read_excel(DATASET_PATH)
    required_columns = {"User Message", "Intent", "Bot Response"}
    missing_columns = required_columns.difference(dataset.columns)
    if missing_columns:
        raise ValueError(
            "Dataset is missing required columns: "
            + ", ".join(sorted(missing_columns))
        )

    dataset = dataset.dropna(subset=["User Message", "Intent", "Bot Response"]).copy()
    dataset["User Message"] = dataset["User Message"].astype(str)
    dataset["Intent"] = dataset["Intent"].astype(str)

    vectorizer = TfidfVectorizer(
        lowercase=True,
        stop_words="english",
        ngram_range=(1, 2),
    )
    message_vectors = vectorizer.fit_transform(dataset["User Message"])
    model = LogisticRegression(max_iter=1000)
    model.fit(message_vectors, dataset["Intent"])

    return dataset, vectorizer, model, message_vectors


def get_reply(message, dataset, vectorizer, model, message_vectors):
    user_vector = vectorizer.transform([message])
    if user_vector.nnz == 0:
        return {
            "intent": "unknown",
            "response": "Sorry, I don't know the answer to that yet.",
            "confidence": 0.0,
            "sentiment": "neutral",
        }

    similarities = cosine_similarity(user_vector, message_vectors)[0]
    best_match_index = int(np.argmax(similarities))
    max_similarity = float(similarities[best_match_index])

    if max_similarity < 0.30:
        return {
            "intent": "unknown",
            "response": "Sorry, I don't know the answer to that yet.",
            "confidence": max_similarity,
            "sentiment": "neutral",
        }

    probabilities = model.predict_proba(user_vector)[0]
    sentiment = "neutral"
    if "Sentiment Label" in dataset.columns:
        value = dataset.iloc[best_match_index]["Sentiment Label"]
        if pd.notna(value):
            sentiment = str(value)

    return {
        "intent": str(model.predict(user_vector)[0]),
        "response": str(dataset.iloc[best_match_index]["Bot Response"]),
        "confidence": float(np.max(probabilities)),
        "sentiment": sentiment,
    }


st.title("UniBot")
st.caption("AI Campus Assistant")

try:
    dataset, vectorizer, model, message_vectors = load_chatbot()
except Exception as error:
    st.error("The chatbot could not load its dataset or model.")
    st.exception(error)
    st.stop()

with st.sidebar:
    st.subheader("Campus Assistant")
    st.metric("Intents", int(dataset["Intent"].nunique()))
    topic_count = int(dataset["Topic"].nunique()) if "Topic" in dataset.columns else 0
    st.metric("Topics", topic_count)
    if "Conversation ID" in dataset.columns:
        conversation_count = int(dataset["Conversation ID"].nunique())
    else:
        conversation_count = len(dataset)
    st.metric("Conversations", conversation_count)

    if st.button("Clear conversation", use_container_width=True):
        st.session_state.messages = [
            {"role": "assistant", "content": WELCOME_MESSAGE}
        ]
        st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": WELCOME_MESSAGE}
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("intent"):
            st.caption(
                f"Intent: {message['intent']} · "
                f"Confidence: {message['confidence']:.0%} · "
                f"Sentiment: {message['sentiment']}"
            )

prompt = st.chat_input("Ask about courses, campus services, or financial aid")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            reply = get_reply(prompt, dataset, vectorizer, model, message_vectors)
        st.markdown(reply["response"])
        st.caption(
            f"Intent: {reply['intent']} · "
            f"Confidence: {reply['confidence']:.0%} · "
            f"Sentiment: {reply['sentiment']}"
        )

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": reply["response"],
            "intent": reply["intent"],
            "confidence": reply["confidence"],
            "sentiment": reply["sentiment"],
        }
    )