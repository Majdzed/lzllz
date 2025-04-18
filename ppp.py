
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, ListFlowable, ListItem
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER

# Create the PDF document
doc = SimpleDocTemplate('timetable_csp_report.pdf', pagesize=letter)
styles = getSampleStyleSheet()

# Create custom styles
title_style = styles['Title']
heading1_style = styles['Heading1']
heading2_style = styles['Heading2']
normal_style = styles['Normal']
normal_style.alignment = TA_JUSTIFY

bullet_style = ParagraphStyle(
    'BulletPoint',
    parent=normal_style,
    leftIndent=20,
    spaceBefore=2,
    spaceAfter=2
)

code_style = ParagraphStyle(
    'Code',
    parent=normal_style,
    fontName='Courier',
    fontSize=9,
    leftIndent=20
)

# Content elements
elements = []

# Title
elements.append(Paragraph('Timetable Scheduling Problem: CSP Analysis', title_style))
elements.append(Spacer(1, 12))

# Introduction
elements.append(Paragraph('Introduction', heading1_style))
elements.append(Paragraph(
    'This report provides an analysis of the Constraint Satisfaction Problem (CSP) approach used to solve the 1CS '
    'timetable scheduling problem. The problem involves scheduling various courses across multiple groups, '
    'ensuring that all constraints are satisfied to create a valid and efficient timetable.',
    normal_style
))
elements.append(Spacer(1, 12))

# Variables
elements.append(Paragraph('Variables', heading1_style))
elements.append(Paragraph(
    'The variables in this CSP represent the individual sessions that need to be scheduled. Each variable is uniquely '
    'identified by a combination of:',
    normal_style
))

variables_list = [
    Paragraph('Course name (e.g., \"Sécurité\", \"Artificial Intelligence\")', bullet_style),
    Paragraph('Session type (lecture, td, tp)', bullet_style),
    Paragraph('Group (\"all\" for lectures, or specific group identifiers like \"G1\", \"G2\", etc.)', bullet_style),
    Paragraph('Session index (to distinguish between multiple sessions of the same type)', bullet_style)
]
elements.append(ListFlowable(variables_list, bulletType='bullet', start='•'))

elements.append(Paragraph(
    'Variables are represented in the format: \"CourseName_SessionType_Group_Index\". For example:',
    normal_style
))

examples = [
    Paragraph('\"Sécurité_lecture_all_0\": Represents a lecture for the Sécurité course for all groups', bullet_style),
    Paragraph('\"Artificial Intelligence_td_G1_25\": Represents a TD session for the AI course for Group 1', bullet_style)
]
elements.append(ListFlowable(examples, bulletType='bullet', start='•'))
elements.append(Spacer(1, 12))

# Domains
elements.append(Paragraph('Domains', heading1_style))
elements.append(Paragraph(
    'The domain of each variable consists of all possible day-slot-room combinations where the session can be scheduled. '
    'Each value in a domain is a tuple of (day, time slot, room), where:',
    normal_style
))

domain_list = [
    Paragraph('Day: One of \"Sunday\", \"Monday\", \"Tuesday\", \"Wednesday\", \"Thursday\"', bullet_style),
    Paragraph('Time slot: One of \"08:30-10:00\", \"10:10-11:40\", \"11:45-13:15\", \"13:20-14:50\", \"15:00-16:30\"', bullet_style),
    Paragraph('Room: A specific room depending on the session type (Lecture Hall, TD Room, or TP Lab)', bullet_style)
]
elements.append(ListFlowable(domain_list, bulletType='bullet', start='•'))

elements.append(Paragraph('Domain Restrictions:', heading2_style))
domain_restrictions = [
    Paragraph('Tuesday domains only include morning slots (first 3 time slots)', bullet_style),
    Paragraph('Lecture sessions can only be scheduled in Lecture Halls', bullet_style),
    Paragraph('TD sessions can only be scheduled in TD Rooms', bullet_style),
    Paragraph('TP sessions can only be scheduled in TP Labs', bullet_style)
]
elements.append(ListFlowable(domain_restrictions, bulletType='bullet', start='•'))
elements.append(Spacer(1, 12))

# Constraints
elements.append(Paragraph('Constraints', heading1_style))
elements.append(Paragraph(
    'The timetable scheduling problem includes both hard and soft constraints. Hard constraints must be satisfied for a valid solution, '
    'while soft constraints are preferred but can be violated if necessary.',
    normal_style
))

elements.append(Paragraph('Hard Constraints:', heading2_style))
hard_constraints = [
    Paragraph('No room conflicts: Two sessions cannot be scheduled in the same room at the same time', bullet_style),
    Paragraph('No teacher conflicts: A teacher cannot teach multiple sessions at the same time', bullet_style),
    Paragraph('No group conflicts: A group cannot attend multiple sessions at the same time', bullet_style),
    Paragraph('Lecture and group-specific session conflicts: When a lecture is scheduled for all groups, no group-specific '
              'sessions can be scheduled at the same time', bullet_style),
    Paragraph('Maximum consecutive sessions: A group cannot have more than 3 consecutive sessions in a day', bullet_style),
    Paragraph('Room type matching: Lectures must be in Lecture Halls, TD in TD Rooms, and TP in TP Labs', bullet_style),
    Paragraph('Tuesday afternoon unavailability: No sessions can be scheduled on Tuesday afternoons', bullet_style)
]
elements.append(ListFlowable(hard_constraints, bulletType='bullet', start='•'))

elements.append(Paragraph('Soft Constraints:', heading2_style))
soft_constraints = [
    Paragraph('Teacher workdays: Teachers should not have to come to school more than 2 days per week', bullet_style)
]
elements.append(ListFlowable(soft_constraints, bulletType='bullet', start='•'))
elements.append(Spacer(1, 12))

# Backtracking approach
elements.append(Paragraph('Backtracking Approach', heading1_style))
elements.append(Paragraph(
    'The solution uses a backtracking search algorithm with several enhancements to efficiently find a valid timetable. '
    'The key components of this approach are:',
    normal_style
))

elements.append(Paragraph('1. Preprocessing with AC3 (Arc Consistency)', heading2_style))
elements.append(Paragraph(
    'Before starting the backtracking search, the AC3 algorithm is used to enforce arc consistency in the constraint graph. '
    'This preprocessing step helps to reduce the domain sizes by eliminating values that are guaranteed to violate constraints, '
    'making the subsequent backtracking search more efficient.',
    normal_style
))

elements.append(Paragraph('2. Variable Selection Heuristic (MRV)', heading2_style))
elements.append(Paragraph(
    'The Minimum Remaining Values (MRV) heuristic is used to choose which variable to assign next during the backtracking search. '
    'MRV selects the variable with the fewest legal values in its domain, which helps to identify potential failures earlier in the search process.',
    normal_style
))
elements.append(Paragraph(
    'Implementation:',
    normal_style
))
elements.append(Paragraph(
    'unassigned = [v for v in self.variables if v not in assignment]\\n'
    'return min(unassigned, key=lambda var: len([val for val in self.domains[var] if self.is_consistent(var, val, assignment)]))',
    code_style
))

elements.append(Paragraph('3. Value Ordering Heuristic (LCV)', heading2_style))
elements.append(Paragraph(
    'The Least Constraining Value (LCV) heuristic is used to decide the order in which values are tried for a selected variable. '
    'LCV orders values by the number of conflicts they cause with other unassigned variables, trying values that rule out the '
    'fewest options for neighboring variables first.',
    normal_style
))
elements.append(Paragraph(
    'Implementation:',
    normal_style
))
elements.append(Paragraph(
    'def count_conflicts(value):\\n'
    '    # Count how many values would be eliminated from other variables\' domains if we assign this value\\n'
    '    conflict_count = 0\\n'
    '    for other_var in [v for v in self.variables if v not in assignment and v != var]:\\n'
    '        for other_val in self.domains[other_var]:\\n'
    '            # Create a temporary assignment to check consistency\\n'
    '            temp_assignment = assignment.copy()\\n'
    '            temp_assignment[var] = value\\n'
    '            if not self.is_consistent(other_var, other_val, temp_assignment):\\n'
    '                conflict_count += 1\\n'
    '    return conflict_count\\n\\n'
    '# Return values sorted by the number of conflicts they cause\\n'
    'return sorted(self.domains[var], key=count_conflicts)',
    code_style
))

elements.append(Paragraph('4. Constraint Checking', heading2_style))
elements.append(Paragraph(
    'The is_consistent function checks if assigning a specific value to a variable violates any constraints with the current '
    'partial assignment. It checks for conflicts in room usage, teacher availability, group availability, and the '
    'maximum consecutive sessions constraint.',
    normal_style
))
elements.append(Paragraph(
    'The consecutive sessions constraint is handled with special care to ensure no group has more than 3 consecutive sessions. '
    'The algorithm keeps track of the session slots for each group on each day and prevents assignments that would create too many consecutive sessions.',
    normal_style
))

elements.append(Paragraph('5. Backtracking Search Algorithm', heading2_style))
elements.append(Paragraph(
    'The main backtracking algorithm works as follows:',
    normal_style
))

backtracking_steps = [
    Paragraph('If all variables have been assigned, return the complete assignment as the solution', bullet_style),
    Paragraph('Select an unassigned variable using the MRV heuristic', bullet_style),
    Paragraph('Try assigning values from the variable\'s domain, ordered by the LCV heuristic', bullet_style),
    Paragraph('For each value, check if the assignment is consistent with all constraints', bullet_style),
    Paragraph('If consistent, add the assignment and recursively continue with the remaining variables', bullet_style),
    Paragraph('If a recursive call returns a solution, return that solution', bullet_style),
    Paragraph('If no value leads to a solution, remove the current variable\'s assignment (backtrack) and return failure', bullet_style)
]
elements.append(ListFlowable(backtracking_steps, bulletType='bullet', start='•'))
elements.append(Spacer(1, 12))

# Solutions and Output
elements.append(Paragraph('Solution and Output', heading1_style))
elements.append(Paragraph(
    'When a valid solution is found, it is converted into a timetable format that shows the schedule for each group. '
    'The solution includes:',
    normal_style
))

solution_points = [
    Paragraph('A complete assignment of each course session to a specific day, time slot, and room', bullet_style),
    Paragraph('Separate timetables for each group (G1 through G6)', bullet_style),
    Paragraph('Analysis of teacher workdays to check the soft constraint of maximum 2 workdays per teacher', bullet_style)
]
elements.append(ListFlowable(solution_points, bulletType='bullet', start='•'))
elements.append(Spacer(1, 12))

# Conclusion
elements.append(Paragraph('Conclusion', heading1_style))
elements.append(Paragraph(
    'The timetable scheduling problem is solved using a constraint satisfaction approach with backtracking search. '
    'The implementation uses several heuristics (MRV and LCV) and preprocessing (AC3) to improve efficiency. '
    'The complexity of this problem arises from the many constraints that must be satisfied simultaneously, including '
    'room, teacher, and group availability, as well as the maximum consecutive sessions constraint.',
    normal_style
))
elements.append(Paragraph(
    'The backtracking search systematically explores the space of possible assignments until it finds a valid solution '
    'or determines that no solution exists. When a solution is found, it is presented as a timetable for each group, '
    'showing the course, session type, teacher, and room for each time slot.',
    normal_style
))

# Build the PDF
doc.build(elements)
print('PDF report generated: timetable_csp_report.pdf')
