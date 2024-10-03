import schedule
import time
from traindriver import retrieveDepartures

# important Stations
#DONA    ---> 8000078
#Pasing  ---> 8004158
#Munchen ---> 8000261

# Define a function to print a message


def print_message():
    print("Hello! It's time to code on GFG")


# Schedule the task to run every day at 7:00 AM
schedule.every().day.at("06:20").do(retrieveDepartures(8004158,"7am"))
schedule.every().day.at("16:20").do(retrieveDepartures(8000078,"5pm"))

while True:
    schedule.run_pending()
    time.sleep(10)
    