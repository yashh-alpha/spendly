import sqlite3
import random
from datetime import datetime, timedelta
from database.db import DATABASE

def seed_expenses(user_id, count, months):
    conn = sqlite3.connect(DATABASE)
    conn.execute("PRAGMA foreign_keys = ON")

    # Categories with weight for rough proportionality
    # Food: 30%, Transport: 20%, Bills: 15%, Health: 5%, Ent: 10%, Shopping: 15%, Other: 5%
    categories = [
        ("Food", 50, 800, "Paneer Tikka", "Vegetable Samosa", "Masala Chai", "Veg Thali"),
        ("Transport", 20, 500, "Uber ride", "Auto-rickshaw", "Metro ticket", "Petrol refill"),
        ("Bills", 200, 3000, "Electricity bill", "Broadband payment", "Water utility", "Gas connection"),
        ("Health", 100, 2000, "Medicine refill", "Doctor consultation", "Lab tests", "Ayurvedic tonic"),
        ("Entertainment", 100, 1500, "Netflix sub", "Book purchase", "Gaming arcade", "Concert ticket"),
        ("Shopping", 200, 5000, "Clothing store", "Footwear shop", "Grocery store", "Home decor"),
        ("Other", 50, 1000, "Donation", "Gift for friend", "Repair service", "Stationery")
    ]

    weights = [0.30, 0.20, 0.15, 0.05, 0.10, 0.15, 0.05]

    expenses = []
    end_date = datetime.now()
    start_date = end_date - timedelta(days=months * 30)

    for _ in range(count):
        # Pick category
        cat_data = random.choices(categories, weights=weights, k=1)[0]
        category = cat_data[0]
        amount = random.uniform(cat_data[1], cat_data[2])
        description = random.choice(cat_data[3:])

        # Random date within range
        random_days = random.randint(0, months * 30)
        date = (start_date + timedelta(days=random_days)).strftime("%Y-%m-%d")

        expenses.append((user_id, amount, category, date, description))

    try:
        with conn:
            conn.executemany("""
                INSERT INTO expenses (user_id, amount, category, date, description)
                VALUES (?, ?, ?, ?, ?)
            """, expenses)
        print(f"Successfully inserted {count} expenses.")
        print(f"Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    except Exception as e:
        print(f"Error inserting expenses: {e}")
        # Transaction rolls back automatically due to context manager
    finally:
        conn.close()

if __name__ == "__main__":
    seed_expenses(2, 5, 3)
