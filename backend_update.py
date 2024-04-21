import pandas as pd
import numpy as np
from flask import Flask, request, jsonify
from pyope.ope import OPE
from io import BytesIO
import os

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

    def anonymize_data(self):
        if self.dataset is not None:
            try:
                # drop the first column (the identifier)
                self.dataset.drop(columns=self.dataset.columns[0], inplace=True)
                num_records = len(self.dataset)
                
                # Use OPE to encrypt the sequential numbers
                encrypted_ids = []
                for i in range(1, num_records + 1):
                    
                    plaintext = str(i)
                    plaintext_int = int(plaintext)  # Convert plaintext to integer
                    ciphertext = self.ope.encrypt(plaintext_int)
                    encrypted_ids.append(ciphertext)
                    
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
                    
                    # Replace each value in the group with the mean (for numerical data) or mode (for categorical data)
                    for column in columns:
                        if np.issubdtype(group[column].dtype, np.number):
                            group[column] = pd.cut(group[column], bins=k).astype(str)
                        else:
                            group[column] = group[column].mode()[0]
                    
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
        """
        Check if the dataset already satisfies k-anonymity for the specified columns.
        """
        group_counts = self.dataset.groupby(columns).size()
        return all(count >= k for count in group_counts)



    def generalize_numeric_data(self, attribute, bins):
        if self.dataset is not None:
            if attribute in self.dataset.columns:
                try:
                    self.dataset[attribute] = pd.to_numeric(self.dataset[attribute], errors='coerce')
                    self.dataset[attribute] = pd.cut(self.dataset[attribute], bins=bins).astype(str) 
                    
                    return "Numeric data generalized successfully."
                except Exception as e:
                    return str(e)
            else:
                return f"Attribute '{attribute}' not found in the dataset."
        else:
            return "No dataset imported."
        
    
    def perturb_numeric_data(self, attributes, noise_scale=0.3):
        if self.dataset is not None:
            try:
                for attr in attributes:
                    if attr in self.dataset.columns:
                        noise = np.random.normal(scale=noise_scale, size=len(self.dataset))
                        # Add the noise to the attribute values
                        self.dataset[attr] = self.dataset[attr] + noise
                    else:
                        return f"Attribute '{attr}' not found in the dataset."
                return "Numeric data perturbed successfully."
            except Exception as e:
                return str(e)
        else:
            return "No dataset imported."


    def generalize_selected_categories(self, attribute, categories, new_name):
        if self.dataset is not None:
            if attribute in self.dataset.columns:
                try:
                    # Replace the selected categories with the new name
                    self.dataset.loc[self.dataset[attribute].isin(categories), attribute] = new_name
                    
                    return "Selected categories generalized successfully."
                except Exception as e:
                    return str(e)
            else:
                return f"Attribute '{attribute}' not found in the dataset."
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

@app.route("/anonymize_data", methods=["POST"])
def anonymize_data():
    return service.anonymize_data()

@app.route("/generalize_numeric_data", methods=["POST"])
def generalize_numeric_data():
    try:
        data = request.get_json()
        attribute = data.get("attribute")
        bins = data.get("bins")
        return service.generalize_numeric_data(attribute, bins)
    except Exception as e:
        return str(e)
    
@app.route("/perturb_numeric_data", methods=["POST"])
def perturb_numeric_data():
    try:
        data = request.get_json()
        attributes = data.get("attributes")
        noise_scale = data.get("noise_scale", 0.3)
        return service.perturb_numeric_data(attributes, noise_scale)
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

@app.route("/generalize_selected_categories", methods=["POST"])
def generalize_selected_categories():
    try:
        data = request.get_json()
        attribute = data.get("attribute")
        categories = data.get("categories")
        new_name = data.get("new_name")
        return service.generalize_selected_categories(attribute, categories, new_name)
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
