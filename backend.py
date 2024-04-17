import pandas as pd
import numpy as np
from flask import Flask, request, jsonify

app = Flask(__name__)

class AnonymizationService:
    def __init__(self):
        self.dataset = None

    def import_database(self, file_path):
        try:
            self.dataset = pd.read_csv(file_path)
            return "Database imported successfully."
        except Exception as e:
            return str(e)

    def anonymize_data(self):
        if self.dataset is not None:
            try:
                self.dataset.drop(columns=self.dataset.columns[0], inplace=True)
                num_records = len(self.dataset)
                self.dataset['Pseudonym'] = np.random.randint(100000, 999999, num_records)
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
                    self.dataset[attribute] = pd.cut(self.dataset[attribute], bins=bins)
                    return f"Numeric data in '{attribute}' generalized successfully."
                except Exception as e:
                    return str(e)
            else:
                return f"Attribute '{attribute}' not found in the dataset."
        else:
            return "No dataset imported."

    def show_results(self):
        if self.dataset is not None:
            return self.dataset.to_json()
        else:
            return "No results to show."

service = AnonymizationService()

@app.route("/")
def index():
    with open("index.html", "r") as file:
        html_content = file.read()
    return html_content

@app.route("/import_database", methods=["POST"])
def import_database():
    try:
        if "file" not in request.files:
            return "No file part"
        file = request.files["file"]
        if file.filename == "":
            return "No selected file"
        file_path = "uploaded_dataset.csv"
        file.save(file_path)
        return service.import_database(file_path)
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

@app.route("/show_results")
def show_results():
    return service.show_results()

@app.route("/create_own_dataset", methods=["POST"])
def create_own_dataset():
    try:
        data = request.json.get("data")
        # Implement logic to create dataset from provided data
        return "Dataset created successfully."
    except Exception as e:
        return str(e)

@app.route("/anonymize_data_kanonymity", methods=["POST"])
def anonymize_data_kanonymity():
    try:
        k = request.json.get("k")
        # Implement logic to anonymize data with k-anonymity
        return "Data anonymized with k-anonymity successfully."
    except Exception as e:
        return str(e)
    
    

@app.route("/process_csv", methods=["POST"])
def process_csv():
    try:
        if "csv-file" not in request.files:
            return "No file part"
        file = request.files["csv-file"]
        if file.filename == "":
            return "No selected file"
        file_path = "uploaded_dataset.csv"
        file.save(file_path)
        # Process the CSV file here
        # For example, you can read the CSV file and perform some operations
        return "CSV file uploaded and processed successfully."
    except Exception as e:
        return str(e)


@app.route("/process_json", methods=["POST"])
def process_json():
    if request.headers["Content-Type"] == "application/json":
        try:
            data = request.json
            # Process JSON data
            result = {"message": "Data received successfully", "data": data}
            return jsonify(result), 200
        except Exception as e:
            return str(e), 400
    else:
        return "Unsupported Media Type: Content-Type must be 'application/json'", 415

if __name__ == "__main__":
    app.run(debug=True)
