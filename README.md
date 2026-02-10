# Expense-Tracker

A comprehensive, feature-rich desktop application for tracking personal expenses, built with Python's Tkinter library for the GUI and SQLite for database management. The application provides a user-friendly interface for managing expenses, categories, budgets, and generating insightful visual reports. It also includes a full-featured admin panel for user and system management.

Screenshots
(It is highly recommended to add screenshots of your application here to showcase its features. You can replace the placeholder links below with your actual images.)

Login Screen	Dashboard	View Expenses

Export to Sheets
Reports	Budget Management	Admin Panel

Export to Sheets
Features
Core Features for All Users
User Authentication: Secure user registration and login system with hashed passwords (SHA-256).

Dashboard Overview: A summary view with key statistics like total expenses, current month's spending, transaction count, and budget status.

Expense Management:

Add: Easily add new expenses with date, category, amount, and description.

View: Display all expenses in a clear, sortable table.

Edit: Modify the details of any existing expense.

Delete: Remove expenses from your records.

Search & Filter: Find specific expenses by date range and/or category.

Category Management:

Add, edit, and delete expense categories.

Prevents deletion of categories that are currently in use.

Budgeting:

Set a monthly budget limit.

View a budget overview to track spending against your budget.

Automatic color-coding and status updates (e.g., "Within Budget", "Over Budget").

Budget Alerts: Receive warnings when you are close to or have exceeded your monthly budget.

Visual Reports:

Generate graphical reports to visualize spending habits.

Monthly Report: Bar and line charts showing monthly totals and trends.

Yearly Report: Bar chart summarizing total expenses per year.

Category Report: Pie and bar charts showing the distribution of expenses across different categories.

Profile Management: Update your name and change your password securely.

Admin-Only Features
Admin Panel: A dedicated screen with system-wide statistics, including total users, total transactions, and most active user/category.

User Management:

View a list of all registered users and their total expenses.

Toggle Admin Status: Grant or revoke admin privileges for any user.

Delete User: Permanently delete a user and all their associated data (expenses, budgets, etc.).

Reset Password: Reset the password for any user.

Database Operations:

Export Data: Export all expenses and users data to CSV files (expenses_export.csv, users_export.csv).

Backup Database: Create a timestamped backup of the entire SQLite database file.

Clear All Expenses: A high-privilege option to wipe all expense records from the system (requires double confirmation).

Technologies Used
Language: Python 3

GUI: Tkinter (with ttk for modern widgets)

Database: SQLite3

Data Visualization: Matplotlib

Data Export: Pandas

Password Hashing: hashlib

Setup and Installation
Follow these steps to get the application running on your local machine.

1. Prerequisites:

Python 3.7 or higher

Pip (Python package installer)

2. Clone the Repository:

Bash

git clone https://github.com/your-username/tkinter-expense-tracker.git
cd tkinter-expense-tracker
3. Create a Virtual Environment (Recommended):

On Windows:

Bash

python -m venv venv
.\venv\Scripts\activate
On macOS/Linux:

Bash

python3 -m venv venv
source venv/bin/activate
4. Install Dependencies:
The project requires matplotlib and pandas. Install them using pip.

Bash

pip install matplotlib pandas
(Alternatively, you can create a requirements.txt file with the content below and run pip install -r requirements.txt)

# requirements.txt
matplotlib
pandas
5. Run the Application:

Bash

python et.py
The application will start, and a expense_tracker.db file will be automatically created in the project directory upon the first run.

How to Use
Launch the application using the command python et.py.

Register a new account or use the default admin credentials to log in:

Email: admin@expense.com

Password: admin123

Once logged in, use the sidebar to navigate between different sections:

Add your first expense via the "Add Expense" tab.

Set a budget for the current month in the "Budget" tab.

Explore your spending patterns in the "Reports" section.

If logged in as an admin, check out the "Manage Users" and "Admin Panel" sections for advanced controls.

Database Schema
The application uses an SQLite database with five main tables:

Users: Stores user information, credentials, and admin status.

Categories: Stores user-defined expense categories.

Expenses: The main table for logging all expense transactions.

Budgets: Stores monthly budget limits for each user.

Reports: (Note: This table is defined but not actively used in the provided code for generating dynamic reports. The reports are generated on-the-fly.)

SQL

CREATE TABLE IF NOT EXISTS Users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    is_admin INTEGER DEFAULT 0,
    registration_date DATE DEFAULT CURRENT_DATE
);

CREATE TABLE IF NOT EXISTS Categories (
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS Expenses (
    expense_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    date DATE NOT NULL,
    amount REAL NOT NULL,
    description TEXT,
    FOREIGN KEY (user_id) REFERENCES Users (user_id),
    FOREIGN KEY (category_id) REFERENCES Categories (category_id)
);

CREATE TABLE IF NOT EXISTS Budgets (
    budget_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    month TEXT NOT NULL,
    limit_amount REAL NOT NULL,
    FOREIGN KEY (user_id) REFERENCES Users (user_id),
    UNIQUE(user_id, month)
);
Future Improvements
[ ] Add support for recurring expenses.

[ ] Implement data import from CSV files.

[ ] Introduce multi-currency support.

[ ] Add a "dark mode" or theme selection.

[ ] More advanced report filtering (e.g., by description tags).

License
This project is licensed under the MIT License. See the LICENSE file for details.
