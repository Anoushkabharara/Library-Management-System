# Library Management System (LMS)

A full-stack Library Management System built with **Flask** and **SQLite**, based on a
team database design project. Tracks books, authors, publishers, members, borrowing,
returns, fines, and reservations — with a small web UI for day-to-day library operations
and a reports dashboard.

## Features

- **Book management** — add books (with author/publisher), track multiple physical copies per title, delete titles.
- **Member management** — register members, see who currently has active loans.
- **Borrow / return** — check out an available copy to a member with a due date; returning
  a book automatically calculates a late fine ($0.25/day overdue) and frees up the copy.
- **Reservations** — members can reserve a title; librarians can mark reservations completed or cancelled.
- **Reports**
  - Overdue books
  - Top 5 most borrowed books
  - Reservation status summary
  - Books never borrowed
  - Full member borrowing history

## Tech stack

- **Backend:** Python, Flask
- **Database:** SQLite (single-file, zero setup — swap in MySQL/Postgres later if needed)
- **Frontend:** Server-rendered Jinja2 templates, plain CSS (no build step)

## Database design

The schema (`schema.sql`) implements this entity structure:

```
Author ──┬── Book_Author ──┬── Book ── Publisher
         │                 │
         │                 └── Book_Copy
Member ──┼── Borrow_Transaction ── Return_Transaction
         │        │
         │        └── Book_Copy
         └── Reservation ── Book

Librarian ── Borrow_Transaction
```

Key design notes / fixes made vs. the original conceptual diagram:

- `Book_Copy.Status` and `Reservation.Status` use `CHECK` constraints instead of malformed
  `ENUM` syntax.
- `ON DELETE CASCADE` / `ON DELETE SET NULL` are applied consistently so removing a book or
  member cleans up related copies/transactions predictably.
- Fine calculation lives in the application layer (`app.py`) rather than a separate `Fine`
  table, computed at return time from days-overdue.

See `queries.sql` for the full set of reporting queries (overdue books, borrowing history,
most popular books, members with no active loans, etc).

## Getting started

```bash
git clone https://github.com/<your-username>/library-management-system.git
cd library-management-system

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
python app.py
```

Then open **http://127.0.0.1:5000** in your browser.

The first run automatically creates `library.db` from `schema.sql` and seeds it with a
handful of sample books/members/loans from `sample_data.sql` (delete `library.db` and
restart to reset).

## Project structure

```
library-management-system/
├── app.py              # Flask app + all routes
├── schema.sql           # Database schema
├── sample_data.sql      # Seed data
├── queries.sql          # Standalone reference queries used by the reports
├── requirements.txt
├── templates/            # Jinja2 HTML templates
│   ├── base.html
│   ├── dashboard.html
│   ├── books.html
│   ├── members.html
│   ├── borrow.html
│   ├── reservations.html
│   └── reports.html
└── static/
    └── style.css
```

## Team

Originally designed as a group database project by Ashna Murali, Amrutha Veeraswamy,
Siya Deole, Yosra Nseirat, Hania Aslam, and Anoushka Bharara.

## License

MIT — feel free to fork and extend.
