CREATE TABLE IF NOT EXISTS members (
    UserID int PRIMARY KEY,
    UserName varchar(225),
    Guild varchar(225),
    UserRole varchar(225),
    MemberSince varchar(225),
    MemberLeft varchar(225)
);