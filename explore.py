import pandas as pd

# Load the dataset
df = pd.read_excel("bank_transactions.xlsx")

# See the first 5 rows
print("📄 First 5 rows:")
print(df.head())

# See column names
print("\n📋 Columns:", df.columns.tolist())

# See shape (rows, columns)
print("\n📐 Shape:", df.shape)

# Check for missing values
print("\n❓ Missing values:")
print(df.isnull().sum())