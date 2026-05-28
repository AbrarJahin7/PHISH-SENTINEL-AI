import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report

# --- 1. Load data ---
df = pd.read_csv("emails.csv")

TEXT_COL = "Email Text"     # CHANGE to your dataset's text column
LABEL_COL = "Email Type"  # CHANGE to your dataset's label column

df = df.dropna(subset=[TEXT_COL, LABEL_COL])   # remove empty rows
X = df[TEXT_COL].astype(str)                   # the emails (input)
y = df[LABEL_COL]                              # the labels (answer)

# --- 2. Split: learn on 80%, test honestly on the unseen 20% ---
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42       # random_state makes it repeatable
)

# --- 3. Turn text into numbers ---
vectorizer = TfidfVectorizer(stop_words="english", max_features=5000)
X_train_vec = vectorizer.fit_transform(X_train)  # learn vocabulary FROM TRAINING ONLY
X_test_vec = vectorizer.transform(X_test)         # apply same vocabulary to test

# --- 4. Train the classifier ---
model = LogisticRegression(max_iter=1000)
model.fit(X_train_vec, y_train)                   # this is the actual "learning"

# --- 5. Check how good it is on data it never saw ---
predictions = model.predict(X_test_vec)
print(classification_report(y_test, predictions))

# --- 6. Save model + vectorizer so the app can reuse them ---
joblib.dump(model, "model.pkl")
joblib.dump(vectorizer, "vectorizer.pkl")
print("Saved model.pkl and vectorizer.pkl")