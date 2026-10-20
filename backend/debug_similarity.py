#!/usr/bin/env python3
"""Debug script to analyze similarity scores for problematic pairs."""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from grouping import extract_capitalized_terms, get_shared_capitalized_terms

# Problematic pair 1: Fox News - LeBron/Carmelo
pair1_title1 = "Carmelo Anthony says LeBron James and 76ers deserve respect"
pair1_summary1 = "Carmelo Anthony praised LeBron James and the Philadelphia 76ers in a recent interview, discussing their championship prospects."

pair1_title2 = "NBA has no issue with LeBron James' helicopter commute to games"
pair1_summary2 = "NBA officials stated they have no concerns about LeBron James using a helicopter to commute to games from Newport Beach."

# Problematic pair 2: BBC World - Ukraine
pair2_title1 = "Tennis star Svitolina says emotional toll of Ukraine war affected her career"
pair2_summary1 = "Ukrainian tennis player Elina Svitolina discussed how the ongoing war in Ukraine has taken an emotional toll on her professional career and personal life."

pair2_title2 = "Ukraine says it carried out first drone airlift operation deep in Russian territory"
pair2_summary2 = "Ukraine announced it successfully completed its first drone airlift operation to deliver supplies deep into Russian-occupied territory, marking a new strategy."

def analyze_pair(name, title1, summary1, title2, summary2):
    print(f"\n{'='*60}")
    print(f"Pair: {name}")
    print(f"{'='*60}")

    text1 = f"{title1} {summary1}"
    text2 = f"{title2} {summary2}"

    # Calculate TF-IDF similarity
    vectorizer = TfidfVectorizer(stop_words='english', lowercase=True, max_features=100)
    tfidf_matrix = vectorizer.fit_transform([text1, text2])
    similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])[0][0]

    # Extract shared capitalized terms
    shared_terms = get_shared_capitalized_terms(text1, text2)

    print(f"\nArticle 1 Title: {title1}")
    print(f"Article 1 Summary: {summary1[:80]}...")

    print(f"\nArticle 2 Title: {title2}")
    print(f"Article 2 Summary: {summary2[:80]}...")

    print(f"\nSimilarity Score: {similarity:.4f}")
    print(f"Shared Capitalized Terms ({len(shared_terms)}): {shared_terms}")
    print(f"Threshold (same-publisher): 0.60")
    print(f"Passes threshold? {similarity >= 0.60}")
    print(f"Has 2+ shared terms? {len(shared_terms) >= 2}")
    print(f"Would match with current rule? {similarity >= 0.60 and len(shared_terms) >= 2}")

analyze_pair(
    "Fox News - LeBron/Carmelo",
    pair1_title1, pair1_summary1,
    pair1_title2, pair1_summary2
)

analyze_pair(
    "BBC World - Ukraine",
    pair2_title1, pair2_summary1,
    pair2_title2, pair2_summary2
)
