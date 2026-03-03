import pandas as pd

def extract_characters_from_excel():
    """Extract all Chinese characters from the Excel file"""
    df = pd.read_excel('5000-common-characters.xls', header=None)
    
    characters = []
    char_set = set()  # To avoid duplicates
    
    # Go through all columns and rows to find characters
    for col in range(df.shape[1]):
        for row in range(df.shape[0]):
            value = df.iloc[row, col]
            if pd.notna(value) and isinstance(value, str) and len(value.strip()) == 1:
                char = value.strip()
                # Check if it's a Chinese character
                if '\u4e00' <= char <= '\u9fff' and char not in char_set:
                    characters.append(char)
                    char_set.add(char)
    
    return characters

# Extract all characters
print("Extracting characters from Excel file...")
characters = extract_characters_from_excel()
print(f"Found {len(characters)} unique Chinese characters")

# Create CSV with characters and placeholder pinyin/definitions
csv_data = []
for i, char in enumerate(characters):
    csv_data.append({
        'character': char,
        'pinyin': f'pinyin_{i+1}',  # Placeholder
        'definition': f'definition for {char}'  # Placeholder
    })

# Save to CSV
df_output = pd.DataFrame(csv_data)
df_output.to_csv('characters_extracted.csv', index=False, encoding='utf-8')
print(f"Created characters_extracted.csv with {len(csv_data)} entries")
print("Note: This file contains placeholder pinyin and definitions.")
print("You'll need to add real pinyin and definitions for a proper quiz.")

# Show first 10 characters as example
print("\nFirst 10 characters:")
for i in range(min(10, len(characters))):
    print(f"{i+1}. {characters[i]}")