import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import csv
import json
import os

class ConfigurationCheckerApp:
    def __init__(self, master):
        self.master = master
        master.title("OCPP Configuration Comparison Tool")
        master.geometry("1200x800")
        master.configure(bg='#f0f0f0')

        # Style
        self.style = ttk.Style()
        self.style.configure('TFrame', background='#f0f0f0')
        self.style.configure('TLabel', background='#f0f0f0', font=('Arial', 10))
        self.style.configure('TButton', font=('Arial', 10))
        
        # Default Configuration
        self.default_config = {
            "websocketUrl": "ws://192.168.20.150:6969",
            "chargePointId": "STATION_001",
            "centralSystemUrl": "ws://central.system.url",
            "heartbeatInterval": "60",
            "reconnectTimeout": "30",
        }

        # Create UI
        self.create_ui()

    def create_ui(self):
        # Main Container
        main_container = ttk.Frame(self.master, padding="10 10 10 10")
        main_container.pack(fill=tk.BOTH, expand=True)

        # Configuration Input Section
        config_frame = ttk.LabelFrame(main_container, text="JSON Configuration")
        config_frame.pack(fill=tk.X, pady=10)

        # JSON Configuration Text Area
        self.json_text = tk.Text(config_frame, height=10, width=120, font=('Courier', 10))
        self.json_text.pack(padx=10, pady=10, fill=tk.X)
        self.json_text.insert(tk.END, json.dumps(self.default_config, indent=2))

        # Button Frame
        button_frame = ttk.Frame(config_frame)
        button_frame.pack(pady=5)

        # Update Configuration Button
        update_btn = ttk.Button(button_frame, text="Update Configuration", command=self.update_configuration)
        update_btn.pack(side=tk.LEFT, padx=5)

        # Reset Button
        reset_btn = ttk.Button(button_frame, text="Reset All", command=self.reset_all)
        reset_btn.pack(side=tk.LEFT, padx=5)

        # File Upload Section
        upload_frame = ttk.LabelFrame(main_container, text="Upload Configuration File")
        upload_frame.pack(fill=tk.X, pady=10)

        # Button Frame for Upload
        upload_button_frame = ttk.Frame(upload_frame)
        upload_button_frame.pack(padx=10, pady=10)

        # Upload and Reset Buttons
        upload_btn = ttk.Button(upload_button_frame, text="Select CSV File", command=self.upload_file)
        upload_btn.pack(side=tk.LEFT, padx=5)

        reset_upload_btn = ttk.Button(upload_button_frame, text="Reset Upload", command=self.reset_upload)
        reset_upload_btn.pack(side=tk.LEFT, padx=5)

        # Results Section
        results_frame = ttk.LabelFrame(main_container, text="Comparison Results")
        results_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Treeview for Results
        self.results_tree = ttk.Treeview(results_frame, 
            columns=('Parameter', 'JSON Value', 'CSV Value', 'Status'), 
            show='headings'
        )
        
        # Configure columns
        self.results_tree.heading('Parameter', text='Parameter')
        self.results_tree.heading('JSON Value', text='JSON Value')
        self.results_tree.heading('CSV Value', text='CSV Value')
        self.results_tree.heading('Status', text='Status')
        
        self.results_tree.column('Parameter', width=150, anchor='center')
        self.results_tree.column('JSON Value', width=200, anchor='center')
        self.results_tree.column('CSV Value', width=200, anchor='center')
        self.results_tree.column('Status', width=100, anchor='center')

        # Scrollbar for Treeview
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_tree.configure(yscroll=scrollbar.set)
        
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Color tags for treeview
        self.results_tree.tag_configure('match', background='#90EE90')  # Light Green
        self.results_tree.tag_configure('mismatch', background='#FFB6C1')  # Light Red
        self.results_tree.tag_configure('extra', background='#87CEFA')  # Light Blue

    def update_configuration(self):
        """Update the default configuration from the text widget"""
        try:
            updated_config = json.loads(self.json_text.get("1.0", tk.END))
            self.default_config = updated_config
            
            # Reset everything after configuration update
            self.reset_all()
            
            messagebox.showinfo("Success", "Configuration updated successfully!")
        except json.JSONDecodeError:
            messagebox.showerror("Error", "Invalid JSON format")

    def reset_upload(self):
        """Reset the uploaded file and results"""
        # Clear the results treeview
        for i in self.results_tree.get_children():
            self.results_tree.delete(i)

    def reset_all(self):
        """Reset both configuration and upload"""
        # Reset JSON configuration to default
        self.json_text.delete('1.0', tk.END)
        self.json_text.insert(tk.END, json.dumps(self.default_config, indent=2))
        
        # Clear the results treeview
        for i in self.results_tree.get_children():
            self.results_tree.delete(i)

    def upload_file(self):
        """Upload and process CSV file"""
        file_path = filedialog.askopenfilename(
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        
        if not file_path:
            return

        try:
            # Clear previous results
            for i in self.results_tree.get_children():
                self.results_tree.delete(i)

            # Read and process CSV
            self.process_csv(file_path)

        except Exception as e:
            messagebox.showerror("Error", f"Error processing file: {str(e)}")

    def process_csv(self, file_path):
        """Process CSV and compare with JSON configuration"""
        # Read CSV
        with open(file_path, 'r', encoding='utf-8') as csvfile:
            csv_reader = csv.reader(csvfile, delimiter=';')
            
            # Skip header if exists
            next(csv_reader, None)
            
            # Dictionary to track processed parameters
            processed_params = {}

            # Process CSV rows
            for row in csv_reader:
                if len(row) < 3:
                    continue
                
                station_name = row[0].strip()
                parameter = row[1].strip()
                csv_value = row[2].strip()

                # Strip the extra commas from CSV values
                if csv_value.endswith(','):
                    csv_value = csv_value.rstrip(',')

                # Store the parameter and its value
                processed_params[parameter] = csv_value

            # Compare with JSON configuration
            for json_param, json_value in self.default_config.items():
                # Convert both to strings for comparison
                json_value_str = str(json_value).strip()
                
                if json_param in processed_params:
                    csv_value = processed_params[json_param]
                    
                    # Only mark as 'match' when the values are exactly equal
                    if csv_value.strip() == json_value_str:
                        self.results_tree.insert('', 'end', 
                            values=(json_param, json_value_str, csv_value, 'Match'), 
                            tags=('match',)
                        )
                    else:
                        self.results_tree.insert('', 'end', 
                            values=(json_param, json_value_str, csv_value, 'Mismatch'), 
                            tags=('mismatch',)
                        )
                else:
                    # Parameter not found in CSV
                    self.results_tree.insert('', 'end', 
                        values=(json_param, json_value_str, 'N/A', 'Missing'), 
                        tags=('extra',)
                    )

            # Check for extra parameters in CSV
            for csv_param, csv_value in processed_params.items():
                if csv_param not in self.default_config:
                    self.results_tree.insert('', 'end', 
                        values=(csv_param, 'N/A', csv_value, 'Extra'), 
                        tags=('extra',)
                    )

def main():
    root = tk.Tk()
    app = ConfigurationCheckerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
