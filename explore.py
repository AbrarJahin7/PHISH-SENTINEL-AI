import pandas as pd

df = pd.read_csv("emails.csv")
print("Shape (rows, columns):", df.shape)
print("\nColumn names:", list(df.columns))
print("\nFirst 3 rows:")
print(df.head(3))
print("\nHow many of each label:")
print(df.iloc[:, -1].value_counts())   # last column is usually the label