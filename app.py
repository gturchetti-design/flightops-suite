"""
FlightOps Suite — entry point
Delegates entirely to dashboard.py so `python app.py` serves the new layout.
"""
from dashboard import app

if __name__ == "__main__":
    import os
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8050)), debug=False)
