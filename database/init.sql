-- Clean slate
DROP TABLE IF EXISTS events;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS users;

-- 1. Products Catalog (From Instacart)
CREATE TABLE products (
    product_id INT PRIMARY KEY,
    product_name VARCHAR(255),
    aisle_id INT,
    department_id INT
);

-- 2. Users (Synthetic Profiles)
CREATE TABLE users (
    user_id INT PRIMARY KEY,
    age INT,
    gender VARCHAR(10),
    persona VARCHAR(50) -- e.g., "Health Nut", "Budget Shopper"
);

-- 3. Clickstream Events (The "Gold" Data)
CREATE TABLE events (
    event_id VARCHAR(50) PRIMARY KEY,
    user_id INT REFERENCES users(user_id),
    session_id VARCHAR(50),
    product_id INT REFERENCES products(product_id),
    event_type VARCHAR(20), -- 'view', 'cart', 'purchase'
    event_time TIMESTAMP,
    device VARCHAR(20)
);

-- Index for fast querying later
CREATE INDEX idx_events_user ON events(user_id);
CREATE INDEX idx_events_time ON events(event_time);
CREATE TABLE IF NOT EXISTS products (
    product_id INT PRIMARY KEY,
    product_name VARCHAR(255),
    aisle_id INT,
    department_id INT
);

CREATE TABLE IF NOT EXISTS users (
    user_id INT PRIMARY KEY,
    age INT,
    gender VARCHAR(10),
    persona VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS events (
    event_id VARCHAR(50) PRIMARY KEY,
    user_id INT,
    session_id VARCHAR(50),
    product_id INT,
    event_type VARCHAR(20),
    event_time TIMESTAMP,
    device VARCHAR(20)
);
