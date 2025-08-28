import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from typing import Dict, List, Any, Callable, Optional
from datetime import datetime, timedelta
import os

class EditAssignmentDialog(ttk.Toplevel):
    def __init__(self, parent, building_info: Dict[str, Any], current_agent: str, 
                 db_connection, **kwargs):
        """
        Dialog for editing policy assignments
        
        Args:
            parent: Parent widget
            building_info: Building information dictionary
            current_agent: Current agent name
            db_connection: Database connection object
        """
        super().__init__(parent, **kwargs)
        self.building_info = building_info
        self.current_agent = current_agent
        self.db = db_connection
        self.result = None
        
        self.title("Edit Policy Assignment")
        self.geometry("500x300")
        self.resizable(False, False)
        
        # Make dialog modal
        self.transient(parent)
        self.grab_set()
        
        self._create_widgets()
        self._center_window()
    
    def _create_widgets(self):
        """Create the dialog widgets"""
        # Main frame
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Edit Policy Assignment", 
                               font=("Helvetica", 14, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Building info
        info_frame = ttk.LabelFrame(main_frame, text="Building Information", padding=15)
        info_frame.pack(fill=X, pady=(0, 20))
        
        ttk.Label(info_frame, text=f"Code: {self.building_info['building_code']}").pack(anchor=W)
        ttk.Label(info_frame, text=f"Name: {self.building_info['building_name']}").pack(anchor=W)
        ttk.Label(info_frame, text=f"Current Agent: {self.current_agent}").pack(anchor=W)
        
        # Agent selection
        selection_frame = ttk.LabelFrame(main_frame, text="Select New Agent", padding=15)
        selection_frame.pack(fill=X, pady=(0, 20))
        
        ttk.Label(selection_frame, text="New Agent:").pack(anchor=W, pady=(0, 5))
        
        # Get available agents
        agents = self.db.get_agents()
        agent_names = [agent['name'] for agent in agents]
        
        self.agent_var = tk.StringVar(value=self.current_agent)
        self.agent_combo = ttk.Combobox(selection_frame, textvariable=self.agent_var, 
                                       values=agent_names, state="readonly", width=40)
        self.agent_combo.pack(fill=X, pady=(0, 10))
        
        # Notes
        ttk.Label(selection_frame, text="Notes (optional):").pack(anchor=W, pady=(0, 5))
        self.notes_text = tk.Text(selection_frame, height=3, width=50)
        self.notes_text.pack(fill=X)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=X, pady=(20, 0))
        
        ttk.Button(button_frame, text="Cancel", style="secondary.TButton",
                  command=self._on_cancel).pack(side=RIGHT, padx=(10, 0))
        ttk.Button(button_frame, text="Save Changes", style="success.TButton",
                  command=self._on_save).pack(side=RIGHT)
    
    def _center_window(self):
        """Center the dialog on the screen"""
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
    
    def _on_save(self):
        """Handle save button click"""
        new_agent = self.agent_var.get()
        notes = self.notes_text.get("1.0", tk.END).strip()
        
        if not new_agent:
            messagebox.showwarning("Warning", "Please select a new agent")
            return
        
        if new_agent == self.current_agent:
            messagebox.showinfo("Info", "No changes made")
            self.destroy()
            return
        
        try:
            # Find the agent ID
            agents = self.db.get_agents()
            new_agent_id = next((agent['id'] for agent in agents if agent['name'] == new_agent), None)
            
            if not new_agent_id:
                messagebox.showerror("Error", "Selected agent not found")
                return
            
            # Update the policy assignment
            self.db.update_policy_agent(self.building_info['policy_id'], new_agent_id)
            
            # Update notes if provided
            if notes:
                # This would require adding a method to update building notes
                pass
            
            self.result = {
                'success': True,
                'new_agent': new_agent,
                'notes': notes
            }
            
            messagebox.showinfo("Success", f"Policy reassigned to {new_agent}")
            self.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update assignment: {str(e)}")
    
    def _on_cancel(self):
        """Handle cancel button click"""
        self.destroy()

class AddItemDialog(ttk.Toplevel):
    def __init__(self, parent, db_connection, **kwargs):
        """
        Dialog for adding new agents, buildings, or policies
        
        Args:
            parent: Parent widget
            db_connection: Database connection object
        """
        super().__init__(parent, **kwargs)
        self.db = db_connection
        self.result = None
        
        self.title("Add New Item")
        self.geometry("600x500")
        self.resizable(False, False)
        
        # Make dialog modal
        self.transient(parent)
        self.grab_set()
        
        self._create_widgets()
        self._center_window()
    
    def _create_widgets(self):
        """Create the dialog widgets"""
        # Main frame
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Add New Item", 
                               font=("Helvetica", 14, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Notebook for different item types
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=BOTH, expand=True)
        
        # Create tabs
        self._create_agent_tab()
        self._create_building_tab()
        self._create_policy_tab()
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=X, pady=(20, 0))
        
        ttk.Button(button_frame, text="Cancel", style="secondary.TButton",
                  command=self._on_cancel).pack(side=RIGHT, padx=(10, 0))
        ttk.Button(button_frame, text="Add Item", style="success.TButton",
                  command=self._on_add).pack(side=RIGHT)
    
    def _create_agent_tab(self):
        """Create the agent tab"""
        agent_frame = ttk.Frame(self.notebook, padding=20)
        self.notebook.add(agent_frame, text="Agent")
        
        # Agent form
        ttk.Label(agent_frame, text="Agent Information", font=("Helvetica", 12, "bold")).pack(anchor=W, pady=(0, 15))
        
        # Name
        ttk.Label(agent_frame, text="Name *:").pack(anchor=W, pady=(0, 5))
        self.agent_name_var = tk.StringVar()
        ttk.Entry(agent_frame, textvariable=self.agent_name_var, width=50).pack(fill=X, pady=(0, 10))
        
        # Email
        ttk.Label(agent_frame, text="Email:").pack(anchor=W, pady=(0, 5))
        self.agent_email_var = tk.StringVar()
        ttk.Entry(agent_frame, textvariable=self.agent_email_var, width=50).pack(fill=X, pady=(0, 10))
        
        # Phone
        ttk.Label(agent_frame, text="Phone:").pack(anchor=W, pady=(0, 5))
        self.agent_phone_var = tk.StringVar()
        ttk.Entry(agent_frame, textvariable=self.agent_phone_var, width=50).pack(fill=X, pady=(0, 10))
        
        # Notes
        ttk.Label(agent_frame, text="Notes:").pack(anchor=W, pady=(0, 5))
        self.agent_notes_text = tk.Text(agent_frame, height=3, width=50)
        self.agent_notes_text.pack(fill=X)
    
    def _create_building_tab(self):
        """Create the building tab"""
        building_frame = ttk.Frame(self.notebook, padding=20)
        self.notebook.add(building_frame, text="Building")
        
        # Building form
        ttk.Label(building_frame, text="Building Information", font=("Helvetica", 12, "bold")).pack(anchor=W, pady=(0, 15))
        
        # Code
        ttk.Label(building_frame, text="Code *:").pack(anchor=W, pady=(0, 5))
        self.building_code_var = tk.StringVar()
        ttk.Entry(building_frame, textvariable=self.building_code_var, width=50).pack(fill=X, pady=(0, 10))
        
        # Name
        ttk.Label(building_frame, text="Name *:").pack(anchor=W, pady=(0, 5))
        self.building_name_var = tk.StringVar()
        ttk.Entry(building_frame, textvariable=self.building_name_var, width=50).pack(fill=X, pady=(0, 10))
        
        # Address
        ttk.Label(building_frame, text="Address:").pack(anchor=W, pady=(0, 5))
        self.building_address_var = tk.StringVar()
        ttk.Entry(building_frame, textvariable=self.building_address_var, width=50).pack(fill=X, pady=(0, 10))
        
        # Notes
        ttk.Label(building_frame, text="Notes:").pack(anchor=W, pady=(0, 5))
        self.building_notes_text = tk.Text(building_frame, height=3, width=50)
        self.building_notes_text.pack(fill=X)
    
    def _create_policy_tab(self):
        """Create the policy tab"""
        policy_frame = ttk.Frame(self.notebook, padding=20)
        self.notebook.add(policy_frame, text="Policy")
        
        # Policy form
        ttk.Label(policy_frame, text="Policy Information", font=("Helvetica", 12, "bold")).pack(anchor=W, pady=(0, 15))
        
        # Building selection
        ttk.Label(policy_frame, text="Building *:").pack(anchor=W, pady=(0, 5))
        buildings = self.db.get_buildings()
        building_names = [f"{b['code']} - {b['name']}" for b in buildings]
        self.building_var = tk.StringVar()
        self.building_combo = ttk.Combobox(policy_frame, textvariable=self.building_var, 
                                         values=building_names, state="readonly", width=50)
        self.building_combo.pack(fill=X, pady=(0, 10))
        
        # Agent selection
        ttk.Label(policy_frame, text="Agent *:").pack(anchor=W, pady=(0, 5))
        agents = self.db.get_agents()
        agent_names = [agent['name'] for agent in agents]
        self.policy_agent_var = tk.StringVar()
        self.policy_agent_combo = ttk.Combobox(policy_frame, textvariable=self.policy_agent_var, 
                                             values=agent_names, state="readonly", width=50)
        self.policy_agent_combo.pack(fill=X, pady=(0, 10))
        
        # Carrier
        ttk.Label(policy_frame, text="Carrier *:").pack(anchor=W, pady=(0, 5))
        self.carrier_var = tk.StringVar()
        ttk.Entry(policy_frame, textvariable=self.carrier_var, width=50).pack(fill=X, pady=(0, 10))
        
        # Policy number
        ttk.Label(policy_frame, text="Policy Number *:").pack(anchor=W, pady=(0, 5))
        self.policy_number_var = tk.StringVar()
        ttk.Entry(policy_frame, textvariable=self.policy_number_var, width=50).pack(fill=X, pady=(0, 10))
        
        # Premium
        ttk.Label(policy_frame, text="Premium:").pack(anchor=W, pady=(0, 5))
        self.premium_var = tk.StringVar()
        ttk.Entry(policy_frame, textvariable=self.premium_var, width=50).pack(fill=X, pady=(0, 10))
        
        # Effective date
        ttk.Label(policy_frame, text="Effective Date (MM/DD/YYYY):").pack(anchor=W, pady=(0, 5))
        self.eff_date_var = tk.StringVar()
        ttk.Entry(policy_frame, textvariable=self.eff_date_var, width=50).pack(fill=X, pady=(0, 10))
        
        # Expiration date
        ttk.Label(policy_frame, text="Expiration Date (MM/DD/YYYY):").pack(anchor=W, pady=(0, 5))
        self.exp_date_var = tk.StringVar()
        ttk.Entry(policy_frame, textvariable=self.exp_date_var, width=50).pack(fill=X, pady=(0, 10))
        
        # Notes
        ttk.Label(policy_frame, text="Notes:").pack(anchor=W, pady=(0, 5))
        self.policy_notes_text = tk.Text(policy_frame, height=3, width=50)
        self.policy_notes_text.pack(fill=X)
    
    def _center_window(self):
        """Center the dialog on the screen"""
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
    
    def _on_add(self):
        """Handle add button click"""
        current_tab = self.notebook.select()
        tab_text = self.notebook.tab(current_tab, "text")
        
        try:
            if tab_text == "Agent":
                self._add_agent()
            elif tab_text == "Building":
                self._add_building()
            elif tab_text == "Policy":
                self._add_policy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add {tab_text.lower()}: {str(e)}")
    
    def _add_agent(self):
        """Add a new agent"""
        name = self.agent_name_var.get().strip()
        email = self.agent_email_var.get().strip()
        phone = self.agent_phone_var.get().strip()
        notes = self.agent_notes_text.get("1.0", tk.END).strip()
        
        if not name:
            messagebox.showwarning("Warning", "Agent name is required")
            return
        
        agent_id = self.db.add_agent(name, email, phone, notes)
        
        self.result = {
            'type': 'agent',
            'id': agent_id,
            'name': name
        }
        
        messagebox.showinfo("Success", f"Agent '{name}' added successfully")
        self.destroy()
    
    def _add_building(self):
        """Add a new building"""
        code = self.building_code_var.get().strip()
        name = self.building_name_var.get().strip()
        address = self.building_address_var.get().strip()
        notes = self.building_notes_text.get("1.0", tk.END).strip()
        
        if not code or not name:
            messagebox.showwarning("Warning", "Building code and name are required")
            return
        
        building_id = self.db.add_building(code, name, address, notes)
        
        self.result = {
            'type': 'building',
            'id': building_id,
            'code': code,
            'name': name
        }
        
        messagebox.showinfo("Success", f"Building '{code}' added successfully")
        self.destroy()
    
    def _add_policy(self):
        """Add a new policy"""
        building_text = self.building_var.get()
        agent_name = self.policy_agent_var.get()
        carrier = self.carrier_var.get().strip()
        policy_number = self.policy_number_var.get().strip()
        premium = self.premium_var.get().strip()
        eff_date = self.eff_date_var.get().strip()
        exp_date = self.exp_date_var.get().strip()
        notes = self.policy_notes_text.get("1.0", tk.END).strip()
        
        if not all([building_text, agent_name, carrier, policy_number]):
            messagebox.showwarning("Warning", "Building, agent, carrier, and policy number are required")
            return
        
        # Parse building selection
        building_code = building_text.split(" - ")[0]
        buildings = self.db.get_buildings()
        building = next((b for b in buildings if b['code'] == building_code), None)
        
        if not building:
            messagebox.showerror("Error", "Selected building not found")
            return
        
        # Parse agent selection
        agents = self.db.get_agents()
        agent = next((a for a in agents if a['name'] == agent_name), None)
        
        if not agent:
            messagebox.showerror("Error", "Selected agent not found")
            return
        
        # Parse premium
        premium_value = None
        if premium:
            try:
                premium_value = float(premium)
            except ValueError:
                messagebox.showerror("Error", "Premium must be a valid number")
                return
        
        # Parse dates
        try:
            if eff_date:
                datetime.strptime(eff_date, '%m/%d/%Y')
            if exp_date:
                datetime.strptime(exp_date, '%m/%d/%Y')
        except ValueError:
            messagebox.showerror("Error", "Dates must be in MM/DD/YYYY format")
            return
        
        # Add policy
        policy_id = self.db.add_policy(
            building['id'], agent['id'], carrier, policy_number,
            "{}", premium_value, eff_date, exp_date, None, notes
        )
        
        self.result = {
            'type': 'policy',
            'id': policy_id,
            'policy_number': policy_number,
            'building_code': building_code
        }
        
        messagebox.showinfo("Success", f"Policy '{policy_number}' added successfully")
        self.destroy()
    
    def _on_cancel(self):
        """Handle cancel button click"""
        self.destroy()

class PDFUploadDialog(ttk.Toplevel):
    def __init__(self, parent, db_connection, pdf_parser, rag_system, **kwargs):
        """
        Dialog for uploading and parsing PDF policies
        
        Args:
            parent: Parent widget
            db_connection: Database connection object
            pdf_parser: PDF parser instance
            rag_system: RAG system instance
        """
        super().__init__(parent, **kwargs)
        self.db = db_connection
        self.pdf_parser = pdf_parser
        self.rag_system = rag_system
        self.result = None
        
        self.title("Upload Policy PDF")
        self.geometry("700x600")
        self.resizable(False, False)
        
        # Make dialog modal
        self.transient(parent)
        self.grab_set()
        
        self._create_widgets()
        self._center_window()
    
    def _create_widgets(self):
        """Create the dialog widgets"""
        # Main frame
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Upload Policy PDF", 
                               font=("Helvetica", 14, "bold"))
        title_label.pack(pady=(0, 20))
        
        # File selection
        file_frame = ttk.LabelFrame(main_frame, text="Select PDF File", padding=15)
        file_frame.pack(fill=X, pady=(0, 20))
        
        self.file_path_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.file_path_var, width=60).pack(side=LEFT, fill=X, expand=True, padx=(0, 10))
        ttk.Button(file_frame, text="Browse", command=self._browse_file).pack(side=RIGHT)
        
        # Policy assignment
        assignment_frame = ttk.LabelFrame(main_frame, text="Policy Assignment", padding=15)
        assignment_frame.pack(fill=X, pady=(0, 20))
        
        # Building selection
        ttk.Label(assignment_frame, text="Building:").pack(anchor=W, pady=(0, 5))
        buildings = self.db.get_buildings()
        building_names = [f"{b['code']} - {b['name']}" for b in buildings]
        self.building_var = tk.StringVar()
        self.building_combo = ttk.Combobox(assignment_frame, textvariable=self.building_var, 
                                         values=building_names, state="readonly", width=60)
        self.building_combo.pack(fill=X, pady=(0, 10))
        
        # Agent selection
        ttk.Label(assignment_frame, text="Agent:").pack(anchor=W, pady=(0, 5))
        agents = self.db.get_agents()
        agent_names = [agent['name'] for agent in agents]
        self.agent_var = tk.StringVar()
        self.agent_combo = ttk.Combobox(assignment_frame, textvariable=self.agent_var, 
                                       values=agent_names, state="readonly", width=60)
        self.agent_combo.pack(fill=X, pady=(0, 10))
        
        # Upload button
        ttk.Button(assignment_frame, text="Upload and Parse PDF", 
                  style="success.TButton", command=self._upload_pdf).pack(pady=(10, 0))
        
        # Results display
        results_frame = ttk.LabelFrame(main_frame, text="Parsing Results", padding=15)
        results_frame.pack(fill=BOTH, expand=True, pady=(0, 20))
        
        # Text widget for results
        self.results_text = tk.Text(results_frame, height=15, width=80)
        self.results_text.pack(fill=BOTH, expand=True)
        
        # Scrollbar for results
        results_scrollbar = ttk.Scrollbar(results_frame, orient=VERTICAL, command=self.results_text.yview)
        results_scrollbar.pack(side=RIGHT, fill=Y)
        self.results_text.configure(yscrollcommand=results_scrollbar.set)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=X)
        
        ttk.Button(button_frame, text="Close", style="secondary.TButton",
                  command=self._on_close).pack(side=RIGHT)
    
    def _center_window(self):
        """Center the dialog on the screen"""
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
    
    def _browse_file(self):
        """Browse for PDF file"""
        file_path = filedialog.askopenfilename(
            title="Select Policy PDF",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        
        if file_path:
            self.file_path_var.set(file_path)
    
    def _upload_pdf(self):
        """Upload and parse the PDF"""
        file_path = self.file_path_var.get().strip()
        building_text = self.building_var.get()
        agent_name = self.agent_var.get()
        
        if not all([file_path, building_text, agent_name]):
            messagebox.showwarning("Warning", "Please select a file, building, and agent")
            return
        
        if not os.path.exists(file_path):
            messagebox.showerror("Error", "Selected file does not exist")
            return
        
        try:
            # Parse the PDF
            self.results_text.delete("1.0", tk.END)
            self.results_text.insert(tk.END, "Parsing PDF...\n\n")
            self.update()
            
            parsed_data = self.pdf_parser.parse_policy_pdf(file_path)
            
            # Display results
            self.results_text.delete("1.0", tk.END)
            self.results_text.insert(tk.END, "PDF Parsing Results:\n")
            self.results_text.insert(tk.END, "=" * 50 + "\n\n")
            
            for key, value in parsed_data.items():
                if key not in ['raw_text', 'file_path', 'file_size', 'extraction_timestamp']:
                    if isinstance(value, dict):
                        self.results_text.insert(tk.END, f"{key}:\n")
                        for sub_key, sub_value in value.items():
                            self.results_text.insert(tk.END, f"  {sub_key}: {sub_value}\n")
                    else:
                        self.results_text.insert(tk.END, f"{key}: {value}\n")
            
            # Validate extraction
            validation = self.pdf_parser.validate_extraction(parsed_data)
            self.results_text.insert(tk.END, f"\nValidation:\n")
            self.results_text.insert(tk.END, f"Valid: {validation['is_valid']}\n")
            self.results_text.insert(tk.END, f"Confidence: {validation['confidence_score']:.2f}\n")
            
            if validation['missing_fields']:
                self.results_text.insert(tk.END, f"Missing fields: {', '.join(validation['missing_fields'])}\n")
            
            if validation['warnings']:
                self.results_text.insert(tk.END, f"Warnings: {', '.join(validation['warnings'])}\n")
            
            # Ask if user wants to save
            if validation['is_valid']:
                self.results_text.insert(tk.END, "\n" + "=" * 50 + "\n")
                self.results_text.insert(tk.END, "Parsing successful! Would you like to save this policy?\n")
                
                # Enable save functionality
                self.parsed_data = parsed_data
                self.building_text = building_text
                self.agent_name = agent_name
                
            else:
                self.results_text.insert(tk.END, "\nParsing failed validation. Please review the PDF and try again.\n")
                
        except Exception as e:
            self.results_text.delete("1.0", tk.END)
            self.results_text.insert(tk.END, f"Error parsing PDF: {str(e)}")
    
    def _on_close(self):
        """Handle close button click"""
        self.destroy()
