import streamlit as st
import pandas as pd
import random
import copy
from collections import deque

st.set_page_config(page_title="1CS Timetable Scheduler", layout="wide")
st.title("1CS Semester 2 Timetable Scheduler")

# Define constants
DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"]
SLOTS = ["08:30-10:00", "10:10-11:40", "11:45-13:15", "13:20-14:50", "15:00-16:30"]
ROOM_TYPES = ["Lecture Hall", "TD Room", "TP Lab"]
ROOMS = {
    "Lecture Hall": ["Amphi 7"],
    "TD Room": ["S4", "S5", "S6", "S7", "S8", "S9", "S14", "S15", "S17", "S18", "S19"],
    "TP Lab": ["SM3", "SM4", "SM7", "SM10", "SM11"]
}

# Define the number of groups
NUM_GROUPS = 6

# Define courses and their requirements
COURSES = {
    "Sécurité": {
        "lectures": 1,
        "td": 1,
        "tp": 0,
        "teachers": {
            "lecture": "Dr. Brahmi",
            "td": "Dr. Brahmi",
            "tp": None
        }
    },
    "Méthodes Formelles": {
        "lectures": 1,
        "td": 1,
        "tp": 0,
        "teachers": {
            "lecture": "Dr. Zedek",
            "td": "Dr. Zedek",
            "tp": None
        }
    },
    "Analyse numérique": {
        "lectures": 1,
        "td": 1,
        "tp": 0,
        "teachers": {
            "lecture": "Dr. Alkama",
            "td": "Dr. Alkama",
            "tp": None
        }
    },
    "Entrepreneuriat": {
        "lectures": 1,
        "td": 0,
        "tp": 0,
        "teachers": {
            "lecture": "Dr. Kaci",
            "td": None,
            "tp": None
        }
    },
    "Recherche Opérationnelle 2": {
        "lectures": 1,
        "td": 1,
        "tp": 0,
        "teachers": {
            "lecture": "Dr. Issadi",
            "td": "Dr. Issadi",
            "tp": None
        }
    },
    "Distributed Architecture & Intensive Computing": {
        "lectures": 1,
        "td": 1,
        "tp": 0,
        "teachers": {
            "lecture": "Dr. Djenadi",
            "td": "Dr. Djenadi",
            "tp": None
        }
    },
    "Réseaux 2": {
        "lectures": 1,
        "td": 1,
        "tp": 1,
        "teachers": {
            "lecture": "Dr. Zenadji",
            "td": "M. Sahli",
            "tp": "Dr. Zenadji"
        }
    },
    "Artificial Intelligence": {
        "lectures": 1,
        "td": 1,
        "tp": 1,
        "teachers": {
            "lecture": "Dr. Lekehali",
            "td": "Dr. Lekehali",
            "tp": ["Mme Alkama", "M. Embarki", "M. Brahami", "M. Badache", "M. Chelghoum"]
        }
    },
}

# Create all possible sessions that need to be scheduled
def create_sessions():
    sessions = []
    
    # Create lecture sessions (shared by all groups)
    for course_name, course_info in COURSES.items():
        for _ in range(course_info["lectures"]):
            sessions.append({
                "course": course_name,
                "type": "lecture",
                "group": "all",
                "teacher": course_info["teachers"]["lecture"],
                "room_type": "Lecture Hall"
            })
    
    # Create TD and TP sessions (separate for each group)
    for group_idx in range(1, NUM_GROUPS + 1):
        group_name = f"G{group_idx}"
        for course_name, course_info in COURSES.items():
            # TD sessions
            for _ in range(course_info["td"]):
                sessions.append({
                    "course": course_name,
                    "type": "td",
                    "group": group_name,
                    "teacher": course_info["teachers"]["td"],
                    "room_type": "TD Room"
                })
            
            # TP sessions
            for _ in range(course_info["tp"]):
                # Handle different teachers for AI TP
                if course_name == "Artificial Intelligence" and course_info["teachers"]["tp"] and isinstance(course_info["teachers"]["tp"], list):
                    teacher_idx = (group_idx - 1) % len(course_info["teachers"]["tp"])
                    tp_teacher = course_info["teachers"]["tp"][teacher_idx]
                else:
                    tp_teacher = course_info["teachers"]["tp"]
                
                if tp_teacher:
                    sessions.append({
                        "course": course_name,
                        "type": "tp",
                        "group": group_name,
                        "teacher": tp_teacher,
                        "room_type": "TP Lab"
                    })
    
    return sessions

# CSP Variables
class TimeTableCSP:
    def __init__(self):
        self.sessions = create_sessions()
        self.variables = []
        self.domains = {}
        self.assignment = {}
        self.initialize_csp()
        
    def initialize_csp(self):
        # Create variables for each session
        for i, session in enumerate(self.sessions):
            var_name = f"{session['course']}_{session['type']}_{session['group']}_{i}"
            self.variables.append(var_name)
            
            # Define domain for each variable (all possible day-slot-room combinations)
            self.domains[var_name] = []
            
            # For Tuesday, we only consider morning slots (the first 3)
            # For other days, we consider all slots
            for day in DAYS:
                available_slots = SLOTS[:3] if day == "Tuesday" else SLOTS
                for slot in available_slots:
                    for room in ROOMS[session["room_type"]]:
                        self.domains[var_name].append((day, slot, room))
    
    def is_consistent(self, var, value, assignment):
        """Check if assigning value to var is consistent with the current assignment"""
        day, slot, room = value
        
        # Find the session info for this variable
        session_info = var.split('_')
        course_name = session_info[0]
        session_type = session_info[1]
        group_name = session_info[2]
        session_idx = int(session_info[3])
        
        # Get the full session details
        session = self.sessions[session_idx]
        
        # Check for conflicts with existing assignments
        for assigned_var, assigned_value in assignment.items():
            assigned_info = assigned_var.split('_')
            assigned_course = assigned_info[0]
            assigned_type = assigned_info[1]
            assigned_group = assigned_info[2]
            assigned_idx = int(assigned_info[3])
            
            assigned_day, assigned_slot, assigned_room = assigned_value
            assigned_session = self.sessions[assigned_idx]
            
            # 1. Same day and slot: check for conflicts
            if assigned_day == day and assigned_slot == slot:
                # Same room conflict
                if assigned_room == room:
                    return False
                
                # Same teacher conflict
                if assigned_session["teacher"] == session["teacher"]:
                    return False
                
                # Same group conflict for non-lecture sessions
                if assigned_group == group_name and assigned_group != "all" and group_name != "all":
                    return False
                
                # Lecture and group-specific session conflict
                if (assigned_group == "all" and group_name != "all") or (assigned_group != "all" and group_name == "all"):
                    if any(g in [assigned_group, group_name] for g in [f"G{i}" for i in range(1, NUM_GROUPS + 1)]):
                        return False
            
        # 2. Check for consecutive slots constraint (max 3 consecutive)
        # This is a more accurate implementation for consecutive session checking
        def would_create_too_many_consecutive_sessions(day, slot_idx, group_to_check):
            # Get all slots for this day and group in order
            day_slots = []
            for s_idx, s in enumerate(SLOTS):
                if day == "Tuesday" and s_idx >= 3:
                    continue  # Skip afternoon slots on Tuesday
                
                # Check if slot is or will be occupied
                is_occupied = False
                if s_idx == slot_idx:
                    # This is the slot we're trying to schedule
                    is_occupied = True
                else:
                    # Check if this slot is already scheduled in the assignment
                    is_occupied = any(
                        assignment.get(v) == (day, s, r)
                        for v in assignment
                        for r in sum(ROOMS.values(), [])
                        if v.split('_')[2] == group_to_check
                    )
                
                if is_occupied:
                    day_slots.append(s_idx)
            
            # Check for consecutive slots (more than 3)
            day_slots.sort()
            consecutive = 1
            max_consecutive = 1
            
            for i in range(1, len(day_slots)):
                if day_slots[i] == day_slots[i-1] + 1:
                    consecutive += 1
                    max_consecutive = max(max_consecutive, consecutive)
                else:
                    consecutive = 1
            
            return max_consecutive > 3
        
        # Convert slot to index
        slot_idx = SLOTS.index(slot)
        
        # For each group, check consecutive slots
        if group_name == "all":
            # For lectures (affecting all groups), check all groups
            groups_to_check = [f"G{i}" for i in range(1, NUM_GROUPS + 1)]
        else:
            # For TD/TP, check only this group
            groups_to_check = [group_name]
        
        # Also check combined group schedule (lectures + group-specific sessions)
        for check_group in groups_to_check:
            # Create a "combined" group that includes both group-specific and "all" sessions
            combined_group = check_group
            if would_create_too_many_consecutive_sessions(day, slot_idx, combined_group):
                return False
        
        return True
    
    def ac3(self):
        """Run AC3 algorithm to enforce arc consistency"""
        queue = deque([(xi, xj) for xi in self.variables for xj in self.variables if xi != xj])
        
        while queue:
            xi, xj = queue.popleft()
            if self.revise(xi, xj):
                if len(self.domains[xi]) == 0:
                    return False
                for xk in self.variables:
                    if xk != xi and xk != xj:
                        queue.append((xk, xi))
        return True
    
    def revise(self, xi, xj):
        """Revise domain of xi with respect to xj"""
        revised = False
        
        # Find the session info for these variables
        xi_info = xi.split('_')
        xi_course = xi_info[0]
        xi_type = xi_info[1]
        xi_group = xi_info[2]
        xi_idx = int(xi_info[3])
        xi_session = self.sessions[xi_idx]
        
        xj_info = xj.split('_')
        xj_course = xj_info[0]
        xj_type = xj_info[1]
        xj_group = xj_info[2]
        xj_idx = int(xj_info[3])
        xj_session = self.sessions[xj_idx]
        
        to_remove = []
        for xi_val in self.domains[xi]:
            xi_day, xi_slot, xi_room = xi_val
            
            # If there exists no value in xj's domain that is consistent with xi_val,
            # then remove xi_val from xi's domain
            if xj in self.assignment:
                xj_val = self.assignment[xj]
                xj_day, xj_slot, xj_room = xj_val
                
                # Check conflicts only if same day and time slot
                if xi_day == xj_day and xi_slot == xj_slot:
                    conflict = False
                    
                    # Room conflict
                    if xi_room == xj_room:
                        conflict = True
                    
                    # Teacher conflict
                    if xi_session["teacher"] == xj_session["teacher"]:
                        conflict = True
                    
                    # Group conflict (for non-lecture sessions)
                    if xi_group == xj_group and xi_group != "all" and xj_group != "all":
                        conflict = True
                    
                    # Lecture and group-specific session conflict
                    if (xi_group == "all" and xj_group != "all") or (xi_group != "all" and xj_group == "all"):
                        if any(g in [xi_group, xj_group] for g in [f"G{i}" for i in range(1, NUM_GROUPS + 1)]):
                            conflict = True
                    
                    if conflict:
                        to_remove.append(xi_val)
                        revised = True
            else:
                # Check if there's at least one value in xj's domain that doesn't conflict
                all_conflict = True
                for xj_val in self.domains[xj]:
                    xj_day, xj_slot, xj_room = xj_val
                    
                    # Check conflicts only if same day and time slot
                    if xi_day == xj_day and xi_slot == xj_slot:
                        conflict = False
                        
                        # Room conflict
                        if xi_room == xj_room:
                            conflict = True
                        
                        # Teacher conflict
                        if xi_session["teacher"] == xj_session["teacher"]:
                            conflict = True
                        
                        # Group conflict (for non-lecture sessions)
                        if xi_group == xj_group and xi_group != "all" and xj_group != "all":
                            conflict = True
                        
                        # Lecture and group-specific session conflict
                        if (xi_group == "all" and xj_group != "all") or (xi_group != "all" and xj_group == "all"):
                            if any(g in [xi_group, xj_group] for g in [f"G{i}" for i in range(1, NUM_GROUPS + 1)]):
                                conflict = True
                        
                        if not conflict:
                            all_conflict = False
                            break
                    else:
                        all_conflict = False
                        break
                
                if all_conflict:
                    to_remove.append(xi_val)
                    revised = True
        
        for val in to_remove:
            self.domains[xi].remove(val)
            
        return revised
    
    def select_unassigned_variable(self, assignment):
        """Select variable with Minimum Remaining Values (MRV) heuristic"""
        unassigned = [v for v in self.variables if v not in assignment]
        if not unassigned:
            return None
        
        # Use MRV heuristic: choose variable with fewest legal values in its domain
        return min(unassigned, key=lambda var: len([val for val in self.domains[var] 
                                               if self.is_consistent(var, val, assignment)]))
    
    def order_domain_values(self, var, assignment):
        """Order domain values using Least Constraining Value (LCV) heuristic"""
        def count_conflicts(value):
            # Count how many values would be eliminated from other variables' domains if we assign this value
            conflict_count = 0
            for other_var in [v for v in self.variables if v not in assignment and v != var]:
                for other_val in self.domains[other_var]:
                    # Create a temporary assignment to check consistency
                    temp_assignment = assignment.copy()
                    temp_assignment[var] = value
                    if not self.is_consistent(other_var, other_val, temp_assignment):
                        conflict_count += 1
            return conflict_count
        
        # Return values sorted by the number of conflicts they cause
        return sorted(self.domains[var], key=count_conflicts)
    
    def backtrack(self, assignment=None):
        """Backtracking search with MRV and LCV heuristics"""
        if assignment is None:
            assignment = {}
            
        # Check if assignment is complete
        if len(assignment) == len(self.variables):
            return assignment
        
        # Select unassigned variable using MRV
        var = self.select_unassigned_variable(assignment)
        if var is None:
            return None
            
        # Try each value in the domain, ordered by LCV
        for value in self.order_domain_values(var, assignment):
            if self.is_consistent(var, value, assignment):
                # Add {var = value} to assignment
                assignment[var] = value
                self.assignment = assignment
                
                # Recursive call
                result = self.backtrack(assignment)
                if result is not None:
                    return result
                
                # If we get here, this assignment didn't work
                del assignment[var]
                
        return None

# Function to convert solution to a timetable format
def solution_to_timetable(solution, sessions):
    if not solution:
        return None
    
    # Initialize empty timetable for each group plus common lectures
    timetable = {}
    for group_idx in range(1, NUM_GROUPS + 1):
        group_name = f"G{group_idx}"
        timetable[group_name] = {day: {slot: [] for slot in SLOTS} for day in DAYS}
    
    # Fill timetable with assigned sessions
    for var, (day, slot, room) in solution.items():
        var_parts = var.split('_')
        course = var_parts[0]
        session_type = var_parts[1]
        group = var_parts[2]
        session_idx = int(var_parts[3])
        session = sessions[session_idx]
        
        session_info = {
            "course": course,
            "type": session_type,
            "teacher": session["teacher"],
            "room": room
        }
        
        if group == "all":
            # Add lecture to all groups' timetables
            for group_idx in range(1, NUM_GROUPS + 1):
                group_name = f"G{group_idx}"
                timetable[group_name][day][slot].append(session_info)
        else:
            # Add TD/TP to specific group timetable
            timetable[group][day][slot].append(session_info)
    
    return timetable

# Display timetable as a DataFrame for a specific group
def display_group_timetable(timetable, group):
    if not timetable or group not in timetable:
        st.error(f"No feasible timetable found for group {group}. Try relaxing some constraints.")
        return
    
    # Create DataFrame for better visualization
    timetable_df = pd.DataFrame(index=SLOTS, columns=DAYS)
    
    for day in DAYS:
        for slot in SLOTS:
            # Skip afternoon slots for Tuesday
            if day == "Tuesday" and SLOTS.index(slot) >= 3:
                timetable_df.loc[slot, day] = "Not Available"
                continue
                
            cell_content = ""
            for session in timetable[group].get(day, {}).get(slot, []):
                session_type_map = {"lecture": "Lecture", "td": "TD", "tp": "TP"}
                session_type = session_type_map.get(session["type"], session["type"])
                
                cell_content += f"{session['course']} ({session_type})\n{session['teacher']}\n{session['room']}\n\n"
            
            timetable_df.loc[slot, day] = cell_content.strip() if cell_content else ""
    
    # Display the timetable
    st.dataframe(timetable_df, height=400, use_container_width=True)

# Count and display teacher workdays
def display_teacher_workdays(timetable):
    if not timetable:
        return
    
    # Count teacher workdays across all groups
    teacher_days = {}
    
    for group in timetable:
        for day in DAYS:
            for slot in SLOTS:
                if day == "Tuesday" and SLOTS.index(slot) >= 3:
                    continue
                    
                for session in timetable[group].get(day, {}).get(slot, []):
                    teacher = session["teacher"]
                    
                    # Only count shared sessions (lectures) once
                    if session["type"] == "lecture" and group != "G1":
                        continue
                    
                    if teacher not in teacher_days:
                        teacher_days[teacher] = set()
                    teacher_days[teacher].add(day)
    
    # Display teacher workdays
    st.subheader("Teacher Workdays")
    teacher_df = pd.DataFrame({
        "Teacher": list(teacher_days.keys()),
        "Work Days": [", ".join(days) for days in teacher_days.values()],
        "Number of Work Days": [len(days) for days in teacher_days.values()]
    })
    st.dataframe(teacher_df, use_container_width=True)
    
    # Check soft constraint: maximum 2 workdays per teacher
    violations = sum(1 for days in teacher_days.values() if len(days) > 2)
    if violations > 0:
        st.warning(f"{violations} teachers have more than 2 workdays (soft constraint violated)")
    else:
        st.success("All teachers have at most 2 workdays (soft constraint satisfied)")

# Main Streamlit app
def main():
    st.sidebar.header("Controls")
    
    # Create a button to generate a new timetable
    if st.sidebar.button("Generate Timetable", type="primary"):
        with st.spinner("Generating timetable... This may take a while..."):
            # Create and solve the CSP
            csp = TimeTableCSP()
            
            # Run AC3 as preprocessing
            st.sidebar.info("Running AC3 preprocessing...")
            csp.ac3()
            
            # Run backtracking search
            st.sidebar.info("Running backtracking search...")
            solution = csp.backtrack()
            
            # Convert solution to timetable format
            timetable = solution_to_timetable(solution, csp.sessions)
            
            st.session_state.timetable = timetable
            st.session_state.sessions = csp.sessions
    
    # Display the timetable if it exists in session state
    if 'timetable' in st.session_state and 'sessions' in st.session_state:
        # Create tabs for each group
        tabs = st.tabs([f"Group {i}" for i in range(1, NUM_GROUPS + 1)])
        
        # Display each group's timetable in its tab
        for i, tab in enumerate(tabs):
            group_name = f"G{i+1}"
            with tab:
                st.subheader(f"Timetable for {group_name}")
                display_group_timetable(st.session_state.timetable, group_name)
        
        # Display teacher workdays
        display_teacher_workdays(st.session_state.timetable)

if __name__ == "__main__":
    main()