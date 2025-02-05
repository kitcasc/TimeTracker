# Time_Tracker
Add tasks to your calendar and it calculates your available windows for the next 2 weeks.

I use this to schedule meetings when I want to show people my available windows in a formatted way:P

The code assumes the earliest time available to be 9:00 a.m., and the latest time to be 10:00 p.m.

They can be adjusted from:

    def __init__(self, wake_time=time(9, 0), sleep_time=time(22, 0)):
    
This line is located at the beginning.
