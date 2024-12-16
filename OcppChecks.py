import tkinter as tk
from tkinter import filedialog, ttk
import pandas as pd
import json
import os
 
class CMGQualityChecker:
    def __init__(self, root):
        self.root = root
        self.root.title("CMG Quality Checker")
        self.root.configure(bg="#333333")
        # Center the window
        self.center_window()
        # Variables
        self.json_data = {}
        self.file_data = pd.DataFrame()
        self.results = pd.DataFrame()
        self.status_text = tk.StringVar()
        self.status_text.set("")
        self.result_count_text = tk.StringVar()
        self.result_count_text.set("Total = 0 | Matched = 0 | Mismatch = 0 | Missing = 0")
 
        # Header
        header_label = tk.Label(root, text="Welcome to the CMG Quality Checker", 
                                bg="#333333", fg="white", font=("Helvetica", 14, "bold"))
        header_label.pack(pady=10)
 
        # Style for ttk buttons
        style = ttk.Style()
        style.configure("Dark.TButton", background="#1C1C1C", foreground="white", font=("Helvetica", 10))
        style.configure("Blue.TButton", background="#0078D7", foreground="white", font=("Helvetica", 10))
 
        # Buttons
        button_frame = tk.Frame(root, bg="#333333")
        button_frame.pack(pady=10)
 
        self.json_button = ttk.Button(button_frame, text="Upload JSON Reference File", command=self.upload_json, style="Dark.TButton")
        self.json_button.grid(row=0, column=0, padx=10)
 
        self.csv_button = ttk.Button(button_frame, text="Upload CSV/Excel File", command=self.upload_csv, style="Dark.TButton")
        self.csv_button.grid(row=0, column=1, padx=10)
 
        self.run_button = ttk.Button(button_frame, text="Run Check", command=self.run_check, style="Blue.TButton")
        self.run_button.grid(row=0, column=2, padx=10)
 
        self.export_button = ttk.Button(button_frame, text="Export Results", command=self.export_results, style="Dark.TButton")
        self.export_button.grid(row=0, column=3, padx=10)
 
        # Status Message Label
        self.status_label = tk.Label(root, textvariable=self.status_text, bg="#333333", fg="yellow", font=("Helvetica", 10))
        self.status_label.pack(pady=5)
 
        # Filter Frame
        filter_frame = tk.Frame(root, bg="#333333")
        filter_frame.pack(pady=5)
 
        filter_label = tk.Label(filter_frame, text="Filter by Status:", bg="#333333", fg="white", font=("Helvetica", 10))
        filter_label.grid(row=0, column=0, padx=5)
 
        self.filter_combobox = ttk.Combobox(filter_frame, values=["All", "Matched", "Mismatch", "Missing"], state="readonly")
        self.filter_combobox.current(0)
        self.filter_combobox.grid(row=0, column=1, padx=5)
        self.filter_combobox.bind("<<ComboboxSelected>>", self.apply_filter)
 
        # Result Count Label
        self.result_count_label = tk.Label(root, textvariable=self.result_count_text, bg="#333333", fg="white", font=("Helvetica", 9))
        self.result_count_label.pack(pady=5)
 
        # Table (TreeView)
        columns = ("SiteName", "ChargerModel", "Connector", "OcppKey", "JsonValue", "CsvValue", "KeyStatus")
        self.tree = ttk.Treeview(root, columns=columns, show="headings", height=15)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=130)
 
        self.tree.pack(pady=10, fill="both", expand=True)
 
        # Add tags for color coding
        self.tree.tag_configure("Matched", background="#008000")  # Normal green
        self.tree.tag_configure("Mismatch", background="#FF0000")  # Normal red
        self.tree.tag_configure("Missing", background="#FFA500")   # Orange
 
    # Center the window on the screen
    def center_window(self):
        window_width = 900
        window_height = 500
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x_coordinate = (screen_width // 2) - (window_width // 2)
        y_coordinate = (screen_height // 2) - (window_height // 2)
        self.root.geometry(f"{window_width}x{window_height}+{x_coordinate}+{y_coordinate}")
 
    # Upload JSON file
    def upload_json(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            try:
                with open(file_path, "r") as file:
                    self.json_data = json.load(file)
                self.status_text.set("JSON File Uploaded Successfully!")
            except Exception as e:
                self.status_text.set(f"Failed to load JSON: {e}")
 
    # Upload CSV/Excel file
    def upload_csv(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx")])
        if file_path:
            try:
                if file_path.endswith(".csv"):
                    self.file_data = pd.read_csv(file_path, header=None)
                elif file_path.endswith(".xlsx"):
                    self.file_data = pd.read_excel(file_path, header=None)
                self.status_text.set("File Uploaded Successfully!")
            except Exception as e:
                self.status_text.set(f"Failed to load file: {e}")
 
    # Populate table with file data
    def populate_table(self, data):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for _, row in data.iterrows():
            tag = row[6]  # KeyStatus column determines the tag
            self.tree.insert("", "end", values=row.tolist(), tags=(tag,))
        self.update_result_count(data)
 
    # Run check: Compare JSON keys to CSV/Excel values
    def run_check(self):
        if self.json_data and not self.file_data.empty:
            results = []
            for _, row in self.file_data.iterrows():
                try:
                    # Parse the single-column CSV file
                    parts = row[0].split(";")
                    site_name = parts[0].rsplit(" - ", 1)[0]  # Extract SiteName
                    connector = parts[0].rsplit(" - ", 1)[1]  # Extract Connector
                    ocpp_key = parts[1]  # Extract OCPP Key
                    csv_value = parts[2]  # Extract Value
 
                    # Identify Charger Model and JSON Value dynamically
                    charger_model, json_value = self.find_json_value(ocpp_key)
 
                    # Determine Key Status
                    if json_value is None:
                        key_status = "Missing"
                    elif str(json_value) == str(csv_value):
                        key_status = "Matched"
                    else:
                        key_status = "Mismatch"
 
                    results.append((site_name, charger_model, connector, ocpp_key, json_value, csv_value, key_status))
                except Exception as e:
                    print(f"Error processing row: {row} -> {e}")
 
            self.results = pd.DataFrame(results, columns=["SiteName", "ChargerModel", "Connector", "OcppKey", "JsonValue", "CsvValue", "KeyStatus"])
            self.populate_table(self.results)
            self.status_text.set("Check Completed Successfully!")
        else:
            self.status_text.set("Please upload both JSON and CSV/Excel files.")
 
    def find_json_value(self, ocpp_key):
        """
        Search for the ocpp_key in the uploaded JSON data and return the ChargerModel and value.
        """
        for charger_model in self.json_data:
            for model, settings in charger_model.items():
                if ocpp_key in settings:
                    return model, settings[ocpp_key]
        return "Unknown", None
 
    # Export results to a CSV file
    def export_results(self):
        if not self.results.empty:
            file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
            if file_path:
                self.results.to_csv(file_path, index=False)
                self.status_text.set("Results Exported Successfully!")
        else:
            self.status_text.set("No results to export.")
 
    # Apply filter for statuses
    def apply_filter(self, event=None):
        status = self.filter_combobox.get()
        if status == "All":
            filtered_results = self.results
        else:
            filtered_results = self.results[self.results["KeyStatus"] == status]
        self.populate_table(filtered_results)
 
    # Update result counts
    def update_result_count(self, data):
        total = len(data)
        matched = len(data[data["KeyStatus"] == "Matched"])
        mismatch = len(data[data["KeyStatus"] == "Mismatch"])
        missing = len(data[data["KeyStatus"] == "Missing"])
        self.result_count_text.set(f"Total = {total} | Matched = {matched} | Mismatch = {mismatch} | Missing = {missing}")
 
# Main Application
if __name__ == "__main__":
    root = tk.Tk()
    app = CMGQualityChecker(root)
    root.mainloop()