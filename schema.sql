-- ============================================================
-- Library Management System (LMS) - Database Schema
-- Based on the team's conceptual ER diagram design
-- SQLite dialect (portable, no server setup required)
-- ============================================================

PRAGMA foreign_keys = ON;

-- ---------- Reference tables ----------

CREATE TABLE IF NOT EXISTS Publisher (
    Publisher_ID INTEGER PRIMARY KEY,
    Name         VARCHAR(100) NOT NULL,
    Address      VARCHAR(255),
    Contact      VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS Author (
    Author_ID INTEGER PRIMARY KEY,
    Name      VARCHAR(100) NOT NULL,
    Biography TEXT
);

CREATE TABLE IF NOT EXISTS Librarian (
    Librarian_ID INTEGER PRIMARY KEY,
    Name         VARCHAR(100) NOT NULL,
    Email        VARCHAR(100) UNIQUE NOT NULL,
    Password     VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS Member (
    Member_ID        INTEGER PRIMARY KEY,
    Name             VARCHAR(100) NOT NULL,
    Email            VARCHAR(100) UNIQUE NOT NULL,
    Phone            VARCHAR(20),
    Registration_Date DATE NOT NULL DEFAULT CURRENT_DATE
);

-- ---------- Book catalog ----------

CREATE TABLE IF NOT EXISTS Book (
    Book_ID       INTEGER PRIMARY KEY,
    Title         VARCHAR(255) NOT NULL,
    ISBN          VARCHAR(20) UNIQUE,
    Publisher_ID  INTEGER,
    Year_Published INTEGER,
    FOREIGN KEY (Publisher_ID) REFERENCES Publisher(Publisher_ID) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS Book_Author (
    Book_ID   INTEGER NOT NULL,
    Author_ID INTEGER NOT NULL,
    PRIMARY KEY (Book_ID, Author_ID),
    FOREIGN KEY (Book_ID) REFERENCES Book(Book_ID) ON DELETE CASCADE,
    FOREIGN KEY (Author_ID) REFERENCES Author(Author_ID) ON DELETE CASCADE
);

-- Individual physical/lendable copies of a book
CREATE TABLE IF NOT EXISTS Book_Copy (
    Copy_ID       INTEGER PRIMARY KEY,
    Book_ID       INTEGER NOT NULL,
    Status        VARCHAR(20) NOT NULL DEFAULT 'Available'
                  CHECK (Status IN ('Available', 'Borrowed', 'Lost')),
    Shelf_Location VARCHAR(50),
    FOREIGN KEY (Book_ID) REFERENCES Book(Book_ID) ON DELETE CASCADE
);

-- ---------- Transactions ----------

CREATE TABLE IF NOT EXISTS Borrow_Transaction (
    Transaction_ID INTEGER PRIMARY KEY,
    Member_ID      INTEGER NOT NULL,
    Copy_ID        INTEGER NOT NULL,
    Librarian_ID   INTEGER,
    Borrow_Date    DATE NOT NULL DEFAULT CURRENT_DATE,
    Due_Date       DATE NOT NULL,
    Returned       BOOLEAN NOT NULL DEFAULT 0,
    FOREIGN KEY (Member_ID) REFERENCES Member(Member_ID) ON DELETE CASCADE,
    FOREIGN KEY (Copy_ID) REFERENCES Book_Copy(Copy_ID) ON DELETE CASCADE,
    FOREIGN KEY (Librarian_ID) REFERENCES Librarian(Librarian_ID) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS Return_Transaction (
    Return_ID      INTEGER PRIMARY KEY,
    Transaction_ID INTEGER UNIQUE NOT NULL,
    Return_Date    DATE NOT NULL DEFAULT CURRENT_DATE,
    Fine_Amount    DECIMAL(6,2) NOT NULL DEFAULT 0.00,
    FOREIGN KEY (Transaction_ID) REFERENCES Borrow_Transaction(Transaction_ID) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Reservation (
    Reservation_ID   INTEGER PRIMARY KEY,
    Member_ID        INTEGER NOT NULL,
    Book_ID          INTEGER NOT NULL,
    Reservation_Date DATE NOT NULL DEFAULT CURRENT_DATE,
    Status           VARCHAR(20) NOT NULL DEFAULT 'Pending'
                     CHECK (Status IN ('Pending', 'Completed', 'Cancelled')),
    FOREIGN KEY (Member_ID) REFERENCES Member(Member_ID) ON DELETE CASCADE,
    FOREIGN KEY (Book_ID) REFERENCES Book(Book_ID) ON DELETE CASCADE
);

-- Helpful indexes for common lookups/reports
CREATE INDEX IF NOT EXISTS idx_borrow_member ON Borrow_Transaction(Member_ID);
CREATE INDEX IF NOT EXISTS idx_borrow_copy ON Borrow_Transaction(Copy_ID);
CREATE INDEX IF NOT EXISTS idx_reservation_member ON Reservation(Member_ID);
CREATE INDEX IF NOT EXISTS idx_reservation_book ON Reservation(Book_ID);
CREATE INDEX IF NOT EXISTS idx_copy_book ON Book_Copy(Book_ID);
