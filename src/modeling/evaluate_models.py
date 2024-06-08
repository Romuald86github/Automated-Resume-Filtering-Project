import os
import joblib
from sklearn.metrics.pairwise import cosine_similarity
from tensorflow.keras.models import load_model
import numpy as np
from sklearn.metrics import ndcg_score
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences

# Preprocess and tokenize the text data
def preprocess_texts(texts, tokenizer, max_len=500):
    sequences = tokenizer.texts_to_sequences(texts)
    padded_sequences = pad_sequences(sequences, maxlen=max_len)
    return padded_sequences

def evaluate_cosine_similarity_model(X_resumes, X_jd, vectorizer_resumes, vectorizer_jd):
    X_resumes_transformed = vectorizer_resumes.transform(X_resumes)
    X_jd_transformed = vectorizer_jd.transform(X_jd)
    similarity_matrix = cosine_similarity(X_resumes_transformed.toarray(), X_jd_transformed.toarray())
    mean_cosine_similarity = np.mean(similarity_matrix.diagonal())
    
    print(f"Cosine Similarity Model:")
    print(f"Mean Cosine Similarity: {mean_cosine_similarity:.4f}")
    
    return mean_cosine_similarity

def evaluate_semantic_similarity_model(X_resumes, X_jd):
    model = load_model('models/semantic_similarity_model.h5')
    resume_embeddings = model.predict(X_resumes)
    jd_embeddings = model.predict(X_jd)
    mean_cosine_similarity = np.mean(cosine_similarity(resume_embeddings, jd_embeddings))
    
    print(f"Semantic Similarity Model:")
    print(f"Mean Cosine Similarity: {mean_cosine_similarity:.4f}")
    
    return mean_cosine_similarity

def evaluate_siamese_model(X_resumes, X_jd):
    model = load_model('models/siamese_model.h5')
    resume_embeddings = model.predict(X_resumes)
    jd_embeddings = model.predict(X_jd)
    mean_euclidean_distance = np.mean(np.sqrt(np.sum((resume_embeddings - jd_embeddings) ** 2, axis=1)))
    
    print(f"Siamese Model:")
    print(f"Mean Euclidean Distance: {mean_euclidean_distance:.4f}")
    
    return -mean_euclidean_distance

def evaluate_ranking_model(X_resumes, X_jd):
    model = load_model('models/ranking_model.h5')
    y_pred = model.predict(X_resumes).flatten()
    ndcg = ndcg_score([np.arange(len(X_resumes))], [y_pred])
    
    print(f"Ranking Model:")
    print(f"NDCG: {ndcg:.4f}")
    
    return ndcg

if __name__ == "__main__":
    resumes_data = joblib.load('data/resume_vectors.pkl')
    jd_data = joblib.load('data/job_description_vectors.pkl')

    X_resumes = resumes_data['raw_texts']
    X_jd = jd_data['raw_texts']

    vectorizer_resumes = resumes_data['vectorizer']
    vectorizer_jd = jd_data['vectorizer']

    # Use the same tokenizer for semantic and ranking models to ensure consistency
    tokenizer = Tokenizer(num_words=5000)
    tokenizer.fit_on_texts(X_resumes + X_jd)

    # Preprocess the text data
    X_resumes_preprocessed = preprocess_texts(X_resumes, tokenizer)
    X_jd_preprocessed = preprocess_texts(X_jd, tokenizer)

    model_scores = {
        'cosine_similarity_model.pkl': evaluate_cosine_similarity_model(X_resumes, X_jd, vectorizer_resumes, vectorizer_jd),
        'semantic_similarity_model.h5': evaluate_semantic_similarity_model(X_resumes_preprocessed, X_jd_preprocessed),
        'siamese_model.h5': evaluate_siamese_model(X_resumes_preprocessed, X_jd_preprocessed),
        'ranking_model.h5': evaluate_ranking_model(X_resumes_preprocessed, X_jd_preprocessed)
    }

    # Select the best model based on the evaluation metrics
    best_model_name = max(model_scores, key=model_scores.get)
    
    # Create the 'models/' directory if it doesn't exist
    os.makedirs('models', exist_ok=True)
    
    # Save the best model
    best_model_path = os.path.join('models', 'best_model')
    if best_model_name.endswith('.pkl'):
        best_model = joblib.load(f'models/{best_model_name}')
        joblib.dump(best_model, f'{best_model_path}.pkl')
    else:
        best_model = load_model(f'models/{best_model_name}')
        best_model.save(f'{best_model_path}.h5')

    print(f"The best model is {best_model_name} and has been saved as {best_model_path}.")
