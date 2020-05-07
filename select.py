from cs50 import SQL

db = SQL("sqlite:///finance.db")

def main():
    quote = db.execute("SELECT sum(noshares), symbol FROM transactions WHERE id = :username GROUP BY symbol"
    , username=10)
    symbol = db.execute("SELECT symbol FROM transactions WHERE id = :username GROUP BY symbol"
    , username=10)
    i = 0
    for i in range(len(quote)):
       print(f"{quote[i].get('symbol')}")
       print(f"{quote[i].get('sum(noshares)')}")
       i=i+1


"""
def get symbol
    try:
        quote = response.json()
        return {
            "name": quote["companyName"],
            "price": float(quote["latestPrice"]),
            "symbol": quote["symbol"]
        }
"""
if __name__ == "__main__":
    main()
