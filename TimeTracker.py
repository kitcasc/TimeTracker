from datetime import datetime, timedelta, time
import calendar
from tabulate import tabulate
import json
import os
import sys

class PersonalScheduler:
    def __init__(self, wake_time=time(9, 0), sleep_time=time(22, 0)):
        self.wake_time = wake_time
        self.sleep_time = sleep_time
        self.personal_calendar = {}
        self.busy_slots = []
        
        # 判断当前是打包成 EXE 还是直接运行脚本
        if getattr(sys, 'frozen', False):
            # 如果打包成 EXE，使用 EXE 所在目录
            application_path = os.path.dirname(sys.executable)
        else:
            # 直接运行脚本时使用脚本所在目录
            application_path = os.path.dirname(os.path.abspath(__file__))
            
        self.data_file = os.path.join(application_path, 'calendar_data.json')
        self.load_data()
        
    def save_data(self):
        """Save data to a JSON file"""
        data = {
            'personal_calendar': {},
            'busy_slots': []
        }
        
        # Convert personal_calendar to a serializable format
        for date, tasks in self.personal_calendar.items():
            data['personal_calendar'][date.isoformat()] = [
                {
                    'start': task['start'].isoformat(),
                    'end': task['end'].isoformat(),
                    'title': task['title']
                }
                for task in tasks
            ]
        
        # Convert busy_slots to a serializable format
        data['busy_slots'] = [
            {
                'start': slot['start'].isoformat(),
                'end': slot['end'].isoformat(),
                'title': slot['title']
            }
            for slot in self.busy_slots
        ]
        
        # Write to file
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_data(self):
        """Load data from a JSON file"""
        if not os.path.exists(self.data_file):
            return
        
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Load personal_calendar
            self.personal_calendar = {}
            for date_str, tasks in data['personal_calendar'].items():
                date = datetime.fromisoformat(date_str).date()
                self.personal_calendar[date] = [
                    {
                        'start': datetime.fromisoformat(task['start']),
                        'end': datetime.fromisoformat(task['end']),
                        'title': task['title']
                    }
                    for task in tasks
                ]
            
            # Load busy_slots
            self.busy_slots = [
                {
                    'start': datetime.fromisoformat(slot['start']),
                    'end': datetime.fromisoformat(slot['end']),
                    'title': slot['title']
                }
                for slot in data['busy_slots']
            ]
        except Exception as e:
            print(f"Error loading data: {e}")

    def add_task(self, start_time, end_time, title, is_personal=True):
        """Add a task and save it"""
        task = {
            'start': start_time,
            'end': end_time,
            'title': title
        }
        
        if is_personal:
            day_key = start_time.date()
            if day_key not in self.personal_calendar:
                self.personal_calendar[day_key] = []
            self.personal_calendar[day_key].append(task)
        
        self.busy_slots.append(task)
        self.save_data()  # Save after adding task

    def delete_task(self, date, task_index):
        """Delete a task by date and index"""
        try:
            if date not in self.personal_calendar or task_index >= len(self.personal_calendar[date]):
                return False

            # Get the task to delete
            task_to_delete = self.personal_calendar[date][task_index]
            
            # Remove from personal_calendar
            self.personal_calendar[date].pop(task_index)
            
            # If no more tasks on this date, remove the date entry
            if not self.personal_calendar[date]:
                del self.personal_calendar[date]
            
            # Remove from busy_slots
            for i, busy_slot in enumerate(self.busy_slots):
                if (busy_slot['start'] == task_to_delete['start'] and 
                    busy_slot['end'] == task_to_delete['end'] and 
                    busy_slot['title'] == task_to_delete['title']):
                    self.busy_slots.pop(i)
                    break
            
            self.save_data()  # Save after deleting task
            return True
        except Exception as e:
            print(f"Error deleting task: {e}")
            return False

    def get_available_windows(self, days=14):
        """Get available time windows within a given number of days"""
        available_windows = []
        start_date = datetime.now().date()
        
        for day in range(days):
            current_date = start_date + timedelta(days=day)
            
            # Start and end time for the day
            available_start = datetime.combine(current_date, self.wake_time)
            available_end = datetime.combine(current_date, self.sleep_time)
            
            # Get all busy slots for the day
            day_busy_slots = [
                slot for slot in self.busy_slots 
                if slot['start'].date() == current_date
            ]
            
            if not day_busy_slots:
                # If there are no tasks for the day, add the entire day's available time
                available_windows.append({
                    'start': available_start,
                    'end': available_end
                })
                continue
            
            # Sort by start time
            day_busy_slots.sort(key=lambda x: x['start'])
            
            # Check if there's available time before the first busy slot
            if day_busy_slots[0]['start'] > available_start:
                available_windows.append({
                    'start': available_start,
                    'end': day_busy_slots[0]['start']
                })
            
            # Check for gaps between busy slots
            for i in range(len(day_busy_slots)-1):
                if day_busy_slots[i]['end'] < day_busy_slots[i+1]['start']:
                    available_windows.append({
                        'start': day_busy_slots[i]['end'],
                        'end': day_busy_slots[i+1]['start']
                    })
            
            # Check if there's available time after the last busy slot
            if day_busy_slots[-1]['end'] < available_end:
                available_windows.append({
                    'start': day_busy_slots[-1]['end'],
                    'end': available_end
                })
        
        return available_windows

    def display_personal_calendar(self, days=14):
        """Display personal calendar"""
        start_date = datetime.now().date()
        calendar_data = []
        
        for day in range(days):
            current_date = start_date + timedelta(days=day)
            tasks_today = self.personal_calendar.get(current_date, [])
            
            if tasks_today:
                for i, task in enumerate(tasks_today):
                    calendar_data.append([
                        i,  # Add index for deletion reference
                        current_date.strftime("%Y-%m-%d"),
                        task['start'].strftime("%H:%M"),
                        task['end'].strftime("%H:%M"),
                        task['title']
                    ])
        
        if calendar_data:
            print("\n=== Personal Calendar ===")
            print(tabulate(calendar_data, headers=['Index', 'Date', 'Start Time', 'End Time', 'Task'], tablefmt='grid'))
        else:
            print("\nNo tasks scheduled.")

    def display_available_windows(self, days=14):
        """Display available time windows"""
        windows = self.get_available_windows(days)
        window_data = []
        
        for window in windows:
            window_data.append([
                window['start'].strftime("%Y-%m-%d"),
                window['start'].strftime("%H:%M"),
                window['end'].strftime("%H:%M")
            ])
        
        if window_data:
            print("\n=== Available Time Windows ===")
            print(tabulate(window_data, headers=['Date', 'Start Time', 'End Time'], tablefmt='grid'))
        else:
            print("\nNo available time windows.")

def main_menu():
    scheduler = PersonalScheduler()
    
    while True:
        print("\n=== Calendar Management System ===")
        print("1. Add Task")
        print("2. View Personal Calendar")
        print("3. View Available Time Windows")
        print("4. Delete Task")
        print("5. Exit")
        
        choice = input("\nPlease select an option (1-5): ")
        
        if choice == '1':
            try:
                date_str = input("Enter the date (YYYY-MM-DD): ")
                start_time_str = input("Enter the start time (HH:MM): ")
                end_time_str = input("Enter the end time (HH:MM): ")
                title = input("Enter task name: ")
                
                # Combine date and time
                date = datetime.strptime(date_str, "%Y-%m-%d").date()
                start_time = datetime.combine(date, datetime.strptime(start_time_str, "%H:%M").time())
                end_time = datetime.combine(date, datetime.strptime(end_time_str, "%H:%M").time())
                
                scheduler.add_task(start_time, end_time, title)
                print("Task added successfully!")
                
            except ValueError as e:
                print("Input format error, please try again!")
                
        elif choice == '2':
            scheduler.display_personal_calendar()
            
        elif choice == '3':
            scheduler.display_available_windows()
            
        elif choice == '4':
            scheduler.display_personal_calendar()
            try:
                if not scheduler.personal_calendar:
                    print("No tasks to delete!")
                    continue
                    
                date_str = input("Enter the date of the task to delete (YYYY-MM-DD): ")
                date = datetime.strptime(date_str, "%Y-%m-%d").date()
                
                if date not in scheduler.personal_calendar:
                    print("No tasks found on this date!")
                    continue
                
                task_index = int(input("Enter the index of the task to delete: "))
                
                if scheduler.delete_task(date, task_index):
                    print("Task deleted successfully!")
                else:
                    print("Failed to delete task. Please check the index and try again.")
            
            except ValueError as e:
                print("Invalid input format. Please try again!")
            
        elif choice == '5':
            print("Thank you for using the system!")
            break
            
        else:
            print("Invalid choice, please try again!")

if __name__ == "__main__":
    main_menu()