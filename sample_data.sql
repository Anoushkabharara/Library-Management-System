-- ============================================================
-- Sample Data - mirrors the examples used in the presentation
-- ============================================================

INSERT INTO Author (Author_ID, Name, Biography) VALUES
    (1, 'J.K. Rowling', 'British author'),
    (2, 'George Orwell', 'English novelist');

INSERT INTO Publisher (Publisher_ID, Name, Address, Contact) VALUES
    (1, 'Bloomsbury', 'London, UK', '123-456-7890'),
    (2, 'Secker & Warburg', 'London, UK', '987-654-3210');

INSERT INTO Book (Book_ID, Title, ISBN, Publisher_ID, Year_Published) VALUES
    (101, 'Harry Potter and the Philosopher''s Stone', '9780747532699', 1, 1997),
    (102, '1984', '9780451524935', 2, 1949);

INSERT INTO Book_Author (Book_ID, Author_ID) VALUES
    (101, 1),
    (102, 2);

INSERT INTO Book_Copy (Copy_ID, Book_ID, Status, Shelf_Location) VALUES
    (201, 101, 'Available', 'A1'),
    (202, 101, 'Borrowed', 'A2'),
    (203, 102, 'Available', 'B1');

INSERT INTO Member (Member_ID, Name, Email, Phone, Registration_Date) VALUES
    (1, 'Alice Smith', 'alice@example.com', '555-1234', '2024-10-01'),
    (2, 'Bob Johnson', 'bob@example.com', '555-5678', '2025-01-10');

INSERT INTO Librarian (Librarian_ID, Name, Email, Password) VALUES
    (1, 'Emma Brown', 'emma@library.com', 'securepass');

INSERT INTO Borrow_Transaction (Transaction_ID, Member_ID, Copy_ID, Librarian_ID, Borrow_Date, Due_Date, Returned) VALUES
    (1001, 1, 202, 1, '2025-03-20', '2025-04-03', 0);

INSERT INTO Reservation (Reservation_ID, Member_ID, Book_ID, Reservation_Date, Status) VALUES
    (301, 2, 101, '2025-03-30', 'Pending');
