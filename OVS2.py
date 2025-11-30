import mysql.connector
import tkinter as tk
from tkinter import messagebox, ttk

# Database Connection
def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",  # Change as needed
        password="",  # Change as needed
        database="lju"
    )

# GUI Application Class
class VotingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Online Voting System")
        self.root.geometry("500x500")
        self.root.configure(bg="#f0f0f0")
        self.create_main_menu()

    def create_main_menu(self):
        self.clear_window()
        tk.Label(self.root, text="Online Voting System", font=("Arial", 18, "bold"), bg="#f0f0f0").pack(pady=20)
        frame = tk.Frame(self.root, bg="#f0f0f0")
        frame.pack()
        
        buttons = [
            ("Register", self.register_user),
            ("Login", self.login_user),
            ("Vote", self.cast_vote),
            ("Logout", self.logout_user),
            ("View Results (Admin)", self.view_results),
            ("Exit", self.root.quit)
        ]
        
        for text, command in buttons:
            ttk.Button(frame, text=text, command=command, width=25).pack(pady=5)

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def register_user(self):
        self.create_form("Register", self.submit_registration)
    
    def login_user(self):
        self.create_form("Login", self.submit_login, fields=["Mobile No", "Password"])
    
    def logout_user(self):
        self.create_form("Logout", self.submit_logout, fields=["Mobile No"])
    
    def cast_vote(self):
        """ First prompt for Mobile No and Aadhaar No """
        self.create_form("Vote Verification", self.verify_voter, fields=["Mobile No", "Aadhaar No"])

    def verify_voter(self, entries):
        """ Verify Mobile No and Aadhaar No before allowing voting """
        mobile_no = entries["Mobile No"].get().strip()
        aadhaar_no = entries["Aadhaar No"].get().strip()

        if not mobile_no or not aadhaar_no:
            messagebox.showerror("Error", "Both fields are required!")
            return
        
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT toWhomHasVoted FROM OVS WHERE mobileno = %s AND aadhaar = %s", 
                       (mobile_no, aadhaar_no))
        user = cursor.fetchone()
        conn.close()
        
        if user is None:
            messagebox.showerror("Error", "Invalid Mobile No or Aadhaar No!")
        elif user[0] is not None:
            messagebox.showerror("Error", "You have already voted!")
            self.create_main_menu()
        else:
            # Proceed to vote
            self.create_form("Cast Your Vote", lambda vote_entries: self.submit_vote(vote_entries, mobile_no), fields=["Candidate Name"])

    def submit_vote(self, entries, mobile_no):
        """ Record the vote in the database """
        candidate_name = entries["Candidate Name"].get().strip()

        if not candidate_name:
            messagebox.showerror("Error", "Candidate Name is required!")
            return

        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE OVS SET toWhomHasVoted = %s WHERE mobileno = %s", 
                       (candidate_name, mobile_no))
        conn.commit()
        conn.close()
        
        messagebox.showinfo("Success", "Vote cast successfully!")
        self.create_main_menu()

    def view_results(self):
        """ Ask for admin credentials before displaying results """
        self.create_form("Admin Login", self.verify_admin, fields=["Username", "Password"])

    def verify_admin(self, entries):
        """ Check if the entered credentials match the admin login details """
        username = entries["Username"].get().strip()
        password = entries["Password"].get().strip()

        if username == "Admin" and password == "admin123":
            self.show_results()
        else:
            messagebox.showerror("Access Denied", "Invalid Admin Credentials!")

    def show_results(self):
        """ Fetch and display election results """
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT toWhomHasVoted, COUNT(*) FROM OVS WHERE toWhomHasVoted IS NOT NULL GROUP BY toWhomHasVoted")
        results = cursor.fetchall()
        conn.close()
        
        if results:
            result_text = "Election Results:\n" + "\n".join([f"{candidate}: {votes} votes" for candidate, votes in results])
        else:
            result_text = "No votes have been cast yet."

        messagebox.showinfo("Results", result_text)
        self.create_main_menu()

    def create_form(self, title, submit_action, fields=["Name", "Age", "Mobile No", "Aadhaar No", "Password"]):
        self.clear_window()
        tk.Label(self.root, text=title, font=("Arial", 18, "bold"), bg="#f0f0f0").pack(pady=10)
        
        frame = tk.Frame(self.root, bg="#f0f0f0")
        frame.pack(pady=10)
        
        entries = {}
        for i, field in enumerate(fields):
            tk.Label(frame, text=f"{field}:").grid(row=i, column=0, padx=5, pady=5, sticky="e")
            entry = tk.Entry(frame, show='*' if "Password" in field else None)
            entry.grid(row=i, column=1, padx=5, pady=5)
            entries[field] = entry
        
        tk.Button(frame, text="Submit", command=lambda: submit_action(entries), bg="#4CAF50", fg="white").grid(row=len(fields), columnspan=2, pady=10)

    def submit_registration(self, entries):
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO OVS (username, age, mobileno, aadhaar, password, isRegistered, isLogin, toWhomHasVoted) VALUES (%s, %s, %s, %s, %s, 1, 0, NULL)",
                       (entries["Name"].get(), entries["Age"].get(), entries["Mobile No"].get(), entries["Aadhaar No"].get(), entries["Password"].get()))
        conn.commit()
        conn.close()
        messagebox.showinfo("Success", "Registration successful!")
        self.create_main_menu()
    
    def submit_login(self, entries):
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM OVS WHERE mobileno = %s", (entries["Mobile No"].get(),))
        user = cursor.fetchone()
        conn.close()
        
        if user and user[0] == entries["Password"].get():
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("UPDATE OVS SET isLogin = 1 WHERE mobileno = %s", (entries["Mobile No"].get(),))
            conn.commit()
            conn.close()
            messagebox.showinfo("Success", "Login successful!")
            self.create_main_menu()
        else:
            messagebox.showerror("Error", "Invalid credentials!")

    def submit_logout(self, entries):
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE OVS SET isLogin = 0 WHERE mobileno = %s", (entries["Mobile No"].get(),))
        conn.commit()
        conn.close()
        messagebox.showinfo("Success", "Logged out successfully!")
        self.create_main_menu()

# Run Application
if __name__ == "__main__":
    root = tk.Tk()
    app = VotingApp(root)
    root.mainloop()
