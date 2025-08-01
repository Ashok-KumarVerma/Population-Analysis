import pandas as pd

# Load dataset
file_path = "population_data.csv"  # Replace with actual filename
df = pd.read_csv(file_path)

# Convert Wide Format to Long Format
df_long = df.melt(id_vars=["State"], 
                  var_name="Year_Population", 
                  value_name="Population")

# Extract Year and Category
df_long["Year"] = df_long["Year_Population"].str.extract(r'(\d{4})')  # Extract year
df_long["Category"] = df_long["Year_Population"].str.extract(r'_(Persons|Male|Female)')  # Extract category

# Pivot Table to get separate columns for Male, Female, and Total Population
df_final = df_long.pivot_table(index=["State", "Year"], columns="Category", values="Population").reset_index()

# Rename columns
df_final.columns = ["State", "Year", "Female", "Male", "Persons"]

# Convert Year to Integer
df_final["Year"] = df_final["Year"].astype(int)

# Save Cleaned Data
df_final.to_csv("cleaned_population_data.csv", index=False)

print("✅ Data cleaned successfully! Check 'cleaned_population_data.csv'")
