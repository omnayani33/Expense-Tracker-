import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from tkinter import font as tkfont
import sqlite3
import hashlib
from datetime import datetime, date
import calendar
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd

# Database Setup
def init_database():
    conn = sqlite3.connect('expense_tracker.db')
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            registration_date DATE DEFAULT CURRENT_DATE
        )
    ''')
    
    # Categories table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Categories (
            category_id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_name TEXT NOT NULL UNIQUE
        )
    ''')
    
    # Expenses table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Expenses (
            expense_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            date DATE NOT NULL,
            amount REAL NOT NULL,
            description TEXT,
            FOREIGN KEY (user_id) REFERENCES Users (user_id),
            FOREIGN KEY (category_id) REFERENCES Categories (category_id)
        )
    ''')
    
    # Reports table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Reports (
            report_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            month TEXT NOT NULL,
            total_amount REAL NOT NULL,
            FOREIGN KEY (user_id) REFERENCES Users (user_id)
        )
    ''')
    
    # Budgets table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Budgets (
            budget_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            month TEXT NOT NULL,
            limit_amount REAL NOT NULL,
            FOREIGN KEY (user_id) REFERENCES Users (user_id),
            UNIQUE(user_id, month)
        )
    ''')
    
    # Insert default categories
    default_categories = ['Food', 'Travel', 'Shopping', 'Bills', 'Others']
    for category in default_categories:
        cursor.execute('INSERT OR IGNORE INTO Categories (category_name) VALUES (?)', (category,))
    
    # Create admin user if not exists
    admin_pass = hashlib.sha256('admin123'.encode()).hexdigest()
    cursor.execute('INSERT OR IGNORE INTO Users (name, email, password, is_admin) VALUES (?, ?, ?, ?)',
                   ('Admin', 'admin@expense.com', admin_pass, 1))
    
    conn.commit()
    conn.close()

# Main Application Class
class ExpenseTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Expense Tracker")
        self.root.geometry("1200x700")
        self.root.configure(bg='#f0f0f0')
        
        # Initialize database
        init_database()
        
        # Current user
        self.current_user = None
        self.is_admin = False
        
        # Fonts
        self.title_font = tkfont.Font(family='Helvetica', size=24, weight='bold')
        self.heading_font = tkfont.Font(family='Helvetica', size=16, weight='bold')
        self.normal_font = tkfont.Font(family='Helvetica', size=12)
        
        # Show login screen
        self.show_login_screen()
    
    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()
    
    def show_login_screen(self):
        self.clear_window()
        
        # Main frame
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        # Title
        title_label = tk.Label(main_frame, text="Expense Tracker", font=self.title_font, bg='#f0f0f0', fg='#333')
        title_label.pack(pady=20)
        
        # Login form
        login_frame = tk.LabelFrame(main_frame, text="Login", font=self.heading_font, bg='white', padx=40, pady=30)
        login_frame.pack(pady=20)
        
        # Email
        tk.Label(login_frame, text="Email:", font=self.normal_font, bg='white').grid(row=0, column=0, sticky='e', pady=10)
        self.login_email = tk.Entry(login_frame, font=self.normal_font, width=25)
        self.login_email.grid(row=0, column=1, pady=10, padx=10)
        
        # Password
        tk.Label(login_frame, text="Password:", font=self.normal_font, bg='white').grid(row=1, column=0, sticky='e', pady=10)
        self.login_password = tk.Entry(login_frame, font=self.normal_font, width=25, show="*")
        self.login_password.grid(row=1, column=1, pady=10, padx=10)
        
        # Buttons
        button_frame = tk.Frame(login_frame, bg='white')
        button_frame.grid(row=2, column=0, columnspan=2, pady=20)
        
        tk.Button(button_frame, text="Login", command=self.login, bg='#4CAF50', fg='white',
                 font=self.normal_font, padx=20, pady=5).pack(side=tk.LEFT, padx=10)
        
        tk.Button(button_frame, text="Register", command=self.show_register_screen, bg='#2196F3', fg='white',
                 font=self.normal_font, padx=20, pady=5).pack(side=tk.LEFT, padx=10)
        
        # Demo credentials
        demo_label = tk.Label(main_frame, text="Demo: admin@expense.com / admin123", font=('Helvetica', 10), bg='#f0f0f0')
        demo_label.pack(pady=10)
    
    def login(self):
        email = self.login_email.get()
        password = self.hash_password(self.login_password.get())
        
        if not email or not self.login_password.get():
            messagebox.showerror("Error", "Please fill all fields")
            return
        
        conn = sqlite3.connect('expense_tracker.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM Users WHERE email = ? AND password = ?', (email, password))
        user = cursor.fetchone()
        
        if user:
            self.current_user = {'id': user[0], 'name': user[1], 'email': user[2]}
            self.is_admin = user[4] == 1
            self.show_dashboard()
        else:
            messagebox.showerror("Error", "Invalid credentials")
        
        conn.close()
    
    def search_expenses(self):
        from_date = self.filter_from_date.get()
        to_date = self.filter_to_date.get()
        category = self.filter_category.get()
        
        filter_parts = []
        
        if from_date:
            filter_parts.append(f"AND e.date >= '{from_date}'")
        if to_date:
            filter_parts.append(f"AND e.date <= '{to_date}'")
        if category and category != 'All':
            filter_parts.append(f"AND c.category_name = '{category}'")
        
        filter_query = ' '.join(filter_parts)
        self.load_expenses(filter_query)
    
    def reset_filters(self):
        self.filter_from_date.delete(0, tk.END)
        self.filter_to_date.delete(0, tk.END)
        self.filter_category.current(0)
        self.load_expenses()
    
    def edit_expense(self):
        selected = self.expense_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select an expense to edit")
            return
        
        item = self.expense_tree.item(selected[0])
        expense_id = item['values'][0]
        
        # Create edit dialog
        edit_window = tk.Toplevel(self.root)
        edit_window.title("Edit Expense")
        edit_window.geometry("400x400")
        
        # Get current expense data
        conn = sqlite3.connect('expense_tracker.db')
        cursor = conn.cursor()
        cursor.execute('''SELECT e.date, c.category_name, e.amount, e.description, e.category_id
                         FROM Expenses e
                         JOIN Categories c ON e.category_id = c.category_id
                         WHERE e.expense_id = ?''', (expense_id,))
        current_data = cursor.fetchone()
        
        # Get categories
        cursor.execute('SELECT category_id, category_name FROM Categories')
        categories = cursor.fetchall()
        conn.close()
        
        # Form fields
        tk.Label(edit_window, text="Date:").grid(row=0, column=0, sticky='e', pady=5, padx=5)
        date_entry = tk.Entry(edit_window, width=20)
        date_entry.insert(0, current_data[0])
        date_entry.grid(row=0, column=1, pady=5, padx=5)
        
        tk.Label(edit_window, text="Category:").grid(row=1, column=0, sticky='e', pady=5, padx=5)
        category_var = tk.StringVar(value=current_data[1])
        category_map = {cat[1]: cat[0] for cat in categories}
        category_menu = ttk.Combobox(edit_window, textvariable=category_var, 
                                    values=[cat[1] for cat in categories], state='readonly', width=18)
        category_menu.grid(row=1, column=1, pady=5, padx=5)
        
        tk.Label(edit_window, text="Amount:").grid(row=2, column=0, sticky='e', pady=5, padx=5)
        amount_entry = tk.Entry(edit_window, width=20)
        amount_entry.insert(0, current_data[2])
        amount_entry.grid(row=2, column=1, pady=5, padx=5)
        
        tk.Label(edit_window, text="Description:").grid(row=3, column=0, sticky='ne', pady=5, padx=5)
        desc_text = tk.Text(edit_window, width=20, height=4)
        desc_text.insert('1.0', current_data[3] or '')
        desc_text.grid(row=3, column=1, pady=5, padx=5)
        
        # Save function
        def save_changes():
            try:
                new_date = date_entry.get()
                new_category = category_var.get()
                new_amount = float(amount_entry.get())
                new_desc = desc_text.get('1.0', tk.END).strip()
                
                category_id = category_map[new_category]
                
                conn = sqlite3.connect('expense_tracker.db')
                cursor = conn.cursor()
                cursor.execute('''UPDATE Expenses 
                                SET date = ?, category_id = ?, amount = ?, description = ?
                                WHERE expense_id = ?''',
                              (new_date, category_id, new_amount, new_desc, expense_id))
                conn.commit()
                conn.close()
                
                messagebox.showinfo("Success", "Expense updated successfully!")
                edit_window.destroy()
                self.load_expenses()
                
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        # Buttons
        button_frame = tk.Frame(edit_window)
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)
        
        tk.Button(button_frame, text="Save", command=save_changes, bg='#4CAF50', fg='white', padx=20).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel", command=edit_window.destroy, bg='#f44336', fg='white', padx=20).pack(side=tk.LEFT, padx=5)
    
    def delete_expense(self):
        selected = self.expense_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select an expense to delete")
            return
        
        if messagebox.askyesno("Confirm", "Are you sure you want to delete this expense?"):
            item = self.expense_tree.item(selected[0])
            expense_id = item['values'][0]
            
            conn = sqlite3.connect('expense_tracker.db')
            cursor = conn.cursor()
            cursor.execute('DELETE FROM Expenses WHERE expense_id = ?', (expense_id,))
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Success", "Expense deleted successfully!")
            self.load_expenses()
    
    def show_categories(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Title
        title_label = tk.Label(self.content_frame, text="Manage Categories", font=self.title_font, bg='#ecf0f1')
        title_label.pack(pady=20)
        
        # Add category frame
        add_frame = tk.LabelFrame(self.content_frame, text="Add New Category", font=self.heading_font, bg='white', padx=20, pady=20)
        add_frame.pack(pady=10)
        
        tk.Label(add_frame, text="Category Name:", font=self.normal_font, bg='white').pack(side=tk.LEFT, padx=10)
        self.new_category_entry = tk.Entry(add_frame, font=self.normal_font, width=20)
        self.new_category_entry.pack(side=tk.LEFT, padx=10)
        
        tk.Button(add_frame, text="Add Category", command=self.add_category, bg='#4CAF50', fg='white',
                 font=self.normal_font, padx=15).pack(side=tk.LEFT, padx=10)
        
        # Categories list
        list_frame = tk.LabelFrame(self.content_frame, text="Existing Categories", font=self.heading_font, bg='white', padx=20, pady=20)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Create treeview
        columns = ('ID', 'Category Name', 'Expense Count')
        self.category_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=10)
        
        for col in columns:
            self.category_tree.heading(col, text=col)
            self.category_tree.column(col, width=150)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.category_tree.yview)
        self.category_tree.configure(yscrollcommand=scrollbar.set)
        
        self.category_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Action buttons
        action_frame = tk.Frame(self.content_frame, bg='#ecf0f1')
        action_frame.pack(fill=tk.X, pady=10)
        
        tk.Button(action_frame, text="Edit Selected", command=self.edit_category, bg='#f39c12', fg='white',
                 font=self.normal_font, padx=15).pack(side=tk.LEFT, padx=10)
        
        tk.Button(action_frame, text="Delete Selected", command=self.delete_category, bg='#e74c3c', fg='white',
                 font=self.normal_font, padx=15).pack(side=tk.LEFT, padx=10)
        
        # Load categories
        self.load_categories()
    
    def load_categories(self):
        # Clear tree
        for item in self.category_tree.get_children():
            self.category_tree.delete(item)
        
        conn = sqlite3.connect('expense_tracker.db')
        cursor = conn.cursor()
        cursor.execute('''SELECT c.category_id, c.category_name, COUNT(e.expense_id) as expense_count
                         FROM Categories c
                         LEFT JOIN Expenses e ON c.category_id = e.category_id
                         GROUP BY c.category_id''')
        
        for row in cursor.fetchall():
            self.category_tree.insert('', 'end', values=row)
        
        conn.close()
    
    def add_category(self):
        category_name = self.new_category_entry.get().strip()
        
        if not category_name:
            messagebox.showerror("Error", "Please enter a category name")
            return
        
        try:
            conn = sqlite3.connect('expense_tracker.db')
            cursor = conn.cursor()
            cursor.execute('INSERT INTO Categories (category_name) VALUES (?)', (category_name,))
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Success", "Category added successfully!")
            self.new_category_entry.delete(0, tk.END)
            self.load_categories()
            
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Category already exists")
    
    def edit_category(self):
        selected = self.category_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a category to edit")
            return
        
        item = self.category_tree.item(selected[0])
        category_id = item['values'][0]
        current_name = item['values'][1]
        
        new_name = simpledialog.askstring("Edit Category", "Enter new category name:", initialvalue=current_name)
        
        if new_name and new_name != current_name:
            try:
                conn = sqlite3.connect('expense_tracker.db')
                cursor = conn.cursor()
                cursor.execute('UPDATE Categories SET category_name = ? WHERE category_id = ?', 
                              (new_name, category_id))
                conn.commit()
                conn.close()
                
                messagebox.showinfo("Success", "Category updated successfully!")
                self.load_categories()
                
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Category name already exists")
    
    def delete_category(self):
        selected = self.category_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a category to delete")
            return
        
        item = self.category_tree.item(selected[0])
        category_id = item['values'][0]
        expense_count = item['values'][2]
        
        if expense_count > 0:
            messagebox.showerror("Error", "Cannot delete category with existing expenses")
            return
        
        if messagebox.askyesno("Confirm", "Are you sure you want to delete this category?"):
            conn = sqlite3.connect('expense_tracker.db')
            cursor = conn.cursor()
            cursor.execute('DELETE FROM Categories WHERE category_id = ?', (category_id,))
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Success", "Category deleted successfully!")
            self.load_categories()
    
    def show_reports(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Title
        title_label = tk.Label(self.content_frame, text="Expense Reports", font=self.title_font, bg='#ecf0f1')
        title_label.pack(pady=20)
        
        # Report options
        options_frame = tk.Frame(self.content_frame, bg='#ecf0f1')
        options_frame.pack(pady=10)
        
        tk.Label(options_frame, text="Report Type:", font=self.normal_font, bg='#ecf0f1').pack(side=tk.LEFT, padx=5)
        
        self.report_type = tk.StringVar(value="monthly")
        report_types = [("Monthly", "monthly"), ("Yearly", "yearly"), ("By Category", "category")]
        
        for text, value in report_types:
            tk.Radiobutton(options_frame, text=text, variable=self.report_type, value=value,
                          font=self.normal_font, bg='#ecf0f1').pack(side=tk.LEFT, padx=10)
        
        tk.Button(options_frame, text="Generate Report", command=self.generate_report, bg='#3498db', fg='white',
                 font=self.normal_font, padx=20).pack(side=tk.LEFT, padx=20)
        
        # Report display frame
        self.report_frame = tk.Frame(self.content_frame, bg='white')
        self.report_frame.pack(fill=tk.BOTH, expand=True, pady=20)
    
    def generate_report(self):
        # Clear previous report
        for widget in self.report_frame.winfo_children():
            widget.destroy()
        
        report_type = self.report_type.get()
        
        if report_type == "monthly":
            self.generate_monthly_report()
        elif report_type == "yearly":
            self.generate_yearly_report()
        else:
            self.generate_category_report()
    
    def generate_monthly_report(self):
        # Create figure
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        fig.patch.set_facecolor('white')
        
        conn = sqlite3.connect('expense_tracker.db')
        cursor = conn.cursor()
        
        # Get monthly data
        cursor.execute('''SELECT strftime('%Y-%m', date) as month, SUM(amount) as total
                         FROM Expenses
                         WHERE user_id = ?
                         GROUP BY month
                         ORDER BY month DESC
                         LIMIT 12''', (self.current_user['id'],))
        
        monthly_data = cursor.fetchall()
        
        if monthly_data:
            months = [row[0] for row in monthly_data][::-1]
            amounts = [row[1] for row in monthly_data][::-1]
            
            # Bar chart
            ax1.bar(range(len(months)), amounts, color='#3498db')
            ax1.set_xticks(range(len(months)))
            ax1.set_xticklabels([m[-2:] + '/' + m[:4] for m in months], rotation=45)
            ax1.set_title('Monthly Expenses')
            ax1.set_ylabel('Amount (₹)')
            
            # Line chart
            ax2.plot(range(len(months)), amounts, marker='o', color='#e74c3c', linewidth=2, markersize=8)
            ax2.set_xticks(range(len(months)))
            ax2.set_xticklabels([m[-2:] + '/' + m[:4] for m in months], rotation=45)
            ax2.set_title('Expense Trend')
            ax2.set_ylabel('Amount (₹)')
            ax2.grid(True, alpha=0.3)
        
        conn.close()
        
        # Display chart
        canvas = FigureCanvasTkAgg(fig, self.report_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Summary stats
        stats_frame = tk.Frame(self.report_frame, bg='white')
        stats_frame.pack(fill=tk.X, pady=10)
        
        if monthly_data:
            avg_monthly = sum(amounts) / len(amounts)
            max_month = months[amounts.index(max(amounts))]
            min_month = months[amounts.index(min(amounts))]
            
            stats_text = f"Average Monthly Expense: ₹{avg_monthly:.2f}\n"
            stats_text += f"Highest: {max_month} (₹{max(amounts):.2f})\n"
            stats_text += f"Lowest: {min_month} (₹{min(amounts):.2f})"
            
            tk.Label(stats_frame, text=stats_text, font=self.normal_font, bg='white', justify='left').pack()
    
    def generate_yearly_report(self):
        fig, ax = plt.subplots(figsize=(10, 6))
        fig.patch.set_facecolor('white')
        
        conn = sqlite3.connect('expense_tracker.db')
        cursor = conn.cursor()
        
        # Get yearly data
        cursor.execute('''SELECT strftime('%Y', date) as year, SUM(amount) as total
                         FROM Expenses
                         WHERE user_id = ?
                         GROUP BY year
                         ORDER BY year''', (self.current_user['id'],))
        
        yearly_data = cursor.fetchall()
        
        if yearly_data:
            years = [row[0] for row in yearly_data]
            amounts = [row[1] for row in yearly_data]
            
            ax.bar(years, amounts, color='#2ecc71')
            ax.set_xlabel('Year')
            ax.set_ylabel('Total Expenses (₹)')
            ax.set_title('Yearly Expense Summary')
            
            # Add value labels on bars
            for i, (year, amount) in enumerate(zip(years, amounts)):
                ax.text(i, amount, f'₹{amount:.0f}', ha='center', va='bottom')
        
        conn.close()
        
        # Display chart
        canvas = FigureCanvasTkAgg(fig, self.report_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def generate_category_report(self):
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        fig.patch.set_facecolor('white')
        
        conn = sqlite3.connect('expense_tracker.db')
        cursor = conn.cursor()
        
        # Get category data
        cursor.execute('''SELECT c.category_name, SUM(e.amount) as total
                         FROM Expenses e
                         JOIN Categories c ON e.category_id = c.category_id
                         WHERE e.user_id = ?
                         GROUP BY c.category_id
                         ORDER BY total DESC''', (self.current_user['id'],))
        
        category_data = cursor.fetchall()
        
        if category_data:
            categories = [row[0] for row in category_data]
            amounts = [row[1] for row in category_data]
            
            # Pie chart
            ax1.pie(amounts, labels=categories, autopct='%1.1f%%', startangle=90)
            ax1.set_title('Expense Distribution by Category')
            
            # Bar chart
            ax2.barh(categories, amounts, color='#9b59b6')
            ax2.set_xlabel('Amount (₹)')
            ax2.set_title('Expenses by Category')
            
            # Add value labels
            for i, amount in enumerate(amounts):
                ax2.text(amount, i, f' ₹{amount:.2f}', va='center')
        
        conn.close()
        
        # Display chart
        canvas = FigureCanvasTkAgg(fig, self.report_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def show_budget(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Title
        title_label = tk.Label(self.content_frame, text="Budget Management", font=self.title_font, bg='#ecf0f1')
        title_label.pack(pady=20)
        
        # Set budget frame
        set_frame = tk.LabelFrame(self.content_frame, text="Set Monthly Budget", font=self.heading_font, bg='white', padx=30, pady=20)
        set_frame.pack(pady=10)
        
        tk.Label(set_frame, text="Month (YYYY-MM):", font=self.normal_font, bg='white').grid(row=0, column=0, sticky='e', pady=5)
        self.budget_month = tk.Entry(set_frame, font=self.normal_font, width=15)
        self.budget_month.insert(0, datetime.now().strftime('%Y-%m'))
        self.budget_month.grid(row=0, column=1, pady=5, padx=10)
        
        tk.Label(set_frame, text="Budget Limit (₹):", font=self.normal_font, bg='white').grid(row=1, column=0, sticky='e', pady=5)
        self.budget_amount = tk.Entry(set_frame, font=self.normal_font, width=15)
        self.budget_amount.grid(row=1, column=1, pady=5, padx=10)
        
        tk.Button(set_frame, text="Set Budget", command=self.set_budget, bg='#4CAF50', fg='white',
                 font=self.normal_font, padx=20).grid(row=2, column=0, columnspan=2, pady=15)
        
        # Budget overview
        overview_frame = tk.LabelFrame(self.content_frame, text="Budget Overview", font=self.heading_font, bg='white', padx=20, pady=20)
        overview_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Create treeview
        columns = ('Month', 'Budget', 'Expenses', 'Remaining', 'Status')
        self.budget_tree = ttk.Treeview(overview_frame, columns=columns, show='headings', height=10)
        
        for col in columns:
            self.budget_tree.heading(col, text=col)
            self.budget_tree.column(col, width=120)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(overview_frame, orient=tk.VERTICAL, command=self.budget_tree.yview)
        self.budget_tree.configure(yscrollcommand=scrollbar.set)
        
        self.budget_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Load budgets
        self.load_budgets()
    
    def set_budget(self):
        month = self.budget_month.get()
        try:
            amount = float(self.budget_amount.get())
            
            if amount <= 0:
                messagebox.showerror("Error", "Budget amount must be positive")
                return
            
            conn = sqlite3.connect('expense_tracker.db')
            cursor = conn.cursor()
            cursor.execute('INSERT OR REPLACE INTO Budgets (user_id, month, limit_amount) VALUES (?, ?, ?)',
                          (self.current_user['id'], month, amount))
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Success", "Budget set successfully!")
            self.budget_amount.delete(0, tk.END)
            self.load_budgets()
            
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid amount")
    
    def load_budgets(self):
        # Clear tree
        for item in self.budget_tree.get_children():
            self.budget_tree.delete(item)
        
        conn = sqlite3.connect('expense_tracker.db')
        cursor = conn.cursor()
        
        # Get budgets with expenses
        cursor.execute('''SELECT b.month, b.limit_amount,
                         COALESCE(SUM(e.amount), 0) as expenses
                         FROM Budgets b
                         LEFT JOIN Expenses e ON b.user_id = e.user_id 
                             AND strftime('%Y-%m', e.date) = b.month
                         WHERE b.user_id = ?
                         GROUP BY b.month
                         ORDER BY b.month DESC''', (self.current_user['id'],))
        
        for row in cursor.fetchall():
            month, budget, expenses = row
            remaining = budget - expenses
            status = "Within Budget" if remaining >= 0 else "Over Budget"
            
            # Color code the row
            tag = 'within' if remaining >= 0 else 'over'
            self.budget_tree.insert('', 'end', values=(month, f'₹{budget:.2f}', f'₹{expenses:.2f}', 
                                                      f'₹{remaining:.2f}', status), tags=(tag,))
        
        # Configure tags
        self.budget_tree.tag_configure('within', foreground='green')
        self.budget_tree.tag_configure('over', foreground='red')
        
        conn.close()
    
    def show_profile(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Title
        title_label = tk.Label(self.content_frame, text="Profile Management", font=self.title_font, bg='#ecf0f1')
        title_label.pack(pady=20)
        
        # Profile info
        info_frame = tk.LabelFrame(self.content_frame, text="Profile Information", font=self.heading_font, bg='white', padx=40, pady=30)
        info_frame.pack(pady=20)
        
        # Get user info
        conn = sqlite3.connect('expense_tracker.db')
        cursor = conn.cursor()
        cursor.execute('SELECT name, email, registration_date FROM Users WHERE user_id = ?', 
                      (self.current_user['id'],))
        user_info = cursor.fetchone()
        conn.close()
        
        tk.Label(info_frame, text=f"Name: {user_info[0]}", font=self.normal_font, bg='white').pack(anchor='w', pady=5)
        tk.Label(info_frame, text=f"Email: {user_info[1]}", font=self.normal_font, bg='white').pack(anchor='w', pady=5)
        tk.Label(info_frame, text=f"Member Since: {user_info[2]}", font=self.normal_font, bg='white').pack(anchor='w', pady=5)
        
        # Update profile
        update_frame = tk.LabelFrame(self.content_frame, text="Update Profile", font=self.heading_font, bg='white', padx=40, pady=30)
        update_frame.pack(pady=20)
        
        tk.Label(update_frame, text="New Name:", font=self.normal_font, bg='white').grid(row=0, column=0, sticky='e', pady=5)
        self.update_name = tk.Entry(update_frame, font=self.normal_font, width=25)
        self.update_name.insert(0, user_info[0])
        self.update_name.grid(row=0, column=1, pady=5, padx=10)
        
        tk.Label(update_frame, text="New Password:", font=self.normal_font, bg='white').grid(row=1, column=0, sticky='e', pady=5)
        self.update_password = tk.Entry(update_frame, font=self.normal_font, width=25, show="*")
        self.update_password.grid(row=1, column=1, pady=5, padx=10)
        
        tk.Label(update_frame, text="Confirm Password:", font=self.normal_font, bg='white').grid(row=2, column=0, sticky='e', pady=5)
        self.update_confirm = tk.Entry(update_frame, font=self.normal_font, width=25, show="*")
        self.update_confirm.grid(row=2, column=1, pady=5, padx=10)
        
        tk.Button(update_frame, text="Update Profile", command=self.update_profile, bg='#4CAF50', fg='white',
                 font=self.normal_font, padx=20).grid(row=3, column=0, columnspan=2, pady=15)
    
    def update_profile(self):
        new_name = self.update_name.get()
        new_password = self.update_password.get()
        confirm_password = self.update_confirm.get()
        
        if not new_name:
            messagebox.showerror("Error", "Name cannot be empty")
            return
        
        conn = sqlite3.connect('expense_tracker.db')
        cursor = conn.cursor()
        
        # Update password if provided
        if new_password:
            if new_password != confirm_password:
                messagebox.showerror("Error", "Passwords do not match")
                conn.close()
                return
            
            if len(new_password) < 6:
                messagebox.showerror("Error", "Password must be at least 6 characters")
                conn.close()
                return
            
            hashed_password = self.hash_password(new_password)
            cursor.execute('UPDATE Users SET name = ?, password = ? WHERE user_id = ?', 
                          (new_name, hashed_password, self.current_user['id']))
        else:
            # Update name only
            cursor.execute('UPDATE Users SET name = ? WHERE user_id = ?', 
                          (new_name, self.current_user['id']))
        
        conn.commit()
        conn.close()
        
        self.current_user['name'] = new_name
        messagebox.showinfo("Success", "Profile updated successfully!")
        self.update_password.delete(0, tk.END)
        self.update_confirm.delete(0, tk.END)
    
    def show_register_screen(self):
        self.clear_window()
        
        # Main frame
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        # Title
        title_label = tk.Label(main_frame, text="Register New Account", font=self.title_font, bg='#f0f0f0', fg='#333')
        title_label.pack(pady=20)
        
        # Register form
        register_frame = tk.LabelFrame(main_frame, text="Registration", font=self.heading_font, bg='white', padx=40, pady=30)
        register_frame.pack(pady=20)
        
        # Name
        tk.Label(register_frame, text="Name:", font=self.normal_font, bg='white').grid(row=0, column=0, sticky='e', pady=10)
        self.reg_name = tk.Entry(register_frame, font=self.normal_font, width=25)
        self.reg_name.grid(row=0, column=1, pady=10, padx=10)
        
        # Email
        tk.Label(register_frame, text="Email:", font=self.normal_font, bg='white').grid(row=1, column=0, sticky='e', pady=10)
        self.reg_email = tk.Entry(register_frame, font=self.normal_font, width=25)
        self.reg_email.grid(row=1, column=1, pady=10, padx=10)
        
        # Password
        tk.Label(register_frame, text="Password:", font=self.normal_font, bg='white').grid(row=2, column=0, sticky='e', pady=10)
        self.reg_password = tk.Entry(register_frame, font=self.normal_font, width=25, show="*")
        self.reg_password.grid(row=2, column=1, pady=10, padx=10)
        
        # Confirm Password
        tk.Label(register_frame, text="Confirm Password:", font=self.normal_font, bg='white').grid(row=3, column=0, sticky='e', pady=10)
        self.reg_confirm_password = tk.Entry(register_frame, font=self.normal_font, width=25, show="*")
        self.reg_confirm_password.grid(row=3, column=1, pady=10, padx=10)
        
        # Buttons
        button_frame = tk.Frame(register_frame, bg='white')
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)
        
        tk.Button(button_frame, text="Register", command=self.register, bg='#4CAF50', fg='white',
                 font=self.normal_font, padx=20, pady=5).pack(side=tk.LEFT, padx=10)
        
        tk.Button(button_frame, text="Back to Login", command=self.show_login_screen, bg='#f44336', fg='white',
                 font=self.normal_font, padx=20, pady=5).pack(side=tk.LEFT, padx=10)
    
    def register(self):
        name = self.reg_name.get()
        email = self.reg_email.get()
        password = self.reg_password.get()
        confirm_password = self.reg_confirm_password.get()
        
        if not all([name, email, password, confirm_password]):
            messagebox.showerror("Error", "Please fill all fields")
            return
        
        if password != confirm_password:
            messagebox.showerror("Error", "Passwords do not match")
            return
        
        if len(password) < 6:
            messagebox.showerror("Error", "Password must be at least 6 characters")
            return
        
        hashed_password = self.hash_password(password)
        
        try:
            conn = sqlite3.connect('expense_tracker.db')
            cursor = conn.cursor()
            cursor.execute('INSERT INTO Users (name, email, password) VALUES (?, ?, ?)',
                          (name, email, hashed_password))
            conn.commit()
            conn.close()
            messagebox.showinfo("Success", "Registration successful! Please login.")
            self.show_login_screen()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Email already exists")
    
    def show_dashboard(self):
        self.clear_window()
        
        # Header frame
        header_frame = tk.Frame(self.root, bg='#2c3e50', height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        # Welcome label
        welcome_text = f"Welcome, {self.current_user['name']}" + (" (Admin)" if self.is_admin else "")
        welcome_label = tk.Label(header_frame, text=welcome_text, font=self.heading_font, bg='#2c3e50', fg='white')
        welcome_label.pack(side=tk.LEFT, padx=20, pady=20)
        
        # Logout button
        tk.Button(header_frame, text="Logout", command=self.logout, bg='#e74c3c', fg='white',
                 font=self.normal_font, padx=15, pady=5).pack(side=tk.RIGHT, padx=20, pady=20)
        
        # Main container
        main_container = tk.Frame(self.root, bg='#ecf0f1')
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Sidebar
        sidebar = tk.Frame(main_container, bg='#34495e', width=250)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)
        
        # Menu buttons
        menu_buttons = [
            ("Dashboard", self.show_dashboard_content),
            ("Add Expense", self.show_add_expense),
            ("View Expenses", self.show_view_expenses),
            ("Categories", self.show_categories),
            ("Reports", self.show_reports),
            ("Budget", self.show_budget),
            ("Profile", self.show_profile),
        ]
        
        if self.is_admin:
            menu_buttons.extend([
                ("Manage Users", self.show_manage_users),
                ("Admin Panel", self.show_admin_panel),
            ])
        
        for text, command in menu_buttons:
            btn = tk.Button(sidebar, text=text, command=command, bg='#34495e', fg='white',
                           font=self.normal_font, bd=0, pady=15, anchor='w', padx=20)
            btn.pack(fill=tk.X)
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg='#2c3e50'))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg='#34495e'))
        
        # Content area
        self.content_frame = tk.Frame(main_container, bg='#ecf0f1')
        self.content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Show dashboard content
        self.show_dashboard_content()
    
    def show_dashboard_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Title
        title_label = tk.Label(self.content_frame, text="Dashboard Overview", font=self.title_font, bg='#ecf0f1')
        title_label.pack(pady=20)
        
        # Stats frame
        stats_frame = tk.Frame(self.content_frame, bg='#ecf0f1')
        stats_frame.pack(fill=tk.BOTH, expand=True)
        
        # Get statistics
        conn = sqlite3.connect('expense_tracker.db')
        cursor = conn.cursor()
        
        # Total expenses
        cursor.execute('SELECT SUM(amount) FROM Expenses WHERE user_id = ?', (self.current_user['id'],))
        total_expenses = cursor.fetchone()[0] or 0
        
        # This month expenses
        current_month = datetime.now().strftime('%Y-%m')
        cursor.execute('''SELECT SUM(amount) FROM Expenses 
                         WHERE user_id = ? AND strftime('%Y-%m', date) = ?''',
                      (self.current_user['id'], current_month))
        month_expenses = cursor.fetchone()[0] or 0
        
        # Number of transactions
        cursor.execute('SELECT COUNT(*) FROM Expenses WHERE user_id = ?', (self.current_user['id'],))
        transaction_count = cursor.fetchone()[0]
        
        # Budget check
        cursor.execute('SELECT limit_amount FROM Budgets WHERE user_id = ? AND month = ?',
                      (self.current_user['id'], current_month))
        budget_result = cursor.fetchone()
        budget_limit = budget_result[0] if budget_result else 0
        
        conn.close()
        
        # Create stat cards
        stats = [
            ("Total Expenses", f"₹{total_expenses:.2f}", '#3498db'),
            ("This Month", f"₹{month_expenses:.2f}", '#2ecc71'),
            ("Transactions", str(transaction_count), '#e74c3c'),
            ("Budget Status", f"₹{month_expenses:.2f} / ₹{budget_limit:.2f}" if budget_limit > 0 else "No budget set", '#f39c12')
        ]
        
        for i, (label, value, color) in enumerate(stats):
            card = tk.Frame(stats_frame, bg=color, width=250, height=150)
            card.grid(row=i//2, column=i%2, padx=20, pady=20)
            card.pack_propagate(False)
            
            tk.Label(card, text=label, font=self.normal_font, bg=color, fg='white').pack(pady=20)
            tk.Label(card, text=value, font=self.heading_font, bg=color, fg='white').pack()
        
        # Recent expenses
        recent_frame = tk.LabelFrame(self.content_frame, text="Recent Expenses", font=self.heading_font, bg='white', padx=20, pady=20)
        recent_frame.pack(fill=tk.BOTH, expand=True, pady=20)
        
        # Create treeview
        columns = ('Date', 'Category', 'Amount', 'Description')
        tree = ttk.Treeview(recent_frame, columns=columns, show='headings', height=8)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(recent_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Load recent expenses
        conn = sqlite3.connect('expense_tracker.db')
        cursor = conn.cursor()
        cursor.execute('''SELECT e.date, c.category_name, e.amount, e.description
                         FROM Expenses e
                         JOIN Categories c ON e.category_id = c.category_id
                         WHERE e.user_id = ?
                         ORDER BY e.date DESC LIMIT 10''', (self.current_user['id'],))
        
        for row in cursor.fetchall():
            tree.insert('', 'end', values=row)
        
        conn.close()
    
    def show_add_expense(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Title
        title_label = tk.Label(self.content_frame, text="Add New Expense", font=self.title_font, bg='#ecf0f1')
        title_label.pack(pady=20)
        
        # Form frame
        form_frame = tk.LabelFrame(self.content_frame, text="Expense Details", font=self.heading_font, bg='white', padx=40, pady=30)
        form_frame.pack(pady=20)
        
        # Date
        tk.Label(form_frame, text="Date:", font=self.normal_font, bg='white').grid(row=0, column=0, sticky='e', pady=10)
        self.expense_date = tk.Entry(form_frame, font=self.normal_font, width=25)
        self.expense_date.grid(row=0, column=1, pady=10, padx=10)
        self.expense_date.insert(0, date.today().strftime('%Y-%m-%d'))
        
        # Category
        tk.Label(form_frame, text="Category:", font=self.normal_font, bg='white').grid(row=1, column=0, sticky='e', pady=10)
        
        # Get categories
        conn = sqlite3.connect('expense_tracker.db')
        cursor = conn.cursor()
        cursor.execute('SELECT category_id, category_name FROM Categories')
        categories = cursor.fetchall()
        conn.close()
        
        self.category_var = tk.StringVar()
        self.category_map = {cat[1]: cat[0] for cat in categories}
        category_menu = ttk.Combobox(form_frame, textvariable=self.category_var, values=[cat[1] for cat in categories],
                                     font=self.normal_font, width=23, state='readonly')
        category_menu.grid(row=1, column=1, pady=10, padx=10)
        if categories:
            category_menu.current(0)
        
        # Amount
        tk.Label(form_frame, text="Amount (₹):", font=self.normal_font, bg='white').grid(row=2, column=0, sticky='e', pady=10)
        self.expense_amount = tk.Entry(form_frame, font=self.normal_font, width=25)
        self.expense_amount.grid(row=2, column=1, pady=10, padx=10)
        
        # Description
        tk.Label(form_frame, text="Description:", font=self.normal_font, bg='white').grid(row=3, column=0, sticky='e', pady=10)
        self.expense_description = tk.Text(form_frame, font=self.normal_font, width=25, height=4)
        self.expense_description.grid(row=3, column=1, pady=10, padx=10)
        
        # Buttons
        button_frame = tk.Frame(form_frame, bg='white')
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)
        
        tk.Button(button_frame, text="Add Expense", command=self.add_expense, bg='#4CAF50', fg='white',
                 font=self.normal_font, padx=20, pady=5).pack(side=tk.LEFT, padx=10)
        
        tk.Button(button_frame, text="Clear", command=self.clear_expense_form, bg='#f44336', fg='white',
                 font=self.normal_font, padx=20, pady=5).pack(side=tk.LEFT, padx=10)
    
    def add_expense(self):
        try:
            expense_date = self.expense_date.get()
            category = self.category_var.get()
            amount = float(self.expense_amount.get())
            description = self.expense_description.get('1.0', tk.END).strip()
            
            if not all([expense_date, category, amount]):
                messagebox.showerror("Error", "Please fill all required fields")
                return
            
            # Validate date format
            datetime.strptime(expense_date, '%Y-%m-%d')
            
            category_id = self.category_map[category]
            
            conn = sqlite3.connect('expense_tracker.db')
            cursor = conn.cursor()
            cursor.execute('''INSERT INTO Expenses (user_id, category_id, date, amount, description)
                            VALUES (?, ?, ?, ?, ?)''',
                          (self.current_user['id'], category_id, expense_date, amount, description))
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Success", "Expense added successfully!")
            self.clear_expense_form()
            
            # Check budget
            self.check_budget_alert()
            
        except ValueError as e:
            messagebox.showerror("Error", "Please enter valid data")
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def clear_expense_form(self):
        self.expense_date.delete(0, tk.END)
        self.expense_date.insert(0, date.today().strftime('%Y-%m-%d'))
        self.expense_amount.delete(0, tk.END)
        self.expense_description.delete('1.0', tk.END)
    
    def check_budget_alert(self):
        current_month = datetime.now().strftime('%Y-%m')
        
        conn = sqlite3.connect('expense_tracker.db')
        cursor = conn.cursor()
        
        # Get budget limit
        cursor.execute('SELECT limit_amount FROM Budgets WHERE user_id = ? AND month = ?',
                      (self.current_user['id'], current_month))
        budget_result = cursor.fetchone()
        
        if budget_result:
            budget_limit = budget_result[0]
            
            # Get total expenses for the month
            cursor.execute('''SELECT SUM(amount) FROM Expenses 
                            WHERE user_id = ? AND strftime('%Y-%m', date) = ?''',
                          (self.current_user['id'], current_month))
            total_expenses = cursor.fetchone()[0] or 0
            
            if total_expenses > budget_limit:
                messagebox.showwarning("Budget Alert", 
                                     f"You have exceeded your budget!\nBudget: ₹{budget_limit:.2f}\nExpenses: ₹{total_expenses:.2f}")
            elif total_expenses > budget_limit * 0.8:
                messagebox.showwarning("Budget Warning", 
                                     f"You have used {(total_expenses/budget_limit*100):.1f}% of your budget")
        
        conn.close()
    
    def show_view_expenses(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Title
        title_label = tk.Label(self.content_frame, text="View Expenses", font=self.title_font, bg='#ecf0f1')
        title_label.pack(pady=10)
        
        # Filter frame
        filter_frame = tk.Frame(self.content_frame, bg='#ecf0f1')
        filter_frame.pack(fill=tk.X, pady=10)
        
        # Date range filter
        tk.Label(filter_frame, text="From:", font=self.normal_font, bg='#ecf0f1').pack(side=tk.LEFT, padx=5)
        self.filter_from_date = tk.Entry(filter_frame, font=self.normal_font, width=12)
        self.filter_from_date.pack(side=tk.LEFT, padx=5)
        
        tk.Label(filter_frame, text="To:", font=self.normal_font, bg='#ecf0f1').pack(side=tk.LEFT, padx=5)
        self.filter_to_date = tk.Entry(filter_frame, font=self.normal_font, width=12)
        self.filter_to_date.pack(side=tk.LEFT, padx=5)
        
        # Category filter
        tk.Label(filter_frame, text="Category:", font=self.normal_font, bg='#ecf0f1').pack(side=tk.LEFT, padx=5)
        self.filter_category = ttk.Combobox(filter_frame, font=self.normal_font, width=15, state='readonly')
        self.filter_category.pack(side=tk.LEFT, padx=5)
        
        # Load categories
        conn = sqlite3.connect('expense_tracker.db')
        cursor = conn.cursor()
        cursor.execute('SELECT category_name FROM Categories')
        categories = ['All'] + [cat[0] for cat in cursor.fetchall()]
        self.filter_category['values'] = categories
        self.filter_category.current(0)
        conn.close()
        
        # Search button
        tk.Button(filter_frame, text="Search", command=self.search_expenses, bg='#3498db', fg='white',
                 font=self.normal_font, padx=15).pack(side=tk.LEFT, padx=10)
        
        tk.Button(filter_frame, text="Reset", command=self.reset_filters, bg='#95a5a6', fg='white',
                 font=self.normal_font, padx=15).pack(side=tk.LEFT, padx=5)
        
        # Table frame
        table_frame = tk.Frame(self.content_frame, bg='white')
        table_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Create treeview
        columns = ('ID', 'Date', 'Category', 'Amount', 'Description')
        self.expense_tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=15)
        
        # Define headings
        self.expense_tree.heading('ID', text='ID')
        self.expense_tree.heading('Date', text='Date')
        self.expense_tree.heading('Category', text='Category')
        self.expense_tree.heading('Amount', text='Amount (₹)')
        self.expense_tree.heading('Description', text='Description')
        
        # Column widths
        self.expense_tree.column('ID', width=50)
        self.expense_tree.column('Date', width=100)
        self.expense_tree.column('Category', width=120)
        self.expense_tree.column('Amount', width=100)
        self.expense_tree.column('Description', width=300)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.expense_tree.yview)
        self.expense_tree.configure(yscrollcommand=scrollbar.set)
        
        self.expense_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Action buttons
        action_frame = tk.Frame(self.content_frame, bg='#ecf0f1')
        action_frame.pack(fill=tk.X, pady=10)
        
        tk.Button(action_frame, text="Edit Selected", command=self.edit_expense, bg='#f39c12', fg='white',
                 font=self.normal_font, padx=15).pack(side=tk.LEFT, padx=10)
        
        tk.Button(action_frame, text="Delete Selected", command=self.delete_expense, bg='#e74c3c', fg='white',
                 font=self.normal_font, padx=15).pack(side=tk.LEFT, padx=10)
        
        # Load expenses
        self.load_expenses()
    
    def load_expenses(self, filter_query=""):
        # Clear tree
        for item in self.expense_tree.get_children():
            self.expense_tree.delete(item)
        
        conn = sqlite3.connect('expense_tracker.db')
        cursor = conn.cursor()
        
        # Build query
        query = '''SELECT e.expense_id, e.date, c.category_name, e.amount, e.description
                   FROM Expenses e
                   JOIN Categories c ON e.category_id = c.category_id
                   WHERE e.user_id = ? {filters}
                   ORDER BY e.date DESC'''
        query = query.format(filters=filter_query)
        
        cursor.execute(query, (self.current_user['id'],))
        rows = cursor.fetchall()
        
        for row in rows:
            expense_id, date, category, amount, description = row
            self.expense_tree.insert('', 'end',
                values=(expense_id, date, category, f"{amount:.2f}", description))
        
        conn.close()
    
    def load_users(self):
        # Clear tree
        for item in self.user_tree.get_children():
            self.user_tree.delete(item)
        
        conn = sqlite3.connect('expense_tracker.db')
        cursor = conn.cursor()
        
        # Get users with expense statistics
        cursor.execute('''SELECT u.user_id, u.name, u.email, u.is_admin, u.registration_date,
                         COALESCE(SUM(e.amount), 0) as total_expenses
                         FROM Users u
                         LEFT JOIN Expenses e ON u.user_id = e.user_id
                         GROUP BY u.user_id''')
        
        for row in cursor.fetchall():
            user_id, name, email, is_admin, reg_date, total_expenses = row
            admin_status = "Yes" if is_admin else "No"
            self.user_tree.insert('', 'end', values=(user_id, name, email, admin_status, reg_date, f"₹{total_expenses:.2f}"))
        
        conn.close()
    
    def toggle_admin_status(self):
        selected = self.user_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a user")
            return
        
        item = self.user_tree.item(selected[0])
        user_id = item['values'][0]
        user_name = item['values'][1]
        current_admin = item['values'][3] == "Yes"
        
        if user_id == self.current_user['id']:
            messagebox.showerror("Error", "Cannot modify your own admin status")
            return
        
        new_admin = not current_admin
        action = "grant" if new_admin else "remove"
        
        if messagebox.askyesno("Confirm", f"Are you sure you want to {action} admin privileges for {user_name}?"):
            conn = sqlite3.connect('expense_tracker.db')
            cursor = conn.cursor()
            cursor.execute('UPDATE Users SET is_admin = ? WHERE user_id = ?', (int(new_admin), user_id))
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Success", f"Admin status updated for {user_name}")
            self.load_users()
    
    def show_manage_users(self):
        if not self.is_admin:
            messagebox.showerror("Error", "Admin access required")
            return
        
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Title
        title_label = tk.Label(self.content_frame, text="Manage Users", font=self.title_font, bg='#ecf0f1')
        title_label.pack(pady=20)
        
        # Users list frame
        list_frame = tk.LabelFrame(self.content_frame, text="Registered Users", font=self.heading_font, bg='white', padx=20, pady=20)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Create treeview
        columns = ('ID', 'Name', 'Email', 'Admin', 'Registration Date', 'Total Expenses')
        self.user_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=12)
        
        for col in columns:
            self.user_tree.heading(col, text=col)
            self.user_tree.column(col, width=120)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.user_tree.yview)
        self.user_tree.configure(yscrollcommand=scrollbar.set)
        
        self.user_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Action buttons
        action_frame = tk.Frame(self.content_frame, bg='#ecf0f1')
        action_frame.pack(fill=tk.X, pady=10)
        
        tk.Button(action_frame, text="Toggle Admin Status", command=self.toggle_admin_status, bg='#f39c12', fg='white',
                 font=self.normal_font, padx=15).pack(side=tk.LEFT, padx=10)
        
        tk.Button(action_frame, text="Delete User", command=self.delete_user, bg='#e74c3c', fg='white',
                 font=self.normal_font, padx=15).pack(side=tk.LEFT, padx=10)
        
        tk.Button(action_frame, text="Reset Password", command=self.reset_user_password, bg='#3498db', fg='white',
                 font=self.normal_font, padx=15).pack(side=tk.LEFT, padx=10)
        
        # Load users
        self.load_users()
    
    def delete_user(self):
        selected = self.user_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a user")
            return
        
        item = self.user_tree.item(selected[0])
        user_id = item['values'][0]
        
        if user_id == self.current_user['id']:
            messagebox.showerror("Error", "Cannot delete your own account")
            return
        
        if messagebox.askyesno("Confirm", "Are you sure? This will delete all user data including expenses."):
            conn = sqlite3.connect('expense_tracker.db')
            cursor = conn.cursor()
            
            # Delete user's expenses first
            cursor.execute('DELETE FROM Expenses WHERE user_id = ?', (user_id,))
            cursor.execute('DELETE FROM Reports WHERE user_id = ?', (user_id,))
            cursor.execute('DELETE FROM Budgets WHERE user_id = ?', (user_id,))
            cursor.execute('DELETE FROM Users WHERE user_id = ?', (user_id,))
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Success", "User deleted successfully")
            self.load_users()
    
    def reset_user_password(self):
        selected = self.user_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a user")
            return
        
        item = self.user_tree.item(selected[0])
        user_id = item['values'][0]
        user_name = item['values'][1]
        
        new_password = simpledialog.askstring("Reset Password", f"Enter new password for {user_name}:", show='*')
        
        if new_password:
            if len(new_password) < 6:
                messagebox.showerror("Error", "Password must be at least 6 characters")
                return
            
            hashed_password = self.hash_password(new_password)
            
            conn = sqlite3.connect('expense_tracker.db')
            cursor = conn.cursor()
            cursor.execute('UPDATE Users SET password = ? WHERE user_id = ?', (hashed_password, user_id))
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Success", "Password reset successfully")
    
    def show_admin_panel(self):
        if not self.is_admin:
            messagebox.showerror("Error", "Admin access required")
            return
        
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Title
        title_label = tk.Label(self.content_frame, text="Admin Panel", font=self.title_font, bg='#ecf0f1')
        title_label.pack(pady=20)
        
        # Statistics frame
        stats_frame = tk.LabelFrame(self.content_frame, text="System Statistics", font=self.heading_font, bg='white', padx=30, pady=20)
        stats_frame.pack(pady=20)
        
        conn = sqlite3.connect('expense_tracker.db')
        cursor = conn.cursor()
        
        # Get statistics
        cursor.execute('SELECT COUNT(*) FROM Users')
        total_users = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM Users WHERE is_admin = 1')
        admin_users = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM Expenses')
        total_expenses = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(amount) FROM Expenses')
        total_amount = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT COUNT(*) FROM Categories')
        total_categories = cursor.fetchone()[0]
        
        cursor.execute('''SELECT u.name, COUNT(e.expense_id) as count
                         FROM Users u
                         LEFT JOIN Expenses e ON u.user_id = e.user_id
                         GROUP BY u.user_id
                         ORDER BY count DESC
                         LIMIT 1''')
        top_user = cursor.fetchone()
        
        cursor.execute('''SELECT c.category_name, COUNT(e.expense_id) as count
                         FROM Categories c
                         LEFT JOIN Expenses e ON c.category_id = e.category_id
                         GROUP BY c.category_id
                         ORDER BY count DESC
                         LIMIT 1''')
        top_category = cursor.fetchone()
        
        conn.close()
        
        # Display statistics
        stats_text = f"""
        Total Users: {total_users}
        Admin Users: {admin_users}
        Total Transactions: {total_expenses}
        Total Amount: ₹{total_amount:.2f}
        Total Categories: {total_categories}
        Most Active User: {top_user[0] if top_user else 'N/A'} ({top_user[1] if top_user else 0} transactions)
        Most Used Category: {top_category[0] if top_category else 'N/A'} ({top_category[1] if top_category else 0} transactions)
        """
        
        tk.Label(stats_frame, text=stats_text, font=self.normal_font, bg='white', justify='left').pack()
        
        # Database operations
        db_frame = tk.LabelFrame(self.content_frame, text="Database Operations", font=self.heading_font, bg='white', padx=30, pady=20)
        db_frame.pack(pady=20)
        
        tk.Button(db_frame, text="Export All Data to CSV", command=self.export_data, bg='#2ecc71', fg='white',
                 font=self.normal_font, padx=20, pady=10).pack(pady=5)
        
        tk.Button(db_frame, text="Backup Database", command=self.backup_database, bg='#3498db', fg='white',
                 font=self.normal_font, padx=20, pady=10).pack(pady=5)
        
        tk.Button(db_frame, text="Clear All Expenses", command=self.clear_all_expenses, bg='#e74c3c', fg='white',
                 font=self.normal_font, padx=20, pady=10).pack(pady=5)
    
    def export_data(self):
        try:
            conn = sqlite3.connect('expense_tracker.db')
            
            # Export expenses
            expenses_df = pd.read_sql_query('''
                SELECT e.expense_id, u.name as user, c.category_name as category, 
                       e.date, e.amount, e.description
                FROM Expenses e
                JOIN Users u ON e.user_id = u.user_id
                JOIN Categories c ON e.category_id = c.category_id
            ''', conn)
            
            expenses_df.to_csv('expenses_export.csv', index=False)
            
            # Export users
            users_df = pd.read_sql_query('SELECT user_id, name, email, registration_date FROM Users', conn)
            users_df.to_csv('users_export.csv', index=False)
            
            conn.close()
            messagebox.showinfo("Success", "Data exported to expenses_export.csv and users_export.csv")
            
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def backup_database(self):
        try:
            import shutil
            from datetime import datetime
            
            backup_name = f'expense_tracker_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
            shutil.copy2('expense_tracker.db', backup_name)
            messagebox.showinfo("Success", f"Database backed up as {backup_name}")
            
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def clear_all_expenses(self):
        if messagebox.askyesno("Confirm", "Are you sure? This will delete ALL expenses from the system!"):
            if messagebox.askyesno("Double Confirm", "This action cannot be undone. Continue?"):
                conn = sqlite3.connect('expense_tracker.db')
                cursor = conn.cursor()
                cursor.execute('DELETE FROM Expenses')
                cursor.execute('DELETE FROM Reports')
                conn.commit()
                conn.close()
                messagebox.showinfo("Success", "All expenses cleared")
    
    def logout(self):
        self.current_user = None
        self.is_admin = False
        self.show_login_screen()


if __name__ == '__main__':
    root = tk.Tk()
    app = ExpenseTrackerApp(root)
    root.mainloop()