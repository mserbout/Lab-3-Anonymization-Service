import pandas as pd
import numpy as np
from flask import Flask, request, jsonify
from pyope.ope import OPE
from io import BytesIO
import os
import random
import scipy.stats
import string
import matplotlib.pyplot as plt
import seaborn as sns
import base64

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

    def Deidentification(self, attributes_to_drop):
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
                    
                    # Perturb numerical data for specified columns
                    self.perturb_numerical_data(group, columns)
                    
                    # Micro-aggregate numerical data for specified columns
                    self.micro_aggregate(group, columns)
                    
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

    def micro_aggregate(self, group, columns, group_size=3):
        # Sort the group
        group.sort_values(by=columns, inplace=True)

        # Create a list for the micro-aggregated groups
        micro_aggregated_groups = []

        # Split the group into sub-groups of size 'group_size'
        for i in range(0, len(group), group_size):
            sub_group = group[i:i+group_size]

            # Calculate the mean of the sub-group for the specified columns
            for column in columns:
                if np.issubdtype(sub_group[column].dtype, np.number):
                    mean = sub_group[column].mean()

                    # Replace each value in the sub-group with the mean
                    sub_group[column] = mean

            # Append the sub-group to the list of micro-aggregated groups
            micro_aggregated_groups.append(sub_group)

        # Concatenate all the micro-aggregated groups into a new DataFrame
        return pd.concat(micro_aggregated_groups)



    def is_k_anonymized(self, k, columns):
        # Check if the dataset already satisfies k-anonymity for the specified columns
        for i in range(0, len(self.dataset), k):
            group = self.dataset[i:i+k]
            unique_combinations = group[columns].drop_duplicates()
            if len(unique_combinations) < k:
                return False
        return True

    
    def perturb_numerical_data(self, group, columns):
        # Add your perturbation methods for numerical data here
        for column in columns:
            if np.issubdtype(group[column].dtype, np.number):
                #Add random noise to each numerical value
                noise = np.random.normal(0, 1, len(group))
                group[column] += noise
                
                #Add a random constant to each numerical value
                # constant = np.random.randint(-5, 5)
                # group[column] += constant

    def l_diversity(self, l, sensitive_attribute):
        if self.dataset is not None:
            try:
                if self.is_l_diverse(l, sensitive_attribute):
                    return "Dataset already satisfies l-diversity for the sensitive attribute."

                self.dataset.sort_values(by=sensitive_attribute, inplace=True)
                
                diversified_groups = []
                
                unique_sensitive_values = self.dataset[sensitive_attribute].unique()
                for value in unique_sensitive_values:
                    group = self.dataset[self.dataset[sensitive_attribute] == value]
                    if len(group) >= l:
                        diversified_groups.append(group.sample(n=l))
                    else:
                        diversified_groups.append(group)

                self.dataset = pd.concat(diversified_groups)
                
                return "Data diversified successfully."
            except Exception as e:
                return str(e)
        else:
            return "No dataset imported."

    def is_l_diverse(self, l, sensitive_attribute):
        unique_sensitive_values = self.dataset[sensitive_attribute].unique()
        for value in unique_sensitive_values:
            group = self.dataset[self.dataset[sensitive_attribute] == value]
            if len(group[sensitive_attribute].unique()) < l:
                return False
        return True


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

@app.route("/Deidentification", methods=["POST"])
def Deidentification_route():
    try:
        data = request.get_json()
        attributes_to_drop = data.get("attributes_to_drop")

        # Call the Deidentification function and return the result
        result = service.Deidentification(attributes_to_drop)
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


@app.route("/l_diversity", methods=["POST"])
def l_diversity():
    try:
        data = request.get_json()
        l = data.get("l")
        sensitive_attribute = data.get("sensitive_attribute")
        return service.l_diversity(l, sensitive_attribute)
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

@app.route("/plot_data_distributions", methods=["POST"])
def plot_data_distributions():
    try:
        data = request.get_json()
        column = data.get("column")
        
        if column not in service.dataset.columns:
            return jsonify({"message": f"Column '{column}' not found in the dataset."})

        # Plot the original data distribution
        plt.figure(figsize=(16, 8))
        plt.subplot(1, 2, 1)
        if np.issubdtype(service.dataset[column].dtype, np.number):
            sns.histplot(service.dataset[column], kde=True)
            plt.xlabel(column)
            plt.ylabel("Frequency")
            plt.title(f"Original Distribution of {column}")
        else:
            sns.countplot(x=column, data=service.dataset)
            plt.xlabel(column)
            plt.ylabel("Count")
            plt.title(f"Original Distribution of {column}")

        # Plot the anonymized data distribution
        plt.subplot(1, 2, 2)
        modified_column = service.dataset[column] + 1  # Modify as needed
        if np.issubdtype(modified_column.dtype, np.number):
            sns.histplot(modified_column, kde=True)
            plt.xlabel(column)
            plt.ylabel("Frequency")
            plt.title(f"Anonymized Distribution of {column}")
        else:
            sns.countplot(x=modified_column, data=service.dataset)
            plt.xlabel(column)
            plt.ylabel("Count")
            plt.title(f"Anonymized Distribution of {column}")

        # Save the plot to a BytesIO object
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        
        # Return the image as a base64 encoded string
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    except Exception as e:
        return str(e)

if __name__ == "__main__":
    app.run(debug=True)