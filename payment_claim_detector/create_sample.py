import pandas as pd
import os

# Create data directory if it doesn't exist
os.makedirs('data/raw', exist_ok=True)

# Create sample register data
data = {
    'Claim Number': ['12345', '67890', '11111'],
    'Claimant Last Name': ['Smith', 'Johnson', 'Brown'],
    'Claimant First Name': ['John', 'Jane', 'Bob'],
    'Amount Issued': [1000.00, 500.00, 750.00],
    'Payment Description': ['Medical Payment', 'Indemnity Payment', 'Medical Services'],
    'Check Date': ['2026-03-28', '2026-03-29', '2026-03-30'],
    'Payment ID': ['PAY001', 'PAY002', 'PAY003'],
    'Jurisdiction': ['NV', 'CO', 'NV'],
    'Examiner': ['Alice', 'Bob', 'Charlie'],
    'Claim Type': ['Medical', 'Indemnity', 'Medical']
}

df = pd.DataFrame(data)
df.to_excel('data/raw/sample_register.xlsx', index=False)
print('Sample register file created at data/raw/sample_register.xlsx')