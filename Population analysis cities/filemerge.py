import pandas as pd

df1 = pd.read_csv("cities_r2.csv")
df2 = pd.read_csv("cleaned_population_data.csv")

# Ensure state_name columns are in lowercase and trimmed
df1["state_name"] = df1["state_name"].str.strip().str.lower()
df2["state_name"] = df2["state_name"].str.strip().str.lower()

# Merge Data
merged_df = pd.merge(df1, df2, on="state_name", how="left")

# Debugging - Count Rows
print(f"Original DF1 Rows: {df1.shape[0]}")
print(f"Original DF2 Rows: {df2.shape[0]}")
print(f"Merged DF Rows: {merged_df.shape[0]}")

# Save merged file
merged_df.to_csv("merged_data.csv", index=False)
print("Merged file saved as merged_data.csv")
