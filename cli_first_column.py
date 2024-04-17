import pandas as pd
import numpy as np

class Anonymization_service:
    def __init__(self):
        self.dataset = None

    def importing_database(self, file_path):
        self.dataset = pd.read_csv(file_path)
        print("Database imported successfully.")

    def anonymize_data(self):
        if self.dataset is not None:
            # Remove identifiers or the first column 
            self.dataset.drop(columns=self.dataset.columns[0], inplace=True)
            # Add random pseudonyms
            num_records = len(self.dataset)
            self.dataset['Pseudonym'] = np.random.randint(100000, 999999, num_records)
            print("Data anonymized successfully.")
        else:
            print("No dataset imported.")

    def generalize_numeric_data(self, attribute, bins):
        if self.dataset is not None:
            if attribute in self.dataset.columns:
                self.dataset[attribute] = pd.to_numeric(self.dataset[attribute], errors='coerce')
                self.dataset[attribute] = pd.cut(self.dataset[attribute], bins=bins)
                print(f"Numeric data generalized successfully.")
            else:
                print(f"Attribute not found in the dataset.")
        else:
            print("No dataset imported.")

    def show_results(self):
        if self.dataset is not None:
            print(self.dataset.head())  
        else:
            print("No dataset imported.")

    def create_dataset(self):
        print("Enter attribute names (e.g., ID,Name,Age,Income):")
        attributeNames = input().split(',')

        # Create dictionary to store data
        data = {}
        for attribute in attributeNames:
            print(f"Enter values for the attribute '{attribute}' separated by commas:")
            values = input().split(',')
            data[attribute] = values

        # Create DataFrame 
        self.dataset = pd.DataFrame(data)
        print("Dataset created successfully.")


    def display_menu(self):
        while True:
            print("\nMenu:")
            print("1. Import Database")
            print("2. Create Dataset")
            print("3. Anonymize Data")
            print("4. Generalize Numeric Data")
            print("5. Show Results")
            print("6. Exit")

            choice = input("Enter your choice: ")

            if choice == '1':
                file_path = input("Enter the file path of the database: ")
                self.importing_database(file_path)
            elif choice == '2':
                self.create_dataset()
                
            elif choice == '3':
                self.anonymize_data()
                
            elif choice == '4':
                attribute = input("Enter the name of the numeric attribute to generalize: ")
                bins_str = input("Enter the bin edges separated by spaces (e.g., '0 10 20'): ")
                # Remove single quotes if present and split into individual bin edges
                bins = [float(x) for x in bins_str.replace("'", "").split()]
                self.generalize_numeric_data(attribute, bins)
                
            elif choice == '5':
                self.show_results()
    
            elif choice == '6':
                print("Exit")
                break
            else:
                print("Invalid choice. Please try again.")


    

if __name__ == "__main__":
    service = Anonymization_service()
    service.display_menu()
