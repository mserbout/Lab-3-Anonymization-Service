import pandas as pd
import numpy as np
from flask import Flask, request, jsonify
from pyope.ope import OPE
from io import BytesIO
import os
import random
import scipy.stats
import string

app = Flask(__name__)

class Anonymization:
    def __init__(self):
        self.dataset = None
        self.ope = OPE(b'encryption_key') 

    def importing_database(self, file):
        try:
            # Check the file type
            filename = file.filename
            extension = os.path.splitext(filename)[1].lower()

            if extension == '.csv':
                # For CSV files
                self.dataset = pd.read_csv(file)
            elif extension in ['.xls', '.xlsx']:
                # For Excel files
                self.dataset = pd.read_excel(file)
            else:
                return "Unsupported file format"

            return "Database imported successfully."
        except Exception as e:
            return str(e)

    def anonymize_data(self, attributes_to_drop):
        if self.dataset is not None:
            try:
                # Check if all attributes exist in the dataset
                for attribute_to_drop in attributes_to_drop:
                    if attribute_to_drop not in self.dataset.columns:
                        return f"Attribute '{attribute_to_drop}' not found in the dataset."

                # Drop the specified attributes
                self.dataset.drop(columns=attributes_to_drop, inplace=True)
                    
                # Encrypt the sequential numbers to create pseudonyms
                num_records = len(self.dataset)
                encrypted_ids = []
                for i in range(1, num_records + 1):
                    plaintext = str(i)
                    plaintext_int = int(plaintext)  # Convert plaintext to integer
                    ciphertext = self.ope.encrypt(plaintext_int)
                    encrypted_ids.append(ciphertext)

                # Add the pseudonym column to the dataset
                self.dataset['Pseudonym'] = encrypted_ids

                return "Data anonymized successfully."
                
            except Exception as e:
                return str(e)
        else:
            return "No dataset imported."
     
    def k_anonymize(self, k, columns):
        if self.dataset is not None:
            try:
                # Check if the dataset already satisfies k-anonymity for the specified columns
                if self.is_k_anonymized(k, columns):
                    return "Dataset already satisfies k-anonymity for the specified columns."

                # If not, perform k-anonymization
                # Sort the dataset
                self.dataset.sort_values(by=columns, inplace=True)
                
                # Create a list for the anonymized groups
                anonymized_groups = []
                
                # Split the dataset into groups of size k
                for i in range(0, len(self.dataset), k):
                    group = self.dataset[i:i+k]
                    
                    # Replace each value in the group with the range (for numerical data) or a category string (for categorical data)
                    for column in columns:
                        if np.issubdtype(group[column].dtype, np.number):
                            min_val = group[column].min()
                            max_val = group[column].max()
                            group[column] = f"[{min_val}-{max_val}]"
                        else:
                            unique_values = group[column].unique()
                            if len(unique_values) > 1:
                                group[column] = '/'.join(unique_values)
                            else:
                                # Replace with a combination of its own value and some other random values from the unique categories in the dataset
                                unique_categories = self.dataset[column].unique()
                                random_categories = np.random.choice(unique_categories, 2, replace=False)
                                group[column] = '/'.join([unique_values[0], *random_categories])
                    
                    # Append the group to the list of anonymized groups
                    anonymized_groups.append(group)
                
                # Concatenate all the anonymized groups into a new DataFrame
                self.dataset = pd.concat(anonymized_groups)
                
                return "Data anonymized successfully."
            except Exception as e:
                return str(e)
        else:
            return "No dataset imported."

    

    def is_k_anonymized(self, k, columns):
        # Check if the dataset already satisfies k-anonymity for the specified columns
        for i in range(0, len(self.dataset), k):
            group = self.dataset[i:i+k]
            unique_combinations = group[columns].drop_duplicates()
            if len(unique_combinations) < k:
                return False
        return True

    def l_diversify(self, l, sensitive_column, quasi_identifier_columns):
        if self.dataset is not None:
            try:
               # Initialize fake data outside the loop
               fake_data = []        
               # Group the dataset by the quasi-identifier columns
               groups = self.dataset.groupby(quasi_identifier_columns)
               # Check l-diversity for each group
               for name, group in groups:
                   unique_values = group[sensitive_column].nunique()
                   print(f"Group: {name}, Unique Values: {unique_values}, l: {l}")
                   if unique_values < l:
                      print("Diversification needed")
                      # Apply diversification techniques
                      # Add spurious logs or noise by inserting fake rows
                      num_fake_rows = l - unique_values  # Calculate the number of fake rows needed
                      print(f"Adding {num_fake_rows} fake rows")
                      # Generate fake data for the fake rows
                      for _ in range(num_fake_rows):
                          fake_row = {}  # Dictionary to store values for the fake row
                          # Generate fake values for each column
                          for column in self.dataset.columns:
                               if column != sensitive_column:
                                   # Generate fake values for non-sensitive columns
                                   # For simplicity, you can use random values or predefined placeholders
                                   fake_row[column] = random.choice(['fake_value_1', 'fake_value_2', 'fake_value_3'])
                               else:
                                   # For the sensitive column, you can use a placeholder
                                   fake_row[column] = 'SENSITIVE_DATA_PLACEHOLDER'
                          # Append the fake row to the list of fake data
                          fake_data.append(fake_row)
               # Convert the list of fake data into a DataFrame
               fake_df = pd.DataFrame(fake_data)
               print("Fake data generated:")
               print(fake_df)
               # Concatenate the original dataset with the fake data
               self.dataset = pd.concat([self.dataset, fake_df], ignore_index=True)
               print("Dataset updated")
               return "Data diversified successfully."
            except Exception as e:
               return str(e)
        else:
            return "No dataset imported."

    def generate_dataset(self, num_rows):
        identifiers = ['User ID']  
        quasi_identifiers = ['Age', 'Gender']  
        sensitive_attributes = ['Income']  
        
        data = {
            'User ID': range(1, num_rows + 1),
            'Age': np.random.randint(18, 65, size=num_rows),
            'Gender': np.random.choice(['Male', 'Female'], size=num_rows),
            'Income': np.random.randint(20000, 100000, size=num_rows),
            'Education': np.random.choice(['High School', 'Bachelor', 'Master', 'PhD'], size=num_rows),
            'Marital Status': np.random.choice(['Single', 'Married', 'Divorced', 'Widowed'], size=num_rows),
            'Region': np.random.choice(['North', 'South', 'East', 'West'], size=num_rows),
            'Employment': np.random.choice(['Employed', 'Unemployed', 'Student', 'Retired'], size=num_rows),
            'Health Status': np.random.choice(['Good', 'Fair', 'Poor'], size=num_rows),
            'Internet Usage': np.random.choice(['High', 'Medium', 'Low'], size=num_rows),
            'Shopping Preference': np.random.choice(['Online', 'In-store', 'Both'], size=num_rows),
            'Hobbies': np.random.choice(['Reading', 'Sports', 'Cooking', 'Gardening'], size=num_rows),
            'Height (cm)': np.random.normal(loc=170, scale=10, size=num_rows),  
            'Weight (kg)': np.random.normal(loc=70, scale=15, size=num_rows), 
            'Number of Children': np.random.randint(0, 5, size=num_rows), 
            'Number of Pets': np.random.randint(0, 3, size=num_rows), 
            'Travel Frequency': np.random.choice(['Rarely', 'Occasionally', 'Frequently'], size=num_rows), 
            'Favorite Food': np.random.choice(['Italian', 'Mexican', 'Chinese', 'Indian'], size=num_rows), 
        }
        
        # Create the DataFrame
        self.dataset = pd.DataFrame(data)

        return "Custom dataset generated successfully."
        
    def show_results(self):
        if self.dataset is not None:
            return self.dataset.to_html()
        else:
            return "No results."

service = Anonymization()

@app.route("/")
def index():
    with open("index_update.html", "r") as file:
        html_content = file.read()
    return html_content

@app.route("/importing_database", methods=["POST"])
def importing_database():
    try:
        if "file" not in request.files:
            return "No file part"
        file = request.files["file"]
        if file.filename == "":
            return "No selected file"
        return service.importing_database(file)
    except Exception as e:
        return str(e)

@app.route("/anonymize", methods=["POST"])
def anonymize_data_route():
    try:
        data = request.get_json()
        attributes_to_drop = data.get("attributes_to_drop")

        # Call the anonymize_data function and return the result
        result = service.anonymize_data(attributes_to_drop)
        return jsonify({"message": result})
    except Exception as e:
        return str(e)

@app.route("/show_results")
def show_results():
    return service.show_results()



@app.route("/k_anonymize", methods=["POST"])
def k_anonymize():
    try:
        data = request.get_json()
        k = data.get("k")
        columns = data.get("columns")
        return service.k_anonymize(k, columns)
    except Exception as e:
        return str(e)

@app.route("/l_diversify", methods=["POST"])
def l_diversify_route():
    try:
        data = request.get_json()
        l = data.get("l")
        sensitive_column = data.get("sensitive_column")
        quasi_identifier_columns = data.get("quasi_identifier_columns", [])
        if not isinstance(quasi_identifier_columns, list):
            return "Quasi-identifier columns must be provided as a list."
        result = service.l_diversify(l, sensitive_column, quasi_identifier_columns)
        return result
    except Exception as e:
        return str(e)

@app.route("/generate_dataset", methods=["POST"])
def generate_dataset():
    try:
        data = request.get_json()
        num_rows = data.get("num_rows")
        response = service.generate_dataset(num_rows)
        return response
    except Exception as e:
        return str(e)

if __name__ == "__main__":
    app.run(debug=True)
