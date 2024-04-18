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
                #self.dataset['Pseudonym'] = np.random.randint(100000, 999999, num_records)
                #self.dataset['Pseudonym'] = [self.ope.encrypt(str(i)) for i in range(1, num_records + 1)]
                return "Data anonymized successfully."
            except Exception as e:
                return str(e)
        else:
            return "No dataset imported."

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


    def show_results(self):
        if self.dataset is not None:
            return self.dataset.to_json()
        else:
            return "No results."

service = Anonymization()

@app.route("/")
def index():
    with open("index.html", "r") as file:
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
        #file_path = "uploaded_dataset.csv"
        #file.save(file_path)
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

@app.route("/create_dataset", methods=["POST"])
def create_dataset():
    try:
        data = request.json.get("data")
        service.dataset = pd.DataFrame(data)
        return "Dataset created successfully."
    except Exception as e:
        return str(e)

@app.route("/anonymize_data_kanonymity", methods=["POST"])
def anonymize_data_kanonymity():
    try:
        k = request.json.get("k")
        return "Data anonymized with k-anonymity successfully."
    except Exception as e:
        return str(e)
    
    


if __name__ == "__main__":
    app.run(debug=True)
