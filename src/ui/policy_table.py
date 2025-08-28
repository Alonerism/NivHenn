import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from typing import Dict, List, Any, Callable
from datetime import datetime

class PolicyTableWidget(ttk.Frame):
    def __init__(self, parent, db_connection, **kwargs):
        """
        Policy table widget showing agents as headers and buildings as cells
        
        Args:
            parent: Parent widget
            db_connection: Database connection object
        """
        super().__init__(parent, **kwargs)
        self.db = db_connection
        self.agent_buildings = {}
        self.selected_cell = None
        self.on_edit_callback = None
        self.on_add_callback = None
        
        self._create_widgets()
        self._load_data()
    
    def _create_widgets(self):
        """Create the table widgets"""
        # Main container
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(main_frame, text="Insurance Policy Management", 
                               font=("Helvetica", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Control buttons frame (top-right)
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=X, pady=(0, 10))
        
        # Add button
        self.add_button = ttk.Button(button_frame, text="➕ Add New", 
                                   style="success.TButton",
                                   command=self._on_add_clicked)
        self.add_button.pack(side=RIGHT, padx=(10, 0))
        
        # Edit button
        self.edit_button = ttk.Button(button_frame, text="✏️ Edit Assignment", 
                                    style="warning.TButton",
                                    command=self._on_edit_clicked)
        self.edit_button.pack(side=RIGHT, padx=(10, 0))
        
        # Status label
        self.status_label = ttk.Label(button_frame, text="", 
                                    font=("Helvetica", 10))
        self.status_label.pack(side=LEFT)
        
        # Table container with scrollbars
        table_container = ttk.Frame(main_frame)
        table_container.pack(fill=BOTH, expand=True)
        
        # Create canvas and scrollbars
        self.canvas = tk.Canvas(table_container, bg='#2b2b2b')
        self.v_scrollbar = ttk.Scrollbar(table_container, orient=VERTICAL, command=self.canvas.yview)
        self.h_scrollbar = ttk.Scrollbar(table_container, orient=HORIZONTAL, command=self.canvas.xview)
        
        self.canvas.configure(yscrollcommand=self.v_scrollbar.set, xscrollcommand=self.h_scrollbar.set)
        
        # Pack scrollbars and canvas
        self.v_scrollbar.pack(side=RIGHT, fill=Y)
        self.h_scrollbar.pack(side=BOTTOM, fill=X)
        self.canvas.pack(side=LEFT, fill=BOTH, expand=True)
        
        # Create table frame inside canvas
        self.table_frame = ttk.Frame(self.canvas, style="dark.TFrame")
        self.canvas.create_window((0, 0), window=self.table_frame, anchor=NW)
        
        # Bind events
        self.table_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        
        # Style configuration for dark theme
        self._configure_styles()
    
    def _configure_styles(self):
        """Configure custom styles for the table"""
        style = ttk.Style()
        
        # Configure table styles
        style.configure("TableHeader.TLabel", 
                       background="#404040", 
                       foreground="white", 
                       font=("Helvetica", 11, "bold"),
                       padding=10,
                       relief="raised")
        
        style.configure("TableCell.TFrame", 
                       background="#3c3c3c", 
                       relief="sunken",
                       borderwidth=1)
        
        style.configure("TableCellSelected.TFrame", 
                       background="#505050", 
                       relief="raised",
                       borderwidth=2)
        
        style.configure("BuildingCode.TLabel", 
                       background="#3c3c3c", 
                       foreground="white", 
                       font=("Helvetica", 10, "bold"),
                       padding=5)
        
        style.configure("BuildingNotes.TLabel", 
                       background="#3c3c3c", 
                       foreground="#cccccc", 
                       font=("Helvetica", 9),
                       padding=5)
    
    def _load_data(self):
        """Load and display the agent-building matrix"""
        try:
            self.agent_buildings = self.db.get_agent_building_matrix()
            self._create_table()
            self._update_status()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load data: {str(e)}")
    
    def _create_table(self):
        """Create the table structure"""
        # Clear existing widgets
        for widget in self.table_frame.winfo_children():
            widget.destroy()
        
        if not self.agent_buildings:
            no_data_label = ttk.Label(self.table_frame, text="No data available", 
                                    font=("Helvetica", 12))
            no_data_label.pack(pady=50)
            return
        
        # Get all agents and find the maximum number of buildings
        agents = list(self.agent_buildings.keys())
        max_buildings = max(len(buildings) for buildings in self.agent_buildings.values())
        
        # Create header row
        header_frame = ttk.Frame(self.table_frame)
        header_frame.pack(fill=X)
        
        # Empty cell for row headers
        ttk.Label(header_frame, text="", style="TableHeader.TLabel", 
                width=15).pack(side=LEFT, fill=Y)
        
        # Agent headers
        for agent in agents:
            agent_header = ttk.Label(header_frame, text=agent, style="TableHeader.TLabel", 
                                   width=20)
            agent_header.pack(side=LEFT, fill=Y)
        
        # Create building rows
        for building_index in range(max_buildings):
            row_frame = ttk.Frame(self.table_frame)
            row_frame.pack(fill=X)
            
            # Row header (building number)
            row_header = ttk.Label(row_frame, text=f"Building {building_index + 1}", 
                                 style="TableHeader.TLabel", width=15)
            row_header.pack(side=LEFT, fill=Y)
            
            # Building cells for each agent
            for agent in agents:
                buildings = self.agent_buildings[agent]
                
                if building_index < len(buildings):
                    building = buildings[building_index]
                    cell_frame = self._create_building_cell(row_frame, building, agent, building_index)
                else:
                    # Empty cell
                    cell_frame = ttk.Frame(row_frame, style="TableCell.TFrame", width=200, height=80)
                    cell_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=1, pady=1)
                    cell_frame.pack_propagate(False)
                
                cell_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=1, pady=1)
    
    def _create_building_cell(self, parent, building: Dict[str, Any], agent: str, row_index: int):
        """Create a building cell widget"""
        cell_frame = ttk.Frame(parent, style="TableCell.TFrame", width=200, height=80)
        cell_frame.pack_propagate(False)
        
        # Building code (main identifier)
        code_label = ttk.Label(cell_frame, text=building['building_code'], 
                             style="BuildingCode.TLabel")
        code_label.pack(fill=X, padx=5, pady=(5, 2))
        
        # Building name (truncated if too long)
        building_name = building['building_name']
        if len(building_name) > 25:
            building_name = building_name[:22] + "..."
        
        name_label = ttk.Label(cell_frame, text=building_name, 
                             style="BuildingNotes.TLabel")
        name_label.pack(fill=X, padx=5, pady=2)
        
        # Notes (if available)
        if building.get('notes'):
            notes = building['notes']
            if len(notes) > 30:
                notes = notes[:27] + "..."
            
            notes_label = ttk.Label(cell_frame, text=notes, 
                                  style="BuildingNotes.TLabel")
            notes_label.pack(fill=X, padx=5, pady=2)
        
        # Expiration date info
        if building.get('exp_date'):
            try:
                exp_date = building['exp_date']
                if isinstance(exp_date, str):
                    exp_date = datetime.strptime(exp_date, '%Y-%m-%d').date()
                
                days_until_expiry = (exp_date - datetime.now().date()).days
                
                if days_until_expiry <= 30:
                    exp_style = "danger.TLabel"
                elif days_until_expiry <= 60:
                    exp_style = "warning.TLabel"
                else:
                    exp_style = "BuildingNotes.TLabel"
                
                exp_label = ttk.Label(cell_frame, 
                                    text=f"Expires: {exp_date.strftime('%m/%d/%Y')} ({days_until_expiry} days)",
                                    style=exp_style)
                exp_label.pack(fill=X, padx=5, pady=2)
            except:
                pass
        
        # Bind click events for selection
        cell_frame.bind("<Button-1>", lambda e, cf=cell_frame, b=building: self._on_cell_click(e, cf, b))
        code_label.bind("<Button-1>", lambda e, cf=cell_frame, b=building: self._on_cell_click(e, cf, b))
        name_label.bind("<Button-1>", lambda e, cf=cell_frame, b=building: self._on_cell_click(e, cf, b))
        
        # Store building info in the cell frame
        cell_frame.building_info = building
        cell_frame.agent_name = agent
        cell_frame.row_index = row_index
        
        return cell_frame
    
    def _on_cell_click(self, event, cell_frame, building):
        """Handle cell selection"""
        # Deselect previous selection
        if self.selected_cell:
            self.selected_cell.configure(style="TableCell.TFrame")
        
        # Select new cell
        cell_frame.configure(style="TableCellSelected.TFrame")
        self.selected_cell = cell_frame
        
        # Update status
        self._update_status()
    
    def _on_frame_configure(self, event=None):
        """Update canvas scroll region when frame size changes"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def _on_canvas_configure(self, event):
        """Update canvas window when canvas size changes"""
        self.canvas.itemconfig(self.canvas.find_withtag("all")[0], width=event.width)
    
    def _update_status(self):
        """Update the status label"""
        if self.selected_cell:
            building = self.selected_cell.building_info
            agent = self.selected_cell.agent_name
            status_text = f"Selected: {building['building_code']} ({building['building_name']}) - Agent: {agent}"
        else:
            status_text = "Click on a building to select it"
        
        self.status_label.configure(text=status_text)
    
    def _on_edit_clicked(self):
        """Handle edit button click"""
        if not self.selected_cell:
            messagebox.showwarning("No Selection", "Please select a building to edit")
            return
        
        if self.on_edit_callback:
            building = self.selected_cell.building_info
            agent = self.selected_cell.agent_name
            self.on_edit_callback(building, agent)
    
    def _on_add_clicked(self):
        """Handle add button click"""
        if self.on_add_callback:
            self.on_add_callback()
    
    def set_edit_callback(self, callback: Callable):
        """Set the callback for edit operations"""
        self.on_edit_callback = callback
    
    def set_add_callback(self, callback: Callable):
        """Set the callback for add operations"""
        self.on_add_callback = callback
    
    def refresh_data(self):
        """Refresh the table data"""
        self._load_data()
    
    def get_selected_building(self):
        """Get the currently selected building info"""
        if self.selected_cell:
            return self.selected_cell.building_info, self.selected_cell.agent_name
        return None, None
