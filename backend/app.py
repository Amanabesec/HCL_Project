import os
import pandas as pd
import numpy as np
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics.pairwise import cosine_similarity
import logging

app = Flask(__name__, static_folder='../frontend')
CORS(app)
logging.basicConfig(level=logging.INFO)

# Global variables to hold the dataset and models
df = None
vectorizer = None
model = None

def init_app():
    global df, vectorizer, model
    try:
        # Load dataset
        dataset_path = os.path.join(os.path.dirname(__file__), '../AI-Powered Chatbot.xlsx')
        logging.info(f"Loading dataset from {dataset_path}")
        df = pd.read_excel(dataset_path)
        
        # Train model
        logging.info("Training model...")
        vectorizer = TfidfVectorizer(lowercase=True, stop_words='english', ngram_range=(1,2))
        X = vectorizer.fit_transform(df['User Message'])
        y = df['Intent']
        
        model = LogisticRegression(max_iter=1000)
        model.fit(X, y)
        logging.info("Model trained successfully.")
    except Exception as e:
        logging.error(f"Error during initialization: {e}")

# Initialize when importing
init_app()

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"}), 200

@app.route('/api/stats', methods=['GET'])
def stats():
    if df is None:
        return jsonify({"error": "Dataset not loaded"}), 500
        
    try:
        num_intents = df['Intent'].nunique()
        num_topics = df['Topic'].nunique() if 'Topic' in df.columns else 0
        total_conversations = df['Conversation ID'].nunique() if 'Conversation ID' in df.columns else len(df)
        
        return jsonify({
            "num_intents": int(num_intents),
            "num_topics": int(num_topics),
            "total_conversations": int(total_conversations)
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    if not request.json or 'message' not in request.json:
        return jsonify({"error": "No message provided"}), 400
        
    if df is None or vectorizer is None or model is None:
        return jsonify({"error": "Model not initialized"}), 500
        
    user_message = request.json['message']
    
    try:
        # Vectorize user input
        X_user = vectorizer.transform([user_message])
        X_all = vectorizer.transform(df['User Message'])
        
        # Check cosine similarity
        similarities = cosine_similarity(X_user, X_all)[0]
        max_similarity = np.max(similarities)
        best_match_idx = np.argmax(similarities)
        
        if max_similarity < 0.30:
            return jsonify({
                "intent": "unknown",
                "response": "Sorry I don't know",
                "confidence": float(max_similarity),
                "sentiment": "neutral"
            }), 200
            
        # Predict intent
        intent = model.predict(X_user)[0]
        
        # Get probability/confidence
        probabilities = model.predict_proba(X_user)[0]
        confidence = np.max(probabilities)
        
        # Return matched response
        matching_response = df.iloc[best_match_idx]['Bot Response']
        sentiment = df.iloc[best_match_idx]['Sentiment Label'] if 'Sentiment Label' in df.columns else "neutral"
        
        return jsonify({
            "intent": intent,
            "response": matching_response,
            "confidence": float(confidence),
            "sentiment": sentiment
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Serve frontend static files
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        index_path = os.path.join(app.static_folder, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(app.static_folder, 'index.html')
        return jsonify({"error": "Frontend not found"}), 404

if __name__ == '__main__':
    app.run(port=5000, host='0.0.0.0')
