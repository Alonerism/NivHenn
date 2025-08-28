#!/usr/bin/env python3
"""
Insurance Master - Main Application

A Tkinter application for managing building insurance policies with:
- Agent-to-building table view
- PDF policy parsing
- AI-powered Q&A system
- Email alerts for expiring policies
"""

import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from db.database import InsuranceDatabase
from parsing.pdf_parser import PolicyPDFParser
from rag.rag_system import RAGSystem
from alerts.email_alerts import EmailAlertSystem
from ui.policy_table import PolicyTableWidget
from ui.dialogs import EditAssignmentDialog, AddItemDialog, PDFUploadDialog
from ui.chat_panel import ChatPanel

class InsuranceMasterApp:
    def __init__(self):
        """Initialize the Insurance Master application"""
        self.root = ttk.Window(themename="darkly")
        self.root.title("Insurance Master")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)
        
        # Initialize components
        self._initialize_components()
        
        # Create UI
        self._create_ui()
        
        # Start alert system
        self._start_alerts()
        
        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _initialize_components(self):
        """Initialize all application components"""
        try:
            # Initialize database
            print("Initializing database...")
            self.db = InsuranceDatabase()
            print("Database initialized successfully")
            
            # Initialize PDF parser
            print("Initializing PDF parser...")
            self.pdf_parser = PolicyPDFParser()
            print("PDF parser initialized successfully")
            
            # Initialize RAG system (optional)
            print("Initializing RAG system...")
            try:
                self.rag_system = RAGSystem(self.db)
                print("RAG system initialized successfully")
            except Exception as e:
                print(f"Warning: RAG system initialization failed: {e}")
                print("Q&A functionality will be limited, but other features will work")
                self.rag_system = None
            
            # Initialize email alert system
            print("Initializing email alert system...")
            try:
                self.alert_system = EmailAlertSystem(self.db)
                print("Email alert system initialized successfully")
            except Exception as e:
                print(f"Warning: Email alert system initialization failed: {e}")
                print("Email alerts will not be available, but other features will work")
                self.alert_system = None
            
        except Exception as e:
            messagebox.showerror("Initialization Error", 
                               f"Failed to initialize application components:\n{str(e)}")
            sys.exit(1)
    
    def _create_ui(self):
        """Create the main user interface"""
        # Configure grid weights
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Create main notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Create tabs
        self._create_policy_table_tab()
        self._create_chat_tab()
        self._create_upload_tab()
        self._create_alerts_tab()
        
        # Create menu bar
        self._create_menu()
    
    def _create_policy_table_tab(self):
        """Create the main policy table tab"""
        table_frame = ttk.Frame(self.notebook)
        self.notebook.add(table_frame, text="Policy Management")
        
        # Create policy table widget
        self.policy_table = PolicyTableWidget(table_frame, self.db)
        self.policy_table.pack(fill=BOTH, expand=True)
        
        # Set callbacks
        self.policy_table.set_edit_callback(self._on_edit_assignment)
        self.policy_table.set_add_callback(self._on_add_item)
    
    def _create_chat_tab(self):
        """Create the chat Q&A tab"""
        chat_frame = ttk.Frame(self.notebook)
        self.notebook.add(chat_frame, text="Policy Q&A")
        
        if self.rag_system:
            # Create chat panel
            self.chat_panel = ChatPanel(chat_frame, self.rag_system)
            self.chat_panel.pack(fill=BOTH, expand=True)
        else:
            # Show error message if RAG system is not available
            self._create_chat_error_interface(chat_frame)
    
    def _create_chat_error_interface(self, parent):
        """Create an error interface when RAG system is not available"""
        main_frame = ttk.Frame(parent, padding=20)
        main_frame.pack(fill=BOTH, expand=True)
        
        # Error icon and message
        error_label = ttk.Label(main_frame, text="⚠️", font=("Helvetica", 48))
        error_label.pack(pady=(50, 20))
        
        title_label = ttk.Label(main_frame, text="Q&A System Unavailable", 
                               font=("Helvetica", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        desc_label = ttk.Label(main_frame, 
                              text="The Policy Q&A system is currently unavailable due to configuration issues.",
                              font=("Helvetica", 12))
        desc_label.pack(pady=(0, 30))
        
        # Troubleshooting information
        troubleshooting_frame = ttk.LabelFrame(main_frame, text="Troubleshooting", padding=15)
        troubleshooting_frame.pack(fill=X, pady=(0, 20))
        
        issues = [
            "• Check that your OpenAI API key is set in the .env file",
            "• Ensure ChromaDB is properly installed: pip install chromadb",
            "• Verify all dependencies are installed: pip install -r requirements.txt",
            "• Check the console for specific error messages"
        ]
        
        for issue in issues:
            ttk.Label(troubleshooting_frame, text=issue, 
                     font=("Helvetica", 10)).pack(anchor=W, pady=2)
        
        # Refresh button
        refresh_button = ttk.Button(main_frame, text="🔄 Retry Initialization", 
                                  style="primary.TButton",
                                  command=self._retry_rag_initialization)
        refresh_button.pack(pady=(20, 0))
    
    def _retry_rag_initialization(self):
        """Retry initializing the RAG system"""
        try:
            print("Retrying RAG system initialization...")
            self.rag_system = RAGSystem(self.db)
            print("RAG system initialized successfully")
            
            # Refresh the chat tab
            self.notebook.forget(self.notebook.index("Policy Q&A"))
            self._create_chat_tab()
            
            messagebox.showinfo("Success", "Q&A system has been initialized successfully!")
            
        except Exception as e:
            messagebox.showerror("Initialization Failed", 
                               f"Failed to initialize RAG system:\n{str(e)}")
    
    def _create_upload_tab(self):
        """Create the PDF upload tab"""
        upload_frame = ttk.Frame(self.notebook)
        self.notebook.add(upload_frame, text="Upload Policies")
        
        # Create upload interface
        self._create_upload_interface(upload_frame)
    
    def _create_upload_interface(self, parent):
        """Create the PDF upload interface"""
        # Main container
        main_frame = ttk.Frame(parent, padding=20)
        main_frame.pack(fill=BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Upload Policy PDFs", 
                               font=("Helvetica", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Description
        desc_label = ttk.Label(main_frame, 
                              text="Upload PDF policy documents to automatically extract information and add them to the knowledge base.",
                              font=("Helvetica", 11))
        desc_label.pack(pady=(0, 30))
        
        # Upload button
        upload_button = ttk.Button(main_frame, text="📄 Upload New Policy PDF", 
                                 style="success.TButton", 
                                 command=self._show_upload_dialog)
        upload_button.pack(pady=(0, 20))
        
        # Instructions
        instructions_frame = ttk.LabelFrame(main_frame, text="Instructions", padding=15)
        instructions_frame.pack(fill=X, pady=(0, 20))
        
        instructions = [
            "1. Click 'Upload New Policy PDF' to select a policy document",
            "2. Choose the building and agent for the policy",
            "3. The system will automatically parse the PDF and extract key information",
            "4. Review the extracted data and save if correct",
            "5. The policy will be added to the knowledge base for Q&A"
        ]
        
        for instruction in instructions:
            ttk.Label(instructions_frame, text=instruction, 
                     font=("Helvetica", 10)).pack(anchor=W, pady=2)
        
        # Supported formats
        formats_frame = ttk.LabelFrame(main_frame, text="Supported Formats", padding=15)
        formats_frame.pack(fill=X)
        
        ttk.Label(formats_frame, text="• PDF files (.pdf)", 
                 font=("Helvetica", 10)).pack(anchor=W, pady=2)
        ttk.Label(formats_frame, text="• Text-based PDFs work best", 
                 font=("Helvetica", 10)).pack(anchor=W, pady=2)
        ttk.Label(formats_frame, text="• Scanned PDFs may have limited extraction", 
                 font=("Helvetica", 10)).pack(anchor=W, pady=2)
    
    def _create_alerts_tab(self):
        """Create the alerts management tab"""
        alerts_frame = ttk.Frame(self.notebook)
        self.notebook.add(alerts_frame, text="Alerts & Notifications")
        
        if self.alert_system:
            # Create alerts interface
            self._create_alerts_interface(alerts_frame)
        else:
            # Show error message if alert system is not available
            self._create_alerts_error_interface(alerts_frame)
    
    def _create_alerts_error_interface(self, parent):
        """Create an error interface when alert system is not available"""
        main_frame = ttk.Frame(parent, padding=20)
        main_frame.pack(fill=BOTH, expand=True)
        
        # Error icon and message
        error_label = ttk.Label(main_frame, text="⚠️", font=("Helvetica", 48))
        error_label.pack(pady=(50, 20))
        
        title_label = ttk.Label(main_frame, text="Alert System Unavailable", 
                               font=("Helvetica", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        desc_label = ttk.Label(main_frame, 
                              text="The email alert system is currently unavailable due to configuration issues.",
                              font=("Helvetica", 12))
        desc_label.pack(pady=(0, 30))
        
        # Troubleshooting information
        troubleshooting_frame = ttk.LabelFrame(main_frame, text="Troubleshooting", padding=15)
        troubleshooting_frame.pack(fill=X, pady=(0, 20))
        
        issues = [
            "• Check that your email settings are configured in the .env file",
            "• Ensure all required email variables are set (EMAIL_USER, EMAIL_PASSWORD, etc.)",
            "• For Gmail, use an App Password, not your regular password",
            "• Verify SMTP settings and port numbers are correct"
        ]
        
        for issue in issues:
            ttk.Label(troubleshooting_frame, text=issue, 
                     font=("Helvetica", 10)).pack(anchor=W, pady=2)
        
        # Refresh button
        refresh_button = ttk.Button(main_frame, text="🔄 Retry Initialization", 
                                  style="primary.TButton",
                                  command=self._retry_alerts_initialization)
        refresh_button.pack(pady=(20, 0))
    
    def _retry_alerts_initialization(self):
        """Retry initializing the alert system"""
        try:
            print("Retrying alert system initialization...")
            self.alert_system = EmailAlertSystem(self.db)
            print("Alert system initialized successfully")
            
            # Refresh the alerts tab
            self.notebook.forget(self.notebook.index("Alerts & Notifications"))
            self._create_alerts_tab()
            
            messagebox.showinfo("Success", "Alert system has been initialized successfully!")
            
        except Exception as e:
            messagebox.showerror("Initialization Failed", 
                               f"Failed to initialize alert system:\n{str(e)}")
    
    def _create_alerts_interface(self, parent):
        """Create the alerts management interface"""
        # Main container
        main_frame = ttk.Frame(parent, padding=20)
        main_frame.pack(fill=BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Email Alerts & Notifications", 
                               font=("Helvetica", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Status frame
        status_frame = ttk.LabelFrame(main_frame, text="Alert System Status", padding=15)
        status_frame.pack(fill=X, pady=(0, 20))
        
        # Get current status
        try:
            status = self.alert_system.get_alert_status()
            
            # Email configuration status
            config_status = "✅ Configured" if status['email_configured'] else "❌ Not Configured"
            ttk.Label(status_frame, text=f"Email Configuration: {config_status}").pack(anchor=W, pady=2)
            
            if status['email_configured']:
                ttk.Label(status_frame, text=f"SMTP Server: {status['smtp_host']}:{status['smtp_port']}").pack(anchor=W, pady=2)
                ttk.Label(status_frame, text=f"Email User: {status['email_user']}").pack(anchor=W, pady=2)
                ttk.Label(status_frame, text=f"Alert Recipients: {', '.join(status['alert_recipients'])}").pack(anchor=W, pady=2)
                ttk.Label(status_frame, text=f"Alert Thresholds: {', '.join(map(str, status['alert_thresholds']))} days").pack(anchor=W, pady=2)
            
            # Expiring policies
            if 'total_expiring_soon' in status:
                ttk.Label(status_frame, text=f"Policies Expiring Soon: {status['total_expiring_soon']}").pack(anchor=W, pady=2)
                ttk.Label(status_frame, text=f"  - 60 days: {status.get('policies_expiring_60_days', 0)}").pack(anchor=W, pady=2)
                ttk.Label(status_frame, text=f"  - 30 days: {status.get('policies_expiring_30_days', 0)}").pack(anchor=W, pady=2)
            
        except Exception as e:
            ttk.Label(status_frame, text=f"Error getting status: {str(e)}", 
                     foreground="red").pack(anchor=W, pady=2)
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=X, pady=(20, 0))
        
        # Test email button
        test_button = ttk.Button(button_frame, text="📧 Send Test Email", 
                               style="info.TButton",
                               command=self._send_test_email)
        test_button.pack(side=LEFT, padx=(0, 10))
        
        # Manual check button
        check_button = ttk.Button(button_frame, text="🔍 Check Expiring Policies", 
                                style="warning.TButton",
                                command=self._manual_check_alerts)
        check_button.pack(side=LEFT, padx=(0, 10))
        
        # Configuration info
        config_frame = ttk.LabelFrame(main_frame, text="Configuration", padding=15)
        config_frame.pack(fill=X, pady=(20, 0))
        
        config_text = """
To configure email alerts, create a .env file in the application directory with:

EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
ALERT_EMAIL_1=recipient1@example.com
ALERT_EMAIL_2=recipient2@example.com

Note: For Gmail, you'll need to use an App Password, not your regular password.
        """
        
        config_label = ttk.Label(config_frame, text=config_text, 
                               font=("Courier", 9), justify=tk.LEFT)
        config_label.pack(anchor=W)
    
    def _create_menu(self):
        """Create the application menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Refresh Data", command=self._refresh_data)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_closing)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Upload PDF", command=self._show_upload_dialog)
        tools_menu.add_command(label="Add New Item", command=self._on_add_item)
        tools_menu.add_separator()
        
        # Add alert-related menu items only if alert system is available
        if self.alert_system:
            tools_menu.add_command(label="Check Alerts", command=self._manual_check_alerts)
            tools_menu.add_command(label="Send Test Email", command=self._send_test_email)
        else:
            tools_menu.add_command(label="Check Alerts", command=self._show_alerts_unavailable, state=tk.DISABLED)
            tools_menu.add_command(label="Send Test Email", command=self._show_alerts_unavailable, state=tk.DISABLED)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)
    
    def _on_edit_assignment(self, building_info, current_agent):
        """Handle edit assignment request"""
        dialog = EditAssignmentDialog(self.root, building_info, current_agent, self.db)
        self.root.wait_window(dialog)
        
        if dialog.result and dialog.result.get('success'):
            # Refresh the table
            self.policy_table.refresh_data()
    
    def _on_add_item(self):
        """Handle add item request"""
        dialog = AddItemDialog(self.root, self.db)
        self.root.wait_window(dialog)
        
        if dialog.result:
            # Refresh the table
            self.policy_table.refresh_data()
    
    def _show_upload_dialog(self):
        """Show the PDF upload dialog"""
        dialog = PDFUploadDialog(self.root, self.db, self.pdf_parser, self.rag_system)
        self.root.wait_window(dialog)
    
    def _refresh_data(self):
        """Refresh all data displays"""
        try:
            self.policy_table.refresh_data()
            messagebox.showinfo("Success", "Data refreshed successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh data: {str(e)}")
    
    def _manual_check_alerts(self):
        """Manually trigger alert check"""
        if not self.alert_system:
            messagebox.showwarning("Alerts Unavailable", "The alert system is not currently available.")
            return
        
        try:
            self.alert_system.manual_check_expiring_policies()
            messagebox.showinfo("Success", "Alert check completed")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to check alerts: {str(e)}")
    
    def _send_test_email(self):
        """Send a test email"""
        if not self.alert_system:
            messagebox.showwarning("Alerts Unavailable", "The alert system is not currently available.")
            return
        
        try:
            if self.alert_system.send_test_email():
                messagebox.showinfo("Success", "Test email sent successfully")
            else:
                messagebox.showwarning("Warning", "Test email not sent - check configuration")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send test email: {str(e)}")
    
    def _show_about(self):
        """Show about dialog"""
        about_text = """
Insurance Master v1.0

A comprehensive insurance policy management system with:
• Agent-to-building policy management
• PDF policy parsing and extraction
• AI-powered Q&A system
• Automated email alerts

Built with Python, Tkinter, and OpenAI
        """
        
        messagebox.showinfo("About Insurance Master", about_text.strip())
    
    def _start_alerts(self):
        """Start the email alert system"""
        try:
            # The alert system starts automatically in its constructor
            print("Email alert system started")
        except Exception as e:
            print(f"Warning: Failed to start alert system: {e}")
    
    def _on_closing(self):
        """Handle application closing"""
        if messagebox.askokcancel("Quit", "Are you sure you want to quit?"):
            print("Shutting down Insurance Master...")
            self.root.destroy()
    
    def run(self):
        """Run the application"""
        try:
            print("Starting Insurance Master...")
            self.root.mainloop()
        except KeyboardInterrupt:
            print("\nApplication interrupted by user")
        except Exception as e:
            print(f"Application error: {e}")
            messagebox.showerror("Fatal Error", f"Application encountered a fatal error:\n{str(e)}")
        finally:
            print("Insurance Master shutdown complete")

def main():
    """Main entry point"""
    try:
        # Check if .env file exists
        env_file = Path(".env")
        if not env_file.exists():
            print("Warning: .env file not found. Some features may not work properly.")
            print("Please copy env.example to .env and configure your settings.")
        
        # Create and run application
        app = InsuranceMasterApp()
        app.run()
        
    except Exception as e:
        print(f"Failed to start application: {e}")
        messagebox.showerror("Startup Error", f"Failed to start Insurance Master:\n{str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
