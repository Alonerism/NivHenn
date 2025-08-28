import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from typing import Dict, List, Any, Callable
import threading
import time

class ChatPanel(ttk.Frame):
    def __init__(self, parent, rag_system, **kwargs):
        """
        Chat panel for RAG Q&A system
        
        Args:
            parent: Parent widget
            rag_system: RAG system instance
        """
        super().__init__(parent, **kwargs)
        self.rag_system = rag_system
        self.chat_history = []
        self.is_processing = False
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create the chat panel widgets"""
        # Main container
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(main_frame, text="Policy Q&A Assistant", 
                               font=("Helvetica", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Chat display area
        chat_frame = ttk.LabelFrame(main_frame, text="Chat History", padding=10)
        chat_frame.pack(fill=BOTH, expand=True, pady=(0, 20))
        
        # Chat text widget with scrollbar
        self.chat_text = scrolledtext.ScrolledText(chat_frame, height=20, width=80, 
                                                 wrap=tk.WORD, state=tk.DISABLED)
        self.chat_text.pack(fill=BOTH, expand=True)
        
        # Input area
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=X, pady=(0, 10))
        
        # Question input
        ttk.Label(input_frame, text="Ask a question about policies:").pack(anchor=W, pady=(0, 5))
        
        input_container = ttk.Frame(input_frame)
        input_container.pack(fill=X)
        
        self.question_var = tk.StringVar()
        self.question_entry = ttk.Entry(input_container, textvariable=self.question_var, 
                                      font=("Helvetica", 11))
        self.question_entry.pack(side=LEFT, fill=X, expand=True, padx=(0, 10))
        
        # Send button
        self.send_button = ttk.Button(input_container, text="Send", 
                                    style="primary.TButton", command=self._send_question)
        self.send_button.pack(side=RIGHT)
        
        # Bind Enter key to send
        self.question_entry.bind("<Return>", lambda e: self._send_question())
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=X)
        
        # Clear chat button
        ttk.Button(button_frame, text="Clear Chat", style="secondary.TButton",
                  command=self._clear_chat).pack(side=LEFT)
        
        # Sample questions button
        ttk.Button(button_frame, text="Sample Questions", style="info.TButton",
                  command=self._show_sample_questions).pack(side=LEFT, padx=(10, 0))
        
        # Knowledge base stats button
        ttk.Button(button_frame, text="KB Stats", style="info.TButton",
                  command=self._show_kb_stats).pack(side=LEFT, padx=(10, 0))
        
        # Status label
        self.status_label = ttk.Label(button_frame, text="Ready", 
                                    font=("Helvetica", 10))
        self.status_label.pack(side=RIGHT)
        
        # Add welcome message
        self._add_system_message("Welcome to the Policy Q&A Assistant! Ask me anything about your insurance policies.")
        self._add_system_message("I can help you understand coverage, compare policies, find specific information, and more.")
    
    def _send_question(self):
        """Send the current question to the RAG system"""
        question = self.question_var.get().strip()
        
        if not question:
            messagebox.showwarning("Warning", "Please enter a question")
            return
        
        if self.is_processing:
            messagebox.showinfo("Info", "Please wait for the current question to be processed")
            return
        
        # Add user question to chat
        self._add_user_message(question)
        
        # Clear input
        self.question_var.set("")
        
        # Process question in background
        self.is_processing = True
        self.send_button.configure(state=tk.DISABLED)
        self.status_label.configure(text="Processing...")
        
        # Start processing thread
        thread = threading.Thread(target=self._process_question, args=(question,))
        thread.daemon = True
        thread.start()
    
    def _process_question(self, question: str):
        """Process the question using the RAG system"""
        try:
            # Get answer from RAG system
            response = self.rag_system.query_policies(question)
            
            # Update UI in main thread
            self.after(0, self._display_response, response)
            
        except Exception as e:
            error_msg = f"Error processing question: {str(e)}"
            self.after(0, self._display_error, error_msg)
        
        finally:
            # Reset UI state
            self.after(0, self._reset_ui_state)
    
    def _display_response(self, response: Dict[str, Any]):
        """Display the RAG response"""
        answer = response.get('answer', 'No answer generated')
        sources = response.get('sources', [])
        confidence = response.get('confidence', 0.0)
        
        # Add assistant response
        self._add_assistant_message(answer)
        
        # Add source information if available
        if sources:
            source_text = "\n\nSources:\n"
            for i, source in enumerate(sources, 1):
                source_text += f"{i}. Policy: {source['policy_number']}, Building: {source['building_code']}\n"
                source_text += f"   Relevance: {source['relevance_score']:.2f}\n"
                if source.get('text_preview'):
                    source_text += f"   Preview: {source['text_preview']}\n"
                source_text += "\n"
            
            self._add_system_message(source_text)
        
        # Add confidence score
        if confidence > 0:
            confidence_text = f"Confidence: {confidence:.2f}"
            if confidence < 0.5:
                confidence_text += " (Low confidence - consider reviewing sources)"
            self._add_system_message(confidence_text)
    
    def _display_error(self, error_msg: str):
        """Display an error message"""
        self._add_system_message(f"❌ {error_msg}")
    
    def _reset_ui_state(self):
        """Reset the UI state after processing"""
        self.is_processing = False
        self.send_button.configure(state=tk.NORMAL)
        self.status_label.configure(text="Ready")
    
    def _add_user_message(self, message: str):
        """Add a user message to the chat"""
        self.chat_history.append(('user', message))
        self._update_chat_display()
    
    def _add_assistant_message(self, message: str):
        """Add an assistant message to the chat"""
        self.chat_history.append(('assistant', message))
        self._update_chat_display()
    
    def _add_system_message(self, message: str):
        """Add a system message to the chat"""
        self.chat_history.append(('system', message))
        self._update_chat_display()
    
    def _update_chat_display(self):
        """Update the chat display with all messages"""
        self.chat_text.configure(state=tk.NORMAL)
        self.chat_text.delete("1.0", tk.END)
        
        for msg_type, message in self.chat_history:
            if msg_type == 'user':
                self.chat_text.insert(tk.END, "You: ", "user")
                self.chat_text.insert(tk.END, f"{message}\n\n", "user_msg")
            elif msg_type == 'assistant':
                self.chat_text.insert(tk.END, "Assistant: ", "assistant")
                self.chat_text.insert(tk.END, f"{message}\n\n", "assistant_msg")
            else:  # system
                self.chat_text.insert(tk.END, f"{message}\n\n", "system")
        
        # Configure tags for styling
        self.chat_text.tag_configure("user", foreground="#007bff", font=("Helvetica", 10, "bold"))
        self.chat_text.tag_configure("user_msg", foreground="#000000", font=("Helvetica", 10))
        self.chat_text.tag_configure("assistant", foreground="#28a745", font=("Helvetica", 10, "bold"))
        self.chat_text.tag_configure("assistant_msg", foreground="#000000", font=("Helvetica", 10))
        self.chat_text.tag_configure("system", foreground="#6c757d", font=("Helvetica", 9, "italic"))
        
        # Scroll to bottom
        self.chat_text.see(tk.END)
        self.chat_text.configure(state=tk.DISABLED)
    
    def _clear_chat(self):
        """Clear the chat history"""
        if messagebox.askyesno("Clear Chat", "Are you sure you want to clear the chat history?"):
            self.chat_history = []
            self._add_system_message("Chat history cleared.")
    
    def _show_sample_questions(self):
        """Show sample questions to help users"""
        sample_questions = [
            "What is the coverage limit for property damage?",
            "Which policies have the highest deductibles?",
            "What endorsements are available for cyber liability?",
            "Compare the coverage between Building B001 and Building B002",
            "What policies are expiring in the next 30 days?",
            "Which buildings have umbrella coverage?",
            "What is the total premium across all policies?",
            "Find policies with business interruption coverage"
        ]
        
        sample_window = tk.Toplevel(self)
        sample_window.title("Sample Questions")
        sample_window.geometry("500x400")
        sample_window.transient(self)
        sample_window.grab_set()
        
        # Create sample questions list
        main_frame = ttk.Frame(sample_window, padding=20)
        main_frame.pack(fill=BOTH, expand=True)
        
        ttk.Label(main_frame, text="Sample Questions", 
                 font=("Helvetica", 14, "bold")).pack(pady=(0, 20))
        
        # Create listbox with sample questions
        listbox = tk.Listbox(main_frame, height=15, width=60)
        listbox.pack(fill=BOTH, expand=True, pady=(0, 20))
        
        for question in sample_questions:
            listbox.insert(tk.END, question)
        
        # Button to use selected question
        def use_question():
            selection = listbox.curselection()
            if selection:
                question = listbox.get(selection[0])
                self.question_var.set(question)
                sample_window.destroy()
                self.question_entry.focus()
        
        ttk.Button(main_frame, text="Use Selected Question", 
                  style="primary.TButton", command=use_question).pack()
        
        # Center window
        sample_window.update_idletasks()
        x = (sample_window.winfo_screenwidth() // 2) - (sample_window.winfo_width() // 2)
        y = (sample_window.winfo_screenheight() // 2) - (sample_window.winfo_height() // 2)
        sample_window.geometry(f"+{x}+{y}")
    
    def _show_kb_stats(self):
        """Show knowledge base statistics"""
        try:
            stats = self.rag_system.get_knowledge_base_stats()
            
            stats_window = tk.Toplevel(self)
            stats_window.title("Knowledge Base Statistics")
            stats_window.geometry("400x300")
            stats_window.transient(self)
            stats_window.grab_set()
            
            main_frame = ttk.Frame(stats_window, padding=20)
            main_frame.pack(fill=BOTH, expand=True)
            
            ttk.Label(main_frame, text="Knowledge Base Statistics", 
                     font=("Helvetica", 14, "bold")).pack(pady=(0, 20))
            
            # Display stats
            if 'error' not in stats:
                ttk.Label(main_frame, text=f"Total Documents: {stats['total_documents']}").pack(anchor=W, pady=5)
                ttk.Label(main_frame, text=f"Unique Policies: {stats['unique_policies']}").pack(anchor=W, pady=5)
                ttk.Label(main_frame, text=f"Collection: {stats['collection_name']}").pack(anchor=W, pady=5)
                ttk.Label(main_frame, text=f"Status: {stats['status']}").pack(anchor=W, pady=5)
                
                if 'total_expiring_soon' in stats:
                    ttk.Label(main_frame, text=f"Policies Expiring Soon: {stats['total_expiring_soon']}").pack(anchor=W, pady=5)
            else:
                ttk.Label(main_frame, text=f"Error: {stats['error']}", 
                         foreground="red").pack(anchor=W, pady=5)
            
            # Close button
            ttk.Button(main_frame, text="Close", 
                      style="secondary.TButton", 
                      command=stats_window.destroy).pack(pady=(20, 0))
            
            # Center window
            stats_window.update_idletasks()
            x = (stats_window.winfo_screenwidth() // 2) - (stats_window.winfo_width() // 2)
            y = (stats_window.winfo_screenheight() // 2) - (stats_window.winfo_height() // 2)
            stats_window.geometry(f"+{x}+{y}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to get knowledge base stats: {str(e)}")
    
    def get_chat_history(self) -> List[tuple]:
        """Get the current chat history"""
        return self.chat_history.copy()
    
    def export_chat(self, file_path: str):
        """Export chat history to a text file"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("Policy Q&A Chat History\n")
                f.write("=" * 50 + "\n\n")
                
                for msg_type, message in self.chat_history:
                    if msg_type == 'user':
                        f.write(f"You: {message}\n\n")
                    elif msg_type == 'assistant':
                        f.write(f"Assistant: {message}\n\n")
                    else:  # system
                        f.write(f"System: {message}\n\n")
            
            return True
        except Exception as e:
            print(f"Failed to export chat: {e}")
            return False
