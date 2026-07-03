-- ============================================================
-- Reference queries used by the reports in app.py
-- (cleaned-up versions of the team's original presentation queries)
-- ============================================================

-- Members who have borrowed more than 1 book
SELECT Member_ID, COUNT(*) AS Borrowed_Books
FROM Borrow_Transaction
GROUP BY Member_ID
HAVING COUNT(*) > 1;

-- Overdue books (not yet returned, past due date)
SELECT
    m.Member_ID,
    m.Name AS Member_Name,
    bt.Transaction_ID,
    bt.Borrow_Date,
    bt.Due_Date
FROM Member m
JOIN Borrow_Transaction bt ON m.Member_ID = bt.Member_ID
WHERE bt.Returned = 0
  AND bt.Due_Date < date('now');

-- Members who currently have no borrowed books
SELECT m.Member_ID, m.Name
FROM Member m
LEFT JOIN Borrow_Transaction bt
    ON m.Member_ID = bt.Member_ID AND bt.Returned = 0
WHERE bt.Transaction_ID IS NULL;

-- Books reserved but never borrowed (pending reservations only)
SELECT b.Title, r.Reservation_Date
FROM Reservation r
JOIN Book b ON r.Book_ID = b.Book_ID
LEFT JOIN Book_Copy bc ON b.Book_ID = bc.Book_ID
LEFT JOIN Borrow_Transaction bt ON bc.Copy_ID = bt.Copy_ID
WHERE bt.Transaction_ID IS NULL
  AND r.Status = 'Pending';

-- Count of reservations per member
SELECT m.Name, COUNT(r.Reservation_ID) AS Total_Reservations
FROM Member m
LEFT JOIN Reservation r ON m.Member_ID = r.Member_ID
GROUP BY m.Member_ID, m.Name;

-- Books that have never been borrowed
SELECT b.Title
FROM Book b
JOIN Book_Copy bc ON b.Book_ID = bc.Book_ID
LEFT JOIN Borrow_Transaction bt ON bc.Copy_ID = bt.Copy_ID
WHERE bt.Transaction_ID IS NULL;

-- Members with overdue books, including borrow/due dates
SELECT m.Member_ID, m.Name, bt.Borrow_Date, bt.Due_Date
FROM Borrow_Transaction bt
JOIN Member m ON bt.Member_ID = m.Member_ID
LEFT JOIN Return_Transaction rt ON bt.Transaction_ID = rt.Transaction_ID
WHERE rt.Transaction_ID IS NULL
  AND bt.Due_Date < date('now')
ORDER BY bt.Due_Date ASC;

-- Every borrow, with the member who borrowed it, most recent first
SELECT m.Member_ID, m.Name, bt.Borrow_Date
FROM Borrow_Transaction bt
JOIN Member m ON bt.Member_ID = m.Member_ID
ORDER BY m.Name, bt.Borrow_Date;

-- Members and their returns
SELECT m.Member_ID, m.Name, rt.Return_ID, rt.Return_Date, rt.Transaction_ID
FROM Return_Transaction rt
JOIN Borrow_Transaction bt ON rt.Transaction_ID = bt.Transaction_ID
JOIN Member m ON bt.Member_ID = m.Member_ID
ORDER BY m.Name, rt.Return_ID;

-- Books borrowed and returned within 7 days
SELECT b.Title, bt.Borrow_Date, rt.Return_Date
FROM Borrow_Transaction bt
JOIN Return_Transaction rt ON bt.Transaction_ID = rt.Transaction_ID
JOIN Book_Copy bc ON bt.Copy_ID = bc.Copy_ID
JOIN Book b ON bc.Book_ID = b.Book_ID
WHERE julianday(rt.Return_Date) - julianday(bt.Borrow_Date) <= 7;

-- Average borrow duration per member (in days)
SELECT
    m.Member_ID,
    m.Name,
    AVG(julianday(rt.Return_Date) - julianday(bt.Borrow_Date)) AS Avg_Borrow_Duration_Days
FROM Member m
JOIN Borrow_Transaction bt ON m.Member_ID = bt.Member_ID
JOIN Return_Transaction rt ON bt.Transaction_ID = rt.Transaction_ID
GROUP BY m.Member_ID, m.Name;

-- Most borrowed books in the last 3 months
SELECT b.Title, COUNT(bt.Transaction_ID) AS Times_Borrowed
FROM Book b
JOIN Book_Copy bc ON b.Book_ID = bc.Book_ID
JOIN Borrow_Transaction bt ON bc.Copy_ID = bt.Copy_ID
WHERE bt.Borrow_Date >= date('now', '-3 months')
GROUP BY b.Book_ID, b.Title
ORDER BY Times_Borrowed DESC;

-- Top 5 most borrowed books of all time
SELECT b.Title, COUNT(bt.Transaction_ID) AS Times_Borrowed
FROM Book b
JOIN Book_Copy bc ON b.Book_ID = bc.Book_ID
JOIN Borrow_Transaction bt ON bc.Copy_ID = bt.Copy_ID
GROUP BY b.Book_ID, b.Title
ORDER BY Times_Borrowed DESC
LIMIT 5;
