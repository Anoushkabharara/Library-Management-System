"""
Library Management System - Flask Web Application
Built on top of the SQLite schema in schema.sql

Run with:
    pip install -r requirements.txt
    python app.py
Then visit http://127.0.0.1:5000
"""

import os
import sqlite3
from datetime import date, datetime, timedelta

from flask import Flask, render_template, request, redirect, url_for, flash, g

DB_PATH = os.path.join(os.path.dirname(__file__), "library.db")
DEFAULT_LOAN_DAYS = 14

app = Flask(__name__)
app.secret_key = "dev-secret-key-change-me"


# ---------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Create the database from schema.sql + sample_data.sql if it doesn't exist yet."""
    fresh = not os.path.exists(DB_PATH)
    db = sqlite3.connect(DB_PATH)
    db.execute("PRAGMA foreign_keys = ON")
    with open(os.path.join(os.path.dirname(__file__), "schema.sql")) as f:
        db.executescript(f.read())
    if fresh:
        sample_path = os.path.join(os.path.dirname(__file__), "sample_data.sql")
        if os.path.exists(sample_path):
            with open(sample_path) as f:
                db.executescript(f.read())
    db.commit()
    db.close()


# ---------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------

@app.route("/")
def dashboard():
    db = get_db()
    stats = {
        "total_books": db.execute("SELECT COUNT(*) c FROM Book").fetchone()["c"],
        "total_copies": db.execute("SELECT COUNT(*) c FROM Book_Copy").fetchone()["c"],
        "available_copies": db.execute(
            "SELECT COUNT(*) c FROM Book_Copy WHERE Status = 'Available'"
        ).fetchone()["c"],
        "total_members": db.execute("SELECT COUNT(*) c FROM Member").fetchone()["c"],
        "active_borrows": db.execute(
            "SELECT COUNT(*) c FROM Borrow_Transaction WHERE Returned = 0"
        ).fetchone()["c"],
        "overdue": db.execute(
            "SELECT COUNT(*) c FROM Borrow_Transaction "
            "WHERE Returned = 0 AND Due_Date < date('now')"
        ).fetchone()["c"],
        "pending_reservations": db.execute(
            "SELECT COUNT(*) c FROM Reservation WHERE Status = 'Pending'"
        ).fetchone()["c"],
    }
    return render_template("dashboard.html", stats=stats)


# ---------------------------------------------------------------
# Book management
# ---------------------------------------------------------------

@app.route("/books", methods=["GET", "POST"])
def books():
    db = get_db()
    if request.method == "POST":
        title = request.form["title"].strip()
        isbn = request.form.get("isbn", "").strip() or None
        author_name = request.form.get("author_name", "").strip()
        publisher_name = request.form.get("publisher_name", "").strip()
        year = request.form.get("year_published") or None
        copies = int(request.form.get("copies") or 1)
        shelf = request.form.get("shelf_location", "").strip() or "TBD"

        publisher_id = None
        if publisher_name:
            row = db.execute(
                "SELECT Publisher_ID FROM Publisher WHERE Name = ?", (publisher_name,)
            ).fetchone()
            if row:
                publisher_id = row["Publisher_ID"]
            else:
                cur = db.execute(
                    "INSERT INTO Publisher (Name) VALUES (?)", (publisher_name,)
                )
                publisher_id = cur.lastrowid

        cur = db.execute(
            "INSERT INTO Book (Title, ISBN, Publisher_ID, Year_Published) VALUES (?, ?, ?, ?)",
            (title, isbn, publisher_id, year),
        )
        book_id = cur.lastrowid

        if author_name:
            row = db.execute(
                "SELECT Author_ID FROM Author WHERE Name = ?", (author_name,)
            ).fetchone()
            if row:
                author_id = row["Author_ID"]
            else:
                cur2 = db.execute(
                    "INSERT INTO Author (Name) VALUES (?)", (author_name,)
                )
                author_id = cur2.lastrowid
            db.execute(
                "INSERT INTO Book_Author (Book_ID, Author_ID) VALUES (?, ?)",
                (book_id, author_id),
            )

        for _ in range(max(copies, 1)):
            db.execute(
                "INSERT INTO Book_Copy (Book_ID, Status, Shelf_Location) VALUES (?, 'Available', ?)",
                (book_id, shelf),
            )

        db.commit()
        flash(f'Added "{title}" with {copies} cop{"y" if copies == 1 else "ies"}.', "success")
        return redirect(url_for("books"))

    rows = db.execute(
        """
        SELECT b.Book_ID, b.Title, b.ISBN, b.Year_Published,
               p.Name AS Publisher_Name,
               GROUP_CONCAT(DISTINCT a.Name) AS Authors,
               COUNT(bc.Copy_ID) AS Total_Copies,
               SUM(CASE WHEN bc.Status = 'Available' THEN 1 ELSE 0 END) AS Available_Copies
        FROM Book b
        LEFT JOIN Publisher p ON b.Publisher_ID = p.Publisher_ID
        LEFT JOIN Book_Author ba ON b.Book_ID = ba.Book_ID
        LEFT JOIN Author a ON ba.Author_ID = a.Author_ID
        LEFT JOIN Book_Copy bc ON b.Book_ID = bc.Book_ID
        GROUP BY b.Book_ID
        ORDER BY b.Title
        """
    ).fetchall()
    return render_template("books.html", books=rows)


@app.route("/books/<int:book_id>/delete", methods=["POST"])
def delete_book(book_id):
    db = get_db()
    db.execute("DELETE FROM Book WHERE Book_ID = ?", (book_id,))
    db.commit()
    flash("Book removed.", "success")
    return redirect(url_for("books"))


# ---------------------------------------------------------------
# Member management
# ---------------------------------------------------------------

@app.route("/members", methods=["GET", "POST"])
def members():
    db = get_db()
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip()
        phone = request.form.get("phone", "").strip() or None
        try:
            db.execute(
                "INSERT INTO Member (Name, Email, Phone, Registration_Date) VALUES (?, ?, ?, ?)",
                (name, email, phone, date.today().isoformat()),
            )
            db.commit()
            flash(f'Added member "{name}".', "success")
        except sqlite3.IntegrityError:
            flash("That email is already registered to another member.", "error")
        return redirect(url_for("members"))

    rows = db.execute(
        """
        SELECT m.Member_ID, m.Name, m.Email, m.Phone, m.Registration_Date,
               SUM(CASE WHEN bt.Returned = 0 THEN 1 ELSE 0 END) AS Active_Borrows
        FROM Member m
        LEFT JOIN Borrow_Transaction bt ON m.Member_ID = bt.Member_ID
        GROUP BY m.Member_ID
        ORDER BY m.Name
        """
    ).fetchall()
    return render_template("members.html", members=rows)


@app.route("/members/<int:member_id>/delete", methods=["POST"])
def delete_member(member_id):
    db = get_db()
    db.execute("DELETE FROM Member WHERE Member_ID = ?", (member_id,))
    db.commit()
    flash("Member removed.", "success")
    return redirect(url_for("members"))


# ---------------------------------------------------------------
# Borrow / Return
# ---------------------------------------------------------------

@app.route("/borrow", methods=["GET", "POST"])
def borrow():
    db = get_db()
    if request.method == "POST":
        member_id = request.form["member_id"]
        copy_id = request.form["copy_id"]
        loan_days = int(request.form.get("loan_days") or DEFAULT_LOAN_DAYS)
        due_date = (date.today() + timedelta(days=loan_days)).isoformat()

        db.execute(
            "INSERT INTO Borrow_Transaction (Member_ID, Copy_ID, Borrow_Date, Due_Date, Returned) "
            "VALUES (?, ?, ?, ?, 0)",
            (member_id, copy_id, date.today().isoformat(), due_date),
        )
        db.execute(
            "UPDATE Book_Copy SET Status = 'Borrowed' WHERE Copy_ID = ?", (copy_id,)
        )
        db.commit()
        flash("Book checked out.", "success")
        return redirect(url_for("borrow"))

    available_copies = db.execute(
        """
        SELECT bc.Copy_ID, b.Title, bc.Shelf_Location
        FROM Book_Copy bc
        JOIN Book b ON bc.Book_ID = b.Book_ID
        WHERE bc.Status = 'Available'
        ORDER BY b.Title
        """
    ).fetchall()
    members_list = db.execute("SELECT Member_ID, Name FROM Member ORDER BY Name").fetchall()
    active_loans = db.execute(
        """
        SELECT bt.Transaction_ID, m.Name AS Member_Name, b.Title, bt.Borrow_Date, bt.Due_Date,
               CASE WHEN bt.Due_Date < date('now') THEN 1 ELSE 0 END AS Is_Overdue
        FROM Borrow_Transaction bt
        JOIN Member m ON bt.Member_ID = m.Member_ID
        JOIN Book_Copy bc ON bt.Copy_ID = bc.Copy_ID
        JOIN Book b ON bc.Book_ID = b.Book_ID
        WHERE bt.Returned = 0
        ORDER BY bt.Due_Date
        """
    ).fetchall()
    return render_template(
        "borrow.html",
        available_copies=available_copies,
        members=members_list,
        active_loans=active_loans,
    )


@app.route("/return/<int:transaction_id>", methods=["POST"])
def return_book(transaction_id):
    db = get_db()
    txn = db.execute(
        "SELECT * FROM Borrow_Transaction WHERE Transaction_ID = ?", (transaction_id,)
    ).fetchone()
    if txn is None:
        flash("Transaction not found.", "error")
        return redirect(url_for("borrow"))

    today = date.today()
    due = datetime.strptime(txn["Due_Date"], "%Y-%m-%d").date()
    days_late = max((today - due).days, 0)
    fine = round(days_late * 0.25, 2)  # $0.25/day late fee

    db.execute(
        "INSERT INTO Return_Transaction (Transaction_ID, Return_Date, Fine_Amount) VALUES (?, ?, ?)",
        (transaction_id, today.isoformat(), fine),
    )
    db.execute(
        "UPDATE Borrow_Transaction SET Returned = 1 WHERE Transaction_ID = ?",
        (transaction_id,),
    )
    db.execute(
        "UPDATE Book_Copy SET Status = 'Available' WHERE Copy_ID = ?", (txn["Copy_ID"],)
    )
    db.commit()

    if fine > 0:
        flash(f"Book returned. Late fine: ${fine:.2f} ({days_late} day(s) late).", "success")
    else:
        flash("Book returned on time. No fine.", "success")
    return redirect(url_for("borrow"))


# ---------------------------------------------------------------
# Reservations
# ---------------------------------------------------------------

@app.route("/reservations", methods=["GET", "POST"])
def reservations():
    db = get_db()
    if request.method == "POST":
        member_id = request.form["member_id"]
        book_id = request.form["book_id"]
        db.execute(
            "INSERT INTO Reservation (Member_ID, Book_ID, Reservation_Date, Status) "
            "VALUES (?, ?, ?, 'Pending')",
            (member_id, book_id, date.today().isoformat()),
        )
        db.commit()
        flash("Reservation created.", "success")
        return redirect(url_for("reservations"))

    rows = db.execute(
        """
        SELECT r.Reservation_ID, m.Name AS Member_Name, b.Title, r.Reservation_Date, r.Status
        FROM Reservation r
        JOIN Member m ON r.Member_ID = m.Member_ID
        JOIN Book b ON r.Book_ID = b.Book_ID
        ORDER BY r.Reservation_Date DESC
        """
    ).fetchall()
    members_list = db.execute("SELECT Member_ID, Name FROM Member ORDER BY Name").fetchall()
    books_list = db.execute("SELECT Book_ID, Title FROM Book ORDER BY Title").fetchall()
    return render_template(
        "reservations.html", reservations=rows, members=members_list, books=books_list
    )


@app.route("/reservations/<int:reservation_id>/<status>", methods=["POST"])
def update_reservation(reservation_id, status):
    if status not in ("Completed", "Cancelled"):
        flash("Invalid status.", "error")
        return redirect(url_for("reservations"))
    db = get_db()
    db.execute(
        "UPDATE Reservation SET Status = ? WHERE Reservation_ID = ?",
        (status, reservation_id),
    )
    db.commit()
    flash(f"Reservation marked {status.lower()}.", "success")
    return redirect(url_for("reservations"))


# ---------------------------------------------------------------
# Reports
# ---------------------------------------------------------------

@app.route("/reports")
def reports():
    db = get_db()

    overdue_books = db.execute(
        """
        SELECT m.Name AS Member_Name, b.Title, bt.Borrow_Date, bt.Due_Date,
               CAST(julianday('now') - julianday(bt.Due_Date) AS INTEGER) AS Days_Overdue
        FROM Borrow_Transaction bt
        JOIN Member m ON bt.Member_ID = m.Member_ID
        JOIN Book_Copy bc ON bt.Copy_ID = bc.Copy_ID
        JOIN Book b ON bc.Book_ID = b.Book_ID
        WHERE bt.Returned = 0 AND bt.Due_Date < date('now')
        ORDER BY Days_Overdue DESC
        """
    ).fetchall()

    borrowing_history = db.execute(
        """
        SELECT m.Name AS Member_Name, b.Title, bt.Borrow_Date, bt.Due_Date,
               CASE WHEN bt.Returned = 1 THEN 'Returned' ELSE 'Active' END AS Status
        FROM Borrow_Transaction bt
        JOIN Member m ON bt.Member_ID = m.Member_ID
        JOIN Book_Copy bc ON bt.Copy_ID = bc.Copy_ID
        JOIN Book b ON bc.Book_ID = b.Book_ID
        ORDER BY bt.Borrow_Date DESC
        """
    ).fetchall()

    popular_books = db.execute(
        """
        SELECT b.Title, COUNT(bt.Transaction_ID) AS Times_Borrowed
        FROM Book b
        JOIN Book_Copy bc ON b.Book_ID = bc.Book_ID
        JOIN Borrow_Transaction bt ON bc.Copy_ID = bt.Copy_ID
        GROUP BY b.Book_ID, b.Title
        ORDER BY Times_Borrowed DESC
        LIMIT 5
        """
    ).fetchall()

    reservation_status = db.execute(
        """
        SELECT r.Status, COUNT(*) AS Count
        FROM Reservation r
        GROUP BY r.Status
        """
    ).fetchall()

    never_borrowed = db.execute(
        """
        SELECT b.Title
        FROM Book b
        JOIN Book_Copy bc ON b.Book_ID = bc.Book_ID
        LEFT JOIN Borrow_Transaction bt ON bc.Copy_ID = bt.Copy_ID
        WHERE bt.Transaction_ID IS NULL
        """
    ).fetchall()

    return render_template(
        "reports.html",
        overdue_books=overdue_books,
        borrowing_history=borrowing_history,
        popular_books=popular_books,
        reservation_status=reservation_status,
        never_borrowed=never_borrowed,
    )


# ---------------------------------------------------------------

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
