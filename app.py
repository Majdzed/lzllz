import streamlit as st
import pandas as pd
import random
import json
import os
import copy
from datetime import datetime, time

# Set page configuration
st.set_page_config(
    page_title="Group Schedule Generator",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'schedules' not in st.session_state:
    st.session_state.schedules = {}
    
if 'groups' not in st.session_state:
    st.session_state.groups = ["Group 1", "Group 2", "Group 3", "Group 4", "Group 5"]

if 'selected_group' not in st.session_state:
    st.session_state.selected_group = "Group 1"

# Constants for days and time slots
DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"]
TIME_SLOTS = [
    {"label": "08:00-09:30", "unavailable": []},
    {"label": "09:40-11:10", "unavailable": []},
    {"label": "11:20-12:50", "unavailable": []},
    {"label": "13:00-14:30", "unavailable": []},
    {"label": "14:40-16:10", "unavailable": []},
    {"label": "16:20-17:50", "unavailable": []}
]

# Courses and their components
COURSES = {
    "rx2": {
        "cours": {"teacher": "Dr. Zenadji", "shared": True},
        "td": {"teacher": "Mr.Sahli", "shared": False},
        "tp": {"teacher": "Dr. Zenadji", "shared": False}
    },
    "ro2": {
        "cours": {"teacher": "Dr. Issaadi", "shared": True},
        "td": {"teacher": "Dr. Issaadi", "shared": False}
    },
    "adhd": {
        "cours": {"teacher": "Prof. Djenadi", "shared": True},
        "td": {"teacher": "Prof. Djenadi", "shared": False}
    },
    "AI": {
        "cours": {"teacher": "Dr. Lekehali", "shared": True},
        "td": {"teacher": "Dr. Lekehali", "shared": False},
        "tp": {"teacher": "el chabiba", "shared": False}
    },
    "Entrepreneuriat": {
        "cours": {"teacher": "mme. Kaci", "shared": True}
    },
    "mf": {
        "cours": {"teacher": "Dr. el Zedk", "shared": True},
        "td": {"teacher": "Dr. el Zedk", "shared": False}
    },
    "security": {
        "cours": {"teacher": "Dr. Brahimi", "shared": True},
        "td": {"teacher": "Dr. Brahimi", "shared": False}
    },
    "an": {
        "cours": {"teacher": "Dr. Alkama", "shared": True},
        "td": {"teacher": "Dr. Alkama", "shared": False}
    }
}

# Additional teachers for different components of each course
ADDITIONAL_TEACHERS = {
    "Math": {
        "td": ["Dr. Smith", "Ms. Thompson", "Mr. Roberts"],
        "tp": ["Mr. Johnson", "Ms. Lee", "Dr. Hall"]
    },
    "Physics": {
        "td": ["Dr. Brown", "Dr. Green", "Ms. Walker"],
        "tp": ["Ms. Davis", "Mr. Wright", "Dr. Rodriguez"]
    },
    "Chemistry": {
        "td": ["Dr. Wilson", "Dr. Martin", "Mr. King"],
        "tp": ["Mrs. Taylor", "Dr. Lopez", "Ms. Young"]
    },
    "Programming": {
        "td": ["Prof. Clark", "Dr. Hughes", "Mrs. Baker"],
        "tp": ["Mr. Anderson", "Ms. Cook", "Prof. Sanders"]
    },
    "Algorithms": {
        "td": ["Dr. White", "Dr. Morris", "Prof. Bell"],
        "tp": ["Ms. Martinez", "Mr. Cooper", "Dr. Reed"]
    }
}

# Backup teachers that can be used if no other teachers are available
BACKUP_TEACHERS = {
    "Math": ["Dr. Parker", "Prof. Edwards", "Dr. Gonzalez", "Ms. Perez", "Dr. Collins", "Dr. Alkama", "Dr. Zenadji", "Prof. Khan", "Dr. Silverman", "Dr. Gupta"],
    "Physics": ["Dr. Morgan", "Prof. Peterson", "Dr. James", "Ms. Watson", "Dr. Garcia", "Dr. Issaadi", "Prof. Djenadi", "Dr. Rodriguez", "Prof. Takahashi", "Dr. Chen"],
    "Chemistry": ["Dr. Henderson", "Prof. Torres", "Dr. Murphy", "Ms. Nelson", "Dr. Rivera", "Dr. Lekehali", "Dr. Brahimi", "Prof. Ramirez", "Dr. Patel", "Dr. Kim"],
    "Programming": ["Dr. Bennett", "Prof. Carter", "Dr. Price", "Mr. Adams", "Dr. Powell", "Dr. el Zedk", "Mme. Kaci", "Prof. Nguyen", "Dr. Singh", "Dr. Malhotra"],
    "Algorithms": ["Dr. Mitchell", "Prof. Turner", "Dr. Evans", "Ms. Jenkins", "Dr. Foster", "Mr. Sahli", "Dr. el chabiba", "Prof. Sharma", "Dr. Nakamura", "Dr. Petrov"]
}

# Additional backup teachers for specific components
COMPONENT_BACKUP_TEACHERS = {
    "td": ["Dr. Alkama", "Mr. Sahli", "Dr. Issaadi", "Prof. Djenadi", "Dr. Lekehali", "Dr. el Zedk", "Dr. Brahimi", "Prof. Khan", "Dr. Singh", "Prof. Ramirez"],
    "tp": ["Dr. Zenadji", "el chabiba", "Ms. Jenkins", "Dr. Foster", "Ms. Martinez", "Mr. Anderson", "Ms. Lee", "Dr. Chen", "Dr. Kim", "Dr. Malhotra"]
}

# Check if a time slot is available
def is_slot_available(day, slot_index):
    # No classes on Tuesday afternoon
    if day == "Tuesday" and slot_index >= 3:  # After 13:00
        return False
    return True

# Check if scheduling this slot would create more than 3 consecutive sessions
def would_create_too_many_consecutive_sessions(group, day, slot_index, consecutive_sessions):
    # Initialize consecutive count for this slot if not exists
    if slot_index not in consecutive_sessions[group][day]:
        consecutive_sessions[group][day][slot_index] = 1
        # Check if there are consecutive sessions before this
        if slot_index > 0 and (slot_index - 1) in consecutive_sessions[group][day]:
            # If the previous slot has a session (any type), count it as consecutive
            prev_consecutive = consecutive_sessions[group][day][slot_index - 1]
            consecutive_sessions[group][day][slot_index] = prev_consecutive + 1
    
    # Check if the consecutive count exceeds 3
    if consecutive_sessions[group][day].get(slot_index, 0) > 3:
        return True
    return False

# Insert empty slot to break consecutive sessions if needed
def insert_break_if_needed(group, day, consecutive_sessions):
    # Find sequences of more than 3 consecutive sessions
    for slot_index in range(len(TIME_SLOTS)):
        if slot_index in consecutive_sessions[group][day] and consecutive_sessions[group][day][slot_index] > 3:
            # Find a good slot to make empty to break the sequence
            # Prefer to insert break in the middle of a long sequence
            start_index = slot_index - consecutive_sessions[group][day][slot_index] + 1
            middle_index = start_index + ((consecutive_sessions[group][day][slot_index] - 1) // 2)
            
            # Make the middle slot empty if it's not already
            if st.session_state.schedules[group][day].get(TIME_SLOTS[middle_index]["label"]) not in [None, "BREAK"]:
                st.session_state.schedules[group][day][TIME_SLOTS[middle_index]["label"]] = "BREAK"
                
                # Update consecutive sessions after inserting break
                # Reset counts for all slots after the break
                for i in range(middle_index + 1, len(TIME_SLOTS)):
                    # Count starts from 1 at middle_index+1
                    if i in consecutive_sessions[group][day]:
                        consecutive_sessions[group][day][i] = i - middle_index
            
            return True
    return False

# Generate schedules for all groups
def generate_all_schedules():
    st.session_state.schedules = {}
    
    # Initialize empty schedules for all groups
    for group in st.session_state.groups:
        st.session_state.schedules[group] = {}
        for day in DAYS:
            st.session_state.schedules[group][day] = {}
            for slot in TIME_SLOTS:
                if is_slot_available(day, TIME_SLOTS.index(slot)):
                    st.session_state.schedules[group][day][slot["label"]] = None
                else:
                    st.session_state.schedules[group][day][slot["label"]] = "UNAVAILABLE"
    
    # Track teacher availability and days taught
    teacher_schedule = {}  # For timeslot conflicts
    teacher_days = {}  # For tracking days a teacher teaches
    
    # Track courses per day for each group (limit of 2 cours per day)
    group_daily_courses = {group: {day: [] for day in DAYS} for group in st.session_state.groups}
    
    # Track consecutive sessions for each group
    consecutive_sessions = {group: {day: {} for day in DAYS} for group in st.session_state.groups}
    
    # First, schedule all shared "cours" sessions
    all_shared_sessions = []
    for course_name, components in COURSES.items():
        for component_name, details in components.items():
            if details.get("shared", False):
                all_shared_sessions.append({
                    "course": course_name,
                    "component": component_name,
                    "teacher": details["teacher"],
                    "label": f"{course_name} {component_name} ({details['teacher']}) (ALL)"
                })
    
    # Shuffle shared sessions for random scheduling
    random.shuffle(all_shared_sessions)
    
    # This is a greedy algorithm with backtracking characteristics
    # It tries to schedule each session in the first available slot
    # If a constraint is violated, it "backtracks" by skipping the current slot
    # and trying the next one until a valid slot is found
    
    # Schedule shared sessions
    for session in all_shared_sessions:
        scheduled = False
        
        # Try each day and time slot
        days = DAYS.copy()
        random.shuffle(days)
        
        for day in days:
            if scheduled:
                break
                
            # Check if teacher already teaches on 2 days
            teacher = session['teacher']
            if teacher in teacher_days and len(teacher_days[teacher]) >= 2 and day not in teacher_days[teacher]:
                continue  # Backtrack: Skip this day, teacher already teaches on 2 other days
            
            # Check if adding this course would exceed the 2 cours per day limit for any group
            if session["component"] == "cours":
                can_schedule = True
                for group in st.session_state.groups:
                    if len(group_daily_courses[group][day]) >= 2:
                        can_schedule = False
                        break
                if not can_schedule:
                    continue  # Backtrack: Skip this day, some group already has 2 courses
                
            slots = [s["label"] for s in TIME_SLOTS]
            random.shuffle(slots)
            
            for slot_label in slots:
                slot_index = next((i for i, s in enumerate(TIME_SLOTS) if s["label"] == slot_label), None)
                
                # Skip unavailable slots
                if not is_slot_available(day, slot_index):
                    continue  # Backtrack: This slot is unavailable
                
                # Check if all groups have this slot available
                all_available = True
                # Check consecutive sessions constraint for all groups
                consecutive_ok = True
                
                for group in st.session_state.groups:
                    # Check if slot is available
                    if st.session_state.schedules[group][day].get(slot_label) is not None:
                        all_available = False
                        break
                    
                    # Check if this would create more than 3 consecutive sessions
                    if would_create_too_many_consecutive_sessions(group, day, slot_index, consecutive_sessions):
                        consecutive_ok = False
                        break
                
                if not all_available or not consecutive_ok:
                    continue  # Backtrack: This slot violates a constraint
                
                # Check if teacher is available
                teacher_key = f"{teacher}_{day}_{slot_label}"
                if teacher_key not in teacher_schedule:
                    # Track teacher's day
                    if teacher not in teacher_days:
                        teacher_days[teacher] = set()
                    teacher_days[teacher].add(day)
                    
                    # Schedule this session for all groups
                    for group in st.session_state.groups:
                        st.session_state.schedules[group][day][slot_label] = session["label"]
                        
                        # Track courses per day if this is a cours component
                        if session["component"] == "cours":
                            group_daily_courses[group][day].append(session["course"])
                        
                        # Update consecutive sessions
                        if slot_index not in consecutive_sessions[group][day]:
                            consecutive_sessions[group][day][slot_index] = 1
                            # Check if there are consecutive sessions before this
                            if slot_index > 0 and (slot_index - 1) in consecutive_sessions[group][day]:
                                prev_consecutive = consecutive_sessions[group][day][slot_index - 1]
                                consecutive_sessions[group][day][slot_index] = prev_consecutive + 1
                        
                        # Update consecutive count for next slots as well
                        for next_idx in range(slot_index + 1, len(TIME_SLOTS)):
                            if st.session_state.schedules[group][day].get(TIME_SLOTS[next_idx]["label"]) is not None:
                                consecutive_sessions[group][day][next_idx] = consecutive_sessions[group][day][slot_index] + 1
                    
                    teacher_schedule[teacher_key] = True
                    scheduled = True
                    break
        
        if not scheduled:
            # If we get here, we couldn't find a valid slot for this session after trying all possibilities
            # This is where a full backtracking algorithm would go back and undo previous assignments
            # Instead, we just report the failure and continue with the next session
            st.warning(f"Could not schedule shared session: {session['course']} {session['component']}")
            
            # In a true backtracking algorithm, we would now try the following:
            # 1. Undo some previous assignments
            # 2. Try alternative choices for those assignments
            # 3. Continue with the current session again
    
    # Next, schedule individual TD and TP sessions for each group
    # The same backtracking characteristics apply here
    for course_name, components in COURSES.items():
        for component_name, details in components.items():
            if not details.get("shared", False):
                # Get appropriate teachers for this component
                teachers = []
                if course_name in ADDITIONAL_TEACHERS and component_name in ADDITIONAL_TEACHERS[course_name]:
                    teachers = ADDITIONAL_TEACHERS[course_name][component_name]
                else:
                    teachers = [details["teacher"]] * len(st.session_state.groups)
                
                # Try backup teachers if needed
                if len(teachers) == 0 and course_name in BACKUP_TEACHERS:
                    teachers = BACKUP_TEACHERS[course_name]
                
                # For each group, schedule this component
                for i, group in enumerate(st.session_state.groups):
                    # Try each teacher until we find one that works with the 2-day constraint
                    best_teacher = None
                    teacher_found = False
                    
                    # First try the original assigned teacher or the one in the rotation
                    original_teacher = teachers[i % len(teachers)]
                    
                    if original_teacher not in teacher_days or len(teacher_days[original_teacher]) < 2:
                        best_teacher = original_teacher
                        teacher_found = True
                    else:
                        # Try other teachers - this is a form of backtracking at the teacher selection level
                        for potential_teacher in teachers:
                            if potential_teacher not in teacher_days or len(teacher_days[potential_teacher]) < 2:
                                best_teacher = potential_teacher
                                teacher_found = True
                                break
                        
                        # If still no teacher found, try backup teachers
                        if not teacher_found and course_name in BACKUP_TEACHERS:
                            for potential_teacher in BACKUP_TEACHERS[course_name]:
                                if potential_teacher not in teacher_days or len(teacher_days[potential_teacher]) < 2:
                                    best_teacher = potential_teacher
                                    teacher_found = True
                                    break
                    
                    # If no teacher found with < 2 days, just use any available teacher
                    if not teacher_found:
                        best_teacher = original_teacher
                    
                    teacher = best_teacher
                    
                    session = {
                        "course": course_name,
                        "component": component_name,
                        "teacher": teacher,
                        "label": f"{course_name} {component_name} ({teacher}) ({group})"
                    }
                    
                    scheduled = False
                    
                    # Try each day and time slot
                    days = DAYS.copy()
                    random.shuffle(days)
                    
                    # First try days the teacher already teaches on
                    preferred_days = list(teacher_days.get(teacher, set()))
                    if preferred_days:
                        # Add these days first
                        for day in preferred_days:
                            if day in days:  # Make sure day hasn't been removed
                                days.remove(day)
                        days = preferred_days + days
                    
                    # This is another backtracking loop - try each day until we find a valid one
                    for day in days:
                        if scheduled:
                            break
                            
                        # Check teacher day constraint
                        if teacher in teacher_days and len(teacher_days[teacher]) >= 2 and day not in teacher_days[teacher]:
                            continue  # Backtrack: Skip this day, teacher already teaches on 2 other days
                        
                        # For td/tp, try to schedule on days where the student already has the cours
                        # but still respect the 2 course limit
                        if component_name != "cours" and course_name in group_daily_courses[group][day]:
                            # This is ideal - schedule TD/TP on same day as the lecture
                            pass
                        else:
                            # Not ideal, but still possible if there's space
                            pass
                            
                        slots = [s["label"] for s in TIME_SLOTS]
                        random.shuffle(slots)
                        
                        # Try each time slot until we find a valid one - backtracking at the slot level
                        for slot_label in slots:
                            slot_index = next((i for i, s in enumerate(TIME_SLOTS) if s["label"] == slot_label), None)
                            
                            # Skip unavailable slots
                            if not is_slot_available(day, slot_index):
                                continue  # Backtrack: This slot is unavailable
                            
                            # Check if this slot is available for this group
                            if st.session_state.schedules[group][day].get(slot_label) is None:
                                # Check if teacher is available at this time
                                teacher_key = f"{teacher}_{day}_{slot_label}"
                                if teacher_key not in teacher_schedule:
                                    # Check consecutive sessions constraint
                                    if would_create_too_many_consecutive_sessions(group, day, slot_index, consecutive_sessions):
                                        continue  # Backtrack: This would exceed the consecutive session limit
                                    
                                    # Track teacher's day
                                    if teacher not in teacher_days:
                                        teacher_days[teacher] = set()
                                    teacher_days[teacher].add(day)
                                    
                                    # Schedule this session
                                    st.session_state.schedules[group][day][slot_label] = session["label"]
                                    teacher_schedule[teacher_key] = True
                                    
                                    # Update consecutive sessions
                                    if slot_index not in consecutive_sessions[group][day]:
                                        consecutive_sessions[group][day][slot_index] = 1
                                        # Check if there are consecutive sessions before this
                                        if slot_index > 0 and (slot_index - 1) in consecutive_sessions[group][day]:
                                            prev_consecutive = consecutive_sessions[group][day][slot_index - 1]
                                            consecutive_sessions[group][day][slot_index] = prev_consecutive + 1
                                    
                                    # Update consecutive count for next slots as well
                                    for next_idx in range(slot_index + 1, len(TIME_SLOTS)):
                                        if st.session_state.schedules[group][day].get(TIME_SLOTS[next_idx]["label"]) is not None:
                                            consecutive_sessions[group][day][next_idx] = consecutive_sessions[group][day][slot_index] + 1
                                    
                                    scheduled = True
                                    break
                    
                    if not scheduled:
                        # As with shared sessions, we couldn't find a valid slot after trying all possibilities
                        # In a full backtracking algorithm, we would undo previous assignments and try again
                        st.warning(f"Could not schedule: {session['course']} {session['component']} for {group}")
                        
                        # We could potentially try:
                        # 1. A different teacher, even if they teach on more than 2 days
                        # 2. Alternative ways to schedule previous sessions to make room for this one
    
    # Insert breaks to resolve consecutive session issues
    for group in st.session_state.groups:
        for day in DAYS:
            insert_break_if_needed(group, day, consecutive_sessions)
    
    st.success("Schedules generated for all groups!")
    
    # Show summary of teacher days
    teacher_count = {}
    for teacher, days in teacher_days.items():
        teacher_count[teacher] = len(days)
    
    # Check if any teacher teaches more than 2 days
    over_limit = [f"{teacher}: {count} days" for teacher, count in teacher_count.items() if count > 2]
    if over_limit:
        st.warning("Some teachers are scheduled for more than 2 days:")
        for item in over_limit:
            st.write(f"- {item}")

# Save schedules to file
def save_schedules():
    with open("schedules.json", "w") as f:
        json.dump(st.session_state.schedules, f)
    st.success("Schedules saved to 'schedules.json'")

# Load schedules from file
def load_schedules():
    if os.path.exists("schedules.json"):
        with open("schedules.json", "r") as f:
            st.session_state.schedules = json.load(f)
        st.success("Schedules loaded from 'schedules.json'")
    else:
        st.error("No saved schedules found.")

# Display a schedule as a table
def display_schedule(group_name):
    if group_name not in st.session_state.schedules:
        st.warning(f"No schedule generated for {group_name} yet.")
        return
    
    schedule = st.session_state.schedules[group_name]
    
    # Create DataFrame for display
    schedule_df = pd.DataFrame(index=[slot["label"] for slot in TIME_SLOTS], columns=DAYS)
    
    # Count courses per day
    courses_per_day = {day: [] for day in DAYS}
    
    # Fill DataFrame with schedule data
    for day in DAYS:
        for slot in TIME_SLOTS:
            slot_label = slot["label"]
            value = schedule[day].get(slot_label, "")
            
            # Count lectures ("cours") on this day
            if value and "cours" in value:
                parts = value.split()
                if len(parts) >= 2 and parts[0] not in courses_per_day[day]:
                    courses_per_day[day].append(parts[0])
            
            # Highlight shared sessions
            if value and "(ALL)" in value:
                value = f"🔄 {value}"
                
            schedule_df.at[slot_label, day] = value
    
    # Display the schedule
    st.dataframe(
        schedule_df.style.applymap(
            lambda x: "background-color: #ffcccb" if x == "UNAVAILABLE" else
                     ("background-color: #d4f1f9" if x and "🔄" in x else  # Shared sessions
                      "background-color: #d5f5e3" if x else  # Individual sessions
                      "background-color: white")
        ),
        use_container_width=True
    )
    
    # Display courses per day count
    st.write("**Courses per day:**")
    for day in DAYS:
        count = len(courses_per_day[day])
        status = "✅" if count <= 2 else "❌"
        st.write(f"- {day}: {count} courses {status}")
    
    return schedule_df

# Display all schedules in tabs
def display_all_schedules():
    if not st.session_state.schedules:
        st.warning("No schedules generated yet. Click 'Generate Schedules' to create schedules for all groups.")
        return
    
    tabs = st.tabs(st.session_state.groups)
    
    for i, group in enumerate(st.session_state.groups):
        with tabs[i]:
            st.subheader(f"Schedule for {group}")
            
            # Add legend for shared sessions
            st.write("**Legend:**")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("🔄 - Shared lecture (all groups attend)")
            with col2:
                st.markdown("Regular session (only this group attends)")
            
            df = display_schedule(group)
            
            # Download button for this group's schedule
            csv = df.to_csv() if df is not None else ""
            if csv:
                st.download_button(
                    label=f"Download {group} Schedule",
                    data=csv,
                    file_name=f"{group.lower().replace(' ', '_')}_schedule.csv",
                    mime="text/csv"
                )

# Validate all schedules to check for conflicts
def validate_schedules():
    if not st.session_state.schedules:
        st.warning("No schedules to validate.")
        return
    
    all_valid = True
    issues = []
    
    # Track teacher assignments per time slot
    teacher_assignments = {}
    
    # Track which courses each group has
    group_courses = {group: {} for group in st.session_state.groups}
    
    # Track days per teacher
    teacher_days = {}
    
    # Track courses per day for each group
    group_daily_courses = {group: {day: [] for day in DAYS} for group in st.session_state.groups}
    
    # Check all schedules
    for group, schedule in st.session_state.schedules.items():
        for day in DAYS:
            for slot_label in [s["label"] for s in TIME_SLOTS]:
                session = schedule[day].get(slot_label)
                
                if session and session != "UNAVAILABLE":
                    # Extract teacher name - now it's included in the session label
                    if "(" in session and ")" in session:
                        teacher = None
                        parts = session.split("(")
                        for part in parts:
                            if ")" in part and not part.strip().startswith("ALL") and not part.strip().startswith("Group"):
                                teacher = part.split(")")[0].strip()
                                break
                        
                        if teacher:
                            # Track teacher days
                            if teacher not in teacher_days:
                                teacher_days[teacher] = set()
                            teacher_days[teacher].add(day)
                            
                            # Check for teacher conflicts
                            time_key = f"{day}_{slot_label}"
                            if time_key not in teacher_assignments:
                                teacher_assignments[time_key] = []
                            
                            if teacher in teacher_assignments[time_key]:
                                all_valid = False
                                issues.append(f"Teacher conflict: {teacher} is scheduled twice at {day} {slot_label}")
                            teacher_assignments[time_key].append(teacher)
                    
                    # Extract course and component
                    parts = session.split()
                    if len(parts) >= 2:
                        course = parts[0]
                        component = parts[1]
                        
                        # Record this course for the group
                        if course not in group_courses[group]:
                            group_courses[group][course] = set()
                        group_courses[group][course].add(component)
                        
                        # Track courses per day (for the 2 cours max constraint)
                        if component == "cours" and course not in group_daily_courses[group][day]:
                            group_daily_courses[group][day].append(course)
    
    # Check teacher day constraints
    for teacher, days in teacher_days.items():
        if len(days) > 2:
            all_valid = False
            issues.append(f"Teacher constraint: {teacher} teaches on {len(days)} days (max is 2)")
    
    # Check if all groups have all required components
    for group, courses in group_courses.items():
        for course_name, components in COURSES.items():
            if course_name not in courses:
                all_valid = False
                issues.append(f"{group} is missing all components of {course_name}")
            else:
                for component_name in components:
                    if component_name not in courses[course_name]:
                        all_valid = False
                        issues.append(f"{group} is missing {course_name} {component_name}")
    
    # Check if any group has more than 2 courses in a day
    for group, daily_courses in group_daily_courses.items():
        for day, courses in daily_courses.items():
            if len(courses) > 2:
                all_valid = False
                issues.append(f"{group} has {len(courses)} courses on {day} (max is 2)")
    
    # Display validation results
    if all_valid:
        st.success("All schedules are valid! No conflicts found.")
    else:
        st.error("Issues detected in the schedules:")
        for issue in issues:
            st.write(f"- {issue}")

# Analyze course distribution across groups
def analyze_course_distribution():
    if not st.session_state.schedules:
        st.warning("No schedules to analyze.")
        return
    
    # Initialize counters for each course component
    course_counters = {}
    for course in COURSES:
        course_counters[course] = {}
        for component in COURSES[course]:
            course_counters[course][component] = {
                "shared": 0,
                "individual": {group: 0 for group in st.session_state.groups}
            }
    
    # Count occurrences of each course component
    for group, schedule in st.session_state.schedules.items():
        for day in DAYS:
            for slot_label in [s["label"] for s in TIME_SLOTS]:
                session = schedule[day].get(slot_label)
                
                if session and session != "UNAVAILABLE":
                    # Parse the session info
                    parts = session.split()
                    if len(parts) >= 2:
                        course = parts[0]
                        component = parts[1]
                        
                        if course in course_counters and component in course_counters[course]:
                            if "(ALL)" in session:
                                course_counters[course][component]["shared"] += 1
                            else:
                                course_counters[course][component]["individual"][group] += 1
    
    # Create a DataFrame for display
    data = []
    for course, components in course_counters.items():
        for component, counts in components.items():
            shared = counts["shared"] > 0
            status = "✅" if shared and all(count == 1 for count in counts["individual"].values()) else "❌"
            
            row = {
                "Course": course,
                "Component": component,
                "Shared Session": "Yes" if shared else "No",
                "Status": status
            }
            
            # Add individual counts for each group
            for group, count in counts["individual"].items():
                row[group] = count
            
            data.append(row)
    
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True)

# Display teacher workload
def display_teacher_workload():
    if not st.session_state.schedules:
        st.warning("No schedules to analyze.")
        return
    
    # Track teachers and their days
    teacher_days = {}
    teacher_sessions = {}
    
    # Analyze all schedules
    for group, schedule in st.session_state.schedules.items():
        for day in DAYS:
            for slot_label in [s["label"] for s in TIME_SLOTS]:
                session = schedule[day].get(slot_label)
                
                if session and session != "UNAVAILABLE":
                    # Extract teacher name
                    if "(" in session and ")" in session:
                        parts = session.split("(")
                        teacher = None
                        for part in parts:
                            if ")" in part and not part.strip().startswith("ALL") and not part.strip().startswith("Group"):
                                teacher = part.split(")")[0].strip()
                                break
                        
                        if teacher:
                            # Track teacher days
                            if teacher not in teacher_days:
                                teacher_days[teacher] = set()
                                teacher_sessions[teacher] = 0
                            
                            teacher_days[teacher].add(day)
                            teacher_sessions[teacher] += 1
    
    # Create a DataFrame for display
    data = []
    for teacher, days in teacher_days.items():
        day_list = ", ".join(sorted(days))
        status = "✅" if len(days) <= 2 else "❌"
        
        data.append({
            "Teacher": teacher,
            "Number of Days": len(days),
            "Days": day_list,
            "Total Sessions": teacher_sessions[teacher],
            "Status": status
        })
    
    df = pd.DataFrame(data)
    df = df.sort_values(by="Number of Days", ascending=False)
    
    st.dataframe(df, use_container_width=True)

# Analyze course distribution by day
def analyze_daily_course_load():
    if not st.session_state.schedules:
        st.warning("No schedules to analyze.")
        return
    
    # Track courses per day for each group
    group_daily_courses = {group: {day: [] for day in DAYS} for group in st.session_state.groups}
    
    # Count courses per day
    for group, schedule in st.session_state.schedules.items():
        for day in DAYS:
            for slot_label in [s["label"] for s in TIME_SLOTS]:
                session = schedule[day].get(slot_label)
                
                if session and session != "UNAVAILABLE" and "cours" in session:
                    parts = session.split()
                    if len(parts) >= 1:
                        course = parts[0]
                        if course not in group_daily_courses[group][day]:
                            group_daily_courses[group][day].append(course)
    
    # Create DataFrame for display
    data = []
    
    for group in st.session_state.groups:
        for day in DAYS:
            courses = group_daily_courses[group][day]
            course_list = ", ".join(courses)
            status = "✅" if len(courses) <= 2 else "❌"
            
            data.append({
                "Group": group,
                "Day": day,
                "Number of Lectures": len(courses),
                "Courses": course_list,
                "Status": status
            })
    
    df = pd.DataFrame(data)
    
    # Calculate statistics
    max_courses = df["Number of Lectures"].max()
    avg_courses = df["Number of Lectures"].mean()
    
    st.subheader("Daily Course Load Analysis")
    
    st.write(f"**Maximum lectures per day:** {max_courses}")
    st.write(f"**Average lectures per day:** {avg_courses:.2f}")
    
    # Show the dataframe
    st.dataframe(
        df.style.applymap(
            lambda x: "background-color: #ffcccb" if x == "❌" else "background-color: #d5f5e3" if x == "✅" else "", 
            subset=["Status"]
        ),
        use_container_width=True
    )

# Main application
def main():
    st.title("Group Schedule Generator")
    
    # Sidebar
    with st.sidebar:
        st.header("Controls")
        
        if st.button("Generate Schedules", key="generate"):
            generate_all_schedules()
        
        st.divider()
        
        if st.button("Save Schedules", key="save"):
            save_schedules()
        
        if st.button("Load Schedules", key="load"):
            load_schedules()
        
        st.divider()
        
        if st.button("Validate Schedules", key="validate"):
            validate_schedules()
        
        st.divider()
        
        st.subheader("Course Information")
        
        # Display course information
        for course, components in COURSES.items():
            with st.expander(f"{course}"):
                for component, details in components.items():
                    shared_text = "Shared" if details.get("shared", False) else "Separate"
                    st.write(f"**{component}**: {details['teacher']} ({shared_text})")
        
        st.divider()
        
        st.write("**Note:** No classes on Tuesday afternoons")
        st.write("**Note:** Maximum 2 courses per day")
    
    # Main content
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Schedules", "Course Analysis", "Teacher Workload", "Daily Load", "Information"])
    
    with tab1:
        display_all_schedules()
    
    with tab2:
        st.header("Course Distribution Analysis")
        analyze_course_distribution()
    
    with tab3:
        st.header("Teacher Workload Analysis")
        display_teacher_workload()
    
    with tab4:
        analyze_daily_course_load()
    
    with tab5:
        st.header("About the Schedule Generator")
        st.write("""    
        This application generates class schedules for 5 student groups, taking into account:
        
        - 5 different courses with varying components (cours, td, tp)
        - All groups attend lectures (cours) together in a shared session
        - Each group has its own separate sessions for tutorials (td) and practical work (tp)
        - Each group takes exactly one session of each course component
        - School hours are 8:00 AM to 5:50 PM
        - Each session lasts 1:30 hours with 10-minute breaks between sessions
        - No classes on Tuesday afternoons
        - Teachers cannot be in two places at once
        - Teachers should not teach on more than 2 days per week
        - **Students should not have more than 2 different courses in one day**
        
        Use the controls in the sidebar to generate, save, load, and validate schedules.
        """)
        
        st.subheader("Course Legend")
        st.write("- **cours**: Lecture (shared by all groups)")
        st.write("- **td**: Tutorial/Directed Work (separate for each group)")
        st.write("- **tp**: Practical Work (separate for each group)")
        
        st.subheader("Color Legend")
        st.markdown("""
        - <span style='background-color: #d4f1f9; padding: 3px 6px;'>Blue</span>: Shared sessions (all groups)
        - <span style='background-color: #d5f5e3; padding: 3px 6px;'>Green</span>: Individual sessions
        - <span style='background-color: #ffcccb; padding: 3px 6px;'>Red</span>: Unavailable time slots
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()