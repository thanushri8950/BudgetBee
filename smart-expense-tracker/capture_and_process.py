import cv2
import easyocr
import csv
import re  # <--- Add this line

# --- Step 1: Image Loading and Preprocessing ---
print("Step 1: Loading and preprocessing the image...")
image = cv2.imread('receipt_image.jpg') 
if image is None:
    print("Error: Could not open the image file. Please check the name and path.")
    exit()

gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
thresh_image = cv2.adaptiveThreshold(gray_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
print("Image preprocessing complete.")

# --- Step 2: Text Extraction with EasyOCR ---
print("\nStep 2: Initializing EasyOCR and extracting text...")
reader = easyocr.Reader(['en'])
results = reader.readtext(thresh_image)
print("Text extraction complete.")

# --- Step 3: Data Parsing ---
print("\nStep 3: Parsing extracted data...")
total_amount = None
vendor_name = None
items_list = []

# Simple parsing logic
# --- New, more robust logic to find individual items ---
items_list = []
# You can use this to stop searching for items once you hit the total
found_total = False
for i, (bbox, text, prob) in enumerate(results):
    if "TOTAL" in text.upper():
        found_total = True

    # We will assume a price is a float and is either on the same line
    # or the next line. We'll skip adding items after the 'TOTAL' line.
    if not found_total and prob > 0.5:
        # Simple check: Does the item's text not contain only digits?
        # And is the next line a potential number?
        try:
            potential_price_text = results[i+1][1]
            # Use regular expression to find a number with a decimal point
            if re.match(r'^\d+\.\d{2}$', potential_price_text.strip()):
                price = float(potential_price_text)
                items_list.append({
                    'item': text,
                    'price': price
                })
        except (ValueError, IndexError):
            continue

    # Find Items List
    try:
        if i + 1 < len(results):
            next_text = results[i+1][1].replace('$', '').strip()
            if next_text.replace('.', '', 1).isdigit():
                items_list.append({
                    'item': text,
                    'price': float(next_text)
                })
    except (ValueError, IndexError):
        continue

# Find Vendor Name (simple logic)
if len(results) > 0:
    vendor_name = results[0][1]

print(f"Vendor Name: {vendor_name}")
print(f"Total Amount: {total_amount}")
print("Items Found:")
for item in items_list:
    print(f"- {item['item']}: {item['price']}")
    
print("Data parsing complete.")

# --- Step 4: Saving to a CSV File ---
print("\nStep 4: Saving data to CSV file...")
csv_file_path = 'expense_items.csv'
headers = ['item', 'price']

with open(csv_file_path, 'w', newline='') as file:
    writer = csv.DictWriter(file, fieldnames=headers)
    writer.writeheader()
    writer.writerows(items_list)

print("Data successfully saved to expense_items.csv.")
