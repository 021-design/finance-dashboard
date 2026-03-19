import pandas as pd

# Load dataset
df = pd.read_excel("bank_transactions.xlsx")

# Print all column names clearly
print("Columns:", df.columns.tolist())

# Rename columns for easier use
df.columns = df.columns.str.strip()  # remove extra spaces

# Keep only useful columns
df = df[['DATE', 'TRANSACTION DETAILS', 'WITHDRAWAL AMT', 'DEPOSIT AMT', 'BALANCE AMT']]
# Drop rows where transaction details is missing
df = df.dropna(subset=['TRANSACTION DETAILS'])
# Create a category using keyword matching
def categorize(description):
    desc = str(description).upper()
    if any(word in desc for word in ['SWIGGY', 'ZOMATO', 'FOOD', 'RESTAURANT', 'CAFE']):
        return 'Food & Dining'
    elif any(word in desc for word in ['UBER', 'OLA', 'PETROL', 'FUEL', 'IRCTC', 'RAILWAY']):
        return 'Transport'
    elif any(word in desc for word in ['NETFLIX', 'AMAZON', 'HOTSTAR', 'SPOTIFY', 'OTT']):
        return 'Entertainment'
    elif any(word in desc for word in ['ELECTRICITY', 'WATER', 'BILL', 'RECHARGE', 'MOBILE']):
        return 'Utilities'
    elif any(word in desc for word in ['SALARY', 'PAYROLL', 'INCOME']):
        return 'Income'
    elif any(word in desc for word in ['ATM', 'CASH']):
        return 'Cash Withdrawal'
    elif any(word in desc for word in ['TRANSFER', 'TRF', 'NEFT', 'IMPS', 'UPI']):
        return 'Transfer'
    else:
        return 'Others'

# Apply categorization
df['Category'] = df['TRANSACTION DETAILS'].apply(categorize)

# Show result
print("\n✅ Categorized Data:")
print(df[['TRANSACTION DETAILS', 'Category']].head(20).to_string())

# Show category counts
print(df[['TRANSACTION DETAILS', 'Category']].head(20).to_string()) 
print(df['Category'].value_counts())

# Save cleaned data
df.to_csv("cleaned_transactions.csv", index=False)
print("\n💾 Saved as cleaned_transactions.csv")