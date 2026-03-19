import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import pickle

# Load cleaned data
df = pd.read_csv("cleaned_transactions.csv")

# Remove rows where category is 'Others' for better training
df_train = df[df['Category'] != 'Others']

print(f"✅ Training on {len(df_train)} labeled transactions")
print("📊 Category counts:")
print(df_train['Category'].value_counts())

# Features (X) = transaction description text
# Label (y) = category
X = df_train['TRANSACTION DETAILS'].astype(str)
y = df_train['Category']

# Convert text to numbers using TF-IDF
vectorizer = TfidfVectorizer(max_features=500)
X_vectorized = vectorizer.fit_transform(X)

# Split into training and testing sets (80% train, 20% test)
X_train, X_test, y_train, y_test = train_test_split(
    X_vectorized, y, test_size=0.2, random_state=42
)

print(f"\n🔧 Training model...")

# Train Random Forest model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Test the model
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)

print(f"\n🎯 Model Accuracy: {accuracy * 100:.2f}%")
print("\n📋 Detailed Report:")
print(classification_report(y_test, y_pred))

# Save model and vectorizer
pickle.dump(model, open("model/model.pkl", "wb"))
pickle.dump(vectorizer, open("model/vectorizer.pkl", "wb"))
print("\n💾 Model saved successfully!")