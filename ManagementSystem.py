
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os
from datetime import datetime
from typing import List, Dict, Optional
import re

class Theme:
    PRIMARY = "#007acc"
    SECONDARY = "#34495e"
    ACCENT = "#3498db"
    SUCCESS = "#28a745"
    WARNING = "#ffc107"
    DANGER = "#dc3545"
    LIGHT = "#f5f5f5"
    DARK = "#17a2b8"
    BG = "#f8f9fa"

class Validator:
    @staticmethod
    def validate_id(id_str: str) -> bool:
        return bool(re.match(r'^[A-Z]{2}\d{4}$', id_str))

    @staticmethod
    def validate_email(email: str) -> bool:
        return bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email))

    @staticmethod
    def validate_phone(phone: str) -> bool:
        return bool(re.match(r'^\+?1?\d{9,15}$', phone))

class Record:
    def __init__(self, id: str, name: str, role: str, department: str, email: str = "", 
                 phone: str = "", hire_date: str = "", status: str = "Active"):
        self.id = id
        self.name = name
        self.role = role
        self.department = department
        self.email = email
        self.phone = phone
        self.hire_date = hire_date or datetime.now().strftime("%Y-%m-%d")
        self.status = status

    def to_dict(self) -> dict:
        return self.__dict__

    @classmethod
    def from_dict(cls, data: dict) -> 'Record':
        return cls(**data)

class Database:
    def __init__(self, filename: str):
        self.filename = filename
        self.records: List[Record] = []
        self.load_data()

    def load_data(self) -> None:
        if os.path.exists(self.filename):
            with open(self.filename, 'r') as file:
                data = json.load(file)
                self.records = [Record.from_dict(record) for record in data]

    def save_data(self) -> None:
        with open(self.filename, 'w') as file:
            json.dump([record.to_dict() for record in self.records], file, indent=4)

    def add_record(self, record: Record) -> None:
        self.records.append(record)
        self.save_data()

    def update_record(self, index: int, record: Record) -> None:
        self.records[index] = record
        self.save_data()

    def delete_record(self, index: int) -> None:
        del self.records[index]
        self.save_data()

    def search_records(self, term: str) -> List[Record]:
        term = term.lower()
        return [
            record for record in self.records
            if term in record.id.lower() or
               term in record.name.lower() or
               term in record.role.lower() or
               term in record.department.lower()
        ]

class CustomEntry(ttk.Entry):
    def __init__(self, master=None, placeholder="", **kwargs):
        super().__init__(master, **kwargs)
        self.placeholder = placeholder
        self.placeholder_color = 'grey'
        self.default_fg_color = self['foreground']
        
        self.bind("<FocusIn>", self._focus_in)
        self.bind("<FocusOut>", self._focus_out)
        
        self._focus_out(None)
    
    def _focus_in(self, _):
        if self.get() == self.placeholder:
            self.delete(0, tk.END)
            self['foreground'] = self.default_fg_color

    def _focus_out(self, _):
        if not self.get():
            self.insert(0, self.placeholder)
            self['foreground'] = self.placeholder_color

class ManagementSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Management System")
        self.root.minsize(1200, 600)
        self.root.configure(bg=Theme.BG)

        # Initialize database
        self.db = Database("records.json")
        
        self._setup_styles()
        self._create_widgets()
        self._setup_layout()
        self._setup_bindings()
        self.load_table()

    def _setup_styles(self):
        style = ttk.Style()
        style.configure("Custom.TFrame", background=Theme.BG)
        style.configure("Custom.TLabel", background=Theme.BG, foreground=Theme.DARK)
        style.configure("Title.TLabel", 
                       background=Theme.PRIMARY, 
                       foreground=Theme.LIGHT, 
                       font=("Arial", 24, "bold"))
        style.configure("Custom.TButton", 
                       background=Theme.ACCENT, 
                       foreground=Theme.LIGHT, 
                       padding=(10, 5))

    def _create_widgets(self):
        # Title Frame
        self.title_frame = ttk.Frame(self.root, style="Custom.TFrame")
        ttk.Label(
            self.title_frame, 
            text="Advanced Management System",
            style="Title.TLabel"
        ).pack(fill="x", pady=10)

        # Search Frame
        self.search_frame = ttk.Frame(self.root, style="Custom.TFrame")
        self.search_entry = CustomEntry(
            self.search_frame,
            placeholder="Search records...",
            width=40
        )
        self.search_entry.bind('<KeyRelease>', self._on_search)

        # Table Frame
        self.table_frame = ttk.Frame(self.root, style="Custom.TFrame")
        
        # Create Treeview
        self.table = ttk.Treeview(
            self.table_frame,
            columns=("ID", "Name", "Role", "Department", "Email", "Phone", "Hire Date", "Status"),
            show="headings",
            selectmode="browse"
        )
        
        # Configure columns
        columns = [
            ("ID", 70),
            ("Name", 120),
            ("Role", 120),
            ("Department", 120),
            ("Email", 150),
            ("Phone", 100),
            ("Hire Date", 80),
            ("Status", 70)
        ]
        
        for col, width in columns:
            self.table.column(col, width=width, minwidth=50)
            self.table.heading(col, text=col, command=lambda c=col: self._sort_table(c))

        # Add scrollbars
        self.y_scroll = ttk.Scrollbar(
            self.table_frame,
            orient="vertical",
            command=self.table.yview
        )
        self.x_scroll = ttk.Scrollbar(
            self.table_frame,
            orient="horizontal",
            command=self.table.xview
        )
        self.table.configure(
            yscrollcommand=self.y_scroll.set,
            xscrollcommand=self.x_scroll.set
        )

        # Buttons Frame
        self.buttons_frame = ttk.Frame(self.root, style="Custom.TFrame")
        
        # Create buttons with icons (you can add icons later)
        self.buttons = {
            "Add": ("Add Record", self.add_record, Theme.SUCCESS),
            "Update": ("Update Record", self.update_record, Theme.ACCENT),
            "Delete": ("Delete Record", self.delete_record, Theme.DANGER),
            "Export": ("Export Data", self.export_data, Theme.WARNING),
            "Refresh": ("Refresh", self.load_table, Theme.SECONDARY)
        }
        
        for btn_name, (text, command, color) in self.buttons.items():
            btn = tk.Button(
                self.buttons_frame,
                text=text,
                command=command,
                bg=color,
                fg=Theme.LIGHT,
                relief="flat",
                padx=5,
                pady=3
            )
            btn.pack(side="left", padx=2)

    def _setup_layout(self):
        # Configure grid weights
        self.root.grid_rowconfigure(2, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Place frames
        self.title_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=2)
        self.search_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=2)
        self.table_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=2)
        self.buttons_frame.grid(row=3, column=0, sticky="ew", padx=5, pady=2)
        
        # Search layout
        self.search_entry.pack(fill="x", padx=5)
        
        # Table layout
        self.table.grid(row=0, column=0, sticky="nsew")
        self.y_scroll.grid(row=0, column=1, sticky="ns")
        self.x_scroll.grid(row=1, column=0, sticky="ew")
        
        # Configure table frame grid weights
        self.table_frame.grid_rowconfigure(0, weight=1)
        self.table_frame.grid_columnconfigure(0, weight=1)

    def _setup_bindings(self):
        self.table.bind("<Double-1>", lambda e: self.view_record())
        self.root.bind("<Control-f>", lambda e: self.search_entry.focus())
        self.root.bind("<Control-n>", lambda e: self.add_record())
        self.root.bind("<Control-s>", lambda e: self.db.save_data())

    def _sort_table(self, col):
        records = [(self.table.set(item, col), item) for item in self.table.get_children('')]
        records.sort()
        
        for index, (_, item) in enumerate(records):
            self.table.move(item, '', index)

    def _on_search(self, event=None):
        search_term = self.search_entry.get()
        if search_term == self.search_entry.placeholder:
            return
        
        if search_term:
            records = self.db.search_records(search_term)
            self.load_table(records)
        else:
            self.load_table()

    def load_table(self, records=None):
        for item in self.table.get_children():
            self.table.delete(item)
        
        for record in (records or self.db.records):
            self.table.insert('', 'end', values=(
                record.id,
                record.name,
                record.role,
                record.department,
                record.email,
                record.phone,
                record.hire_date,
                record.status
            ))

    def add_record(self):
        self._open_record_form("Add Record")

    def update_record(self):
        selected = self.table.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a record to update.")
            return
        
        index = self.table.index(selected[0])
        self._open_record_form("Update Record", index)

    def view_record(self):
        selected = self.table.selection()
        if not selected:
            return
        
        index = self.table.index(selected[0])
        record = self.db.records[index]
        
        view_window = tk.Toplevel(self.root)
        view_window.title(f"View Record - {record.name}")
        view_window.geometry("400x500")
        view_window.configure(bg=Theme.BG)
        
        for i, (field, value) in enumerate(record.to_dict().items()):
            ttk.Label(
                view_window,
                text=f"{field.title()}:",
                style="Custom.TLabel"
            ).grid(row=i, column=0, padx=10, pady=5, sticky="e")
            
            ttk.Label(
                view_window,
                text=str(value),
                style="Custom.TLabel"
            ).grid(row=i, column=1, padx=10, pady=5, sticky="w")

    def delete_record(self):
        selected = self.table.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a record to delete.")
            return
        
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this record?"):
            index = self.table.index(selected[0])
            self.db.delete_record(index)
            self.load_table()

    def export_data(self):
        filename = "export_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".csv"
        with open(filename, 'w') as f:
            # Write header
            f.write(','.join(self.table['columns']) + '\n')
            
            # Write data
            for record in self.db.records:
                f.write(','.join(str(value) for value in record.to_dict().values()) + '\n')
        
        messagebox.showinfo("Success", f"Data exported to {filename}")

    def _open_record_form(self, title, index=None):
        form = RecordForm(self.root, title, self.db, index)
        self.root.wait_window(form.window)
        self.load_table()

class RecordForm:
    def __init__(self, parent, title, db: Database, index: Optional[int] = None):
        self.parent = parent
        self.db = db
        self.index = index
        
        self.window = tk.Toplevel(parent)
        self.window.title(title)
        self.window.geometry("500x600")
        self.window.configure(bg=Theme.BG)
        
        self._create_widgets()
        
        if index is not None:
            self._load_record(db.records[index])
            
        # Make window modal
        self.window.transient(parent)
        self.window.grab_set()

    def _create_widgets(self):
        # Create form fields
        self.fields = {}
        field_names = ["id", "name", "role", "department", "email", "phone", "hire_date", "status"]
        
        for i, field in enumerate(field_names):
            ttk.Label(
                self.window,
                text=f"{field.title()}:",
                style="Custom.TLabel"
            ).grid(row=i, column=0, padx=10, pady=5, sticky="e")
            
            var = tk.StringVar()
            entry = ttk.Entry(self.window, textvariable=var)
            entry.grid(row=i, column=1, padx=10, pady=5, sticky="ew")
            
            self.fields[field] = var
            
            # Add validation hints
            if field == "id":
                ttk.Label(
                    self.window,
                    text="Format: XX0000",
                    style="Custom.TLabel",
                    foreground="gray"
                ).grid(row=i, column=2, padx=5)
            elif field == "email":
                ttk.Label(
                    self.window,
                    text="example@mail.xxx",
                    style="Custom.TLabel",
                    foreground="gray"
                ).grid(row=i, column=2, padx=5)
            elif field == "hire_date":
                ttk.Label(
                    self.window,
                    text="YYYY-MM-DD",
                    style="Custom.TLabel",
                    foreground="gray"
                ).grid(row=i, column=2, padx=5)

        # Status dropdown
        status_var = self.fields["status"]
        status_dropdown = ttk.Combobox(
            self.window,
            textvariable=status_var,
            values=["Active", "Inactive", "On Leave", "Terminated"]
        )
        status_dropdown.grid(row=7, column=1, padx=10, pady=5, sticky="ew")
        status_var.set("Active")

        # Buttons
        button_frame = ttk.Frame(self.window, style="Custom.TFrame")
        button_frame.grid(row=len(field_names), column=0, columnspan=2, pady=20)
        
        ttk.Button(
            button_frame,
            text="Save",
            command=self.save,
            style="Custom.TButton"
        ).pack(side="left", padx=5)
        
        ttk.Button(
            button_frame,
            text="Cancel",
            command=self.window.destroy,
            style="Custom.TButton"
        ).pack(side="left", padx=5)

    def _load_record(self, record: Record):
        for field, var in self.fields.items():
            var.set(getattr(record, field))

    def validate_form(self) -> bool:
        # Validate required fields
        required_fields = ["id", "name", "role", "department"]
        for field in required_fields:
            if not self.fields[field].get().strip():
                messagebox.showerror("Error", f"{field.title()} is required.")
                return False
        
        # Validate ID format
        if not Validator.validate_id(self.fields["id"].get()):
            messagebox.showerror("Error", "Invalid ID format. Use XX0000 format.")
            return False
        
        # Validate email if provided
        email = self.fields["email"].get().strip()
        if email and not Validator.validate_email(email):
            messagebox.showerror("Error", "Invalid email format.")
            return False
        
        # Validate phone if provided
        phone = self.fields["phone"].get().strip()
        if phone and not Validator.validate_phone(phone):
            messagebox.showerror("Error", "Invalid phone format.")
            return False
        
        # Validate hire date format
        hire_date = self.fields["hire_date"].get().strip()
        if hire_date:
            try:
                datetime.strptime(hire_date, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Error", "Invalid date format. Use YYYY-MM-DD.")
                return False
        
        return True

    def save(self):
        if not self.validate_form():
            return
        
        record = Record(
            id=self.fields["id"].get(),
            name=self.fields["name"].get(),
            role=self.fields["role"].get(),
            department=self.fields["department"].get(),
            email=self.fields["email"].get(),
            phone=self.fields["phone"].get(),
            hire_date=self.fields["hire_date"].get(),
            status=self.fields["status"].get()
        )
        
        try:
            if self.index is not None:
                self.db.update_record(self.index, record)
            else:
                self.db.add_record(record)
            self.window.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save record: {str(e)}")

def main():
    root = tk.Tk()
    app = ManagementSystem(root)
    
    # Set window icon (if available)
    try:
        root.iconbitmap("icon.ico")
    except:
        pass
    
    # Make window responsive to screen size
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    
    # Center window on screen
    window_width = min(1200, int(screen_width * 0.8))
    window_height = min(800, int(screen_height * 0.8))
    
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    # Start the application
    root.mainloop()

if __name__ == "__main__":
    main()