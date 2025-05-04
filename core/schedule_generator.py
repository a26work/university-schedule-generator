"""
University Schedule Generator Core Algorithm
-------------------------------------------
This module contains the core algorithm for generating university class schedules based on a set of constraints and preferences.
"""
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, List, Set, Tuple, Optional, Any

_logger = logging.getLogger(__name__)


class TimeSlot:
    """Represents a time slot with start and end times."""

    def __init__(self, day: str, start_time: str, end_time: str):
        """
        Initialize a time slot.

        Args:
            day: Day of the week (e.g., 'Monday')
            start_time: Start time in format 'HH:MM'
            end_time: End time in format 'HH:MM'
        """
        self.day = day
        self.start_time = start_time
        self.end_time = end_time

    def __str__(self):
        return f"{self.day} {self.start_time} - {self.end_time}"

    def overlaps(self, other: 'TimeSlot') -> bool:
        """
        Check if this time slot overlaps with another.

        Args:
            other: Another time slot to check against

        Returns:
            True if the time slots overlap, False otherwise
        """
        if self.day != other.day:
            return False

        self_start = datetime.strptime(self.start_time, "%H:%M")
        self_end = datetime.strptime(self.end_time, "%H:%M")
        other_start = datetime.strptime(other.start_time, "%H:%M")
        other_end = datetime.strptime(other.end_time, "%H:%M")

        # Check if one slot ends before the other starts
        if self_end <= other_start or other_end <= self_start:
            return False

        return True


class ScheduleSection:
    """Represents a scheduled course section with all necessary details."""

    def __init__(self,
                 course_id: str,
                 section_number: int,
                 professor_id: str,
                 hall_id: str,
                 time_slot: TimeSlot):
        """
        Initialize a schedule section.

        Args:
            course_id: Course identifier
            section_number: Section number for this course
            professor_id: Professor assigned to this section
            hall_id: Hall assigned to this section
            time_slot: Time slot assigned to this section
        """
        self.course_id = course_id
        self.section_number = section_number
        self.professor_id = professor_id
        self.hall_id = hall_id
        self.time_slot = time_slot

    def __str__(self):
        return (f"Course: {self.course_id}, Section: {self.section_number}, "
                f"Professor: {self.professor_id}, Hall: {self.hall_id}, "
                f"Time: {self.time_slot}")


class ScheduleGenerator:
    """
    Core scheduling algorithm that generates university class schedules based on
    provided constraints and preferences.
    """

    def __init__(self):
        """Initialize the schedule generator."""
        self.halls = []
        self.school_days = []
        self.departments = []
        self.professors = []
        self.courses = []
        self.level_courses = {}
        self.department_courses = {}
        self.professor_specialties = {}
        self.professor_preferred_courses = {}
        self.professor_preferred_times = {}
        self.course_preferred_times = {}
        self.restricted_times = []
        self.days_with_hours = {}
        self.course_lecture_durations = {}
        self.course_sections_count = {}

    def load_data(self, data: Dict[str, Any]) -> None:
        """
        Load input data for scheduling.

        Args:
            data: Dictionary containing all necessary data for scheduling
        """
        self.halls = data.get('halls', [])
        self.school_days = data.get('school_days', [])
        self.departments = data.get('departments', [])
        self.professors = data.get('professors', [])
        self.courses = data.get('courses', [])
        self.level_courses = data.get('level_courses', {})
        self.department_courses = data.get('department_courses', {})
        self.professor_specialties = data.get('professor_specialties', {})
        self.professor_preferred_courses = data.get('professor_preferred_courses', {})
        self.professor_preferred_times = data.get('professor_preferred_times', {})
        self.course_preferred_times = data.get('course_preferred_times', {})
        self.restricted_times = data.get('restricted_times', [])
        self.days_with_hours = data.get('days_with_hours', {})
        self.course_lecture_durations = data.get('course_lecture_durations', {})
        self.course_sections_count = data.get('course_sections_count', {})

    def _generate_time_slots(self, course_id: str) -> List[TimeSlot]:
        """
        Generate all possible time slots for a course.

        Args:
            course_id: Course identifier

        Returns:
            List of possible time slots for the course
        """
        all_time_slots = []
        lecture_duration = self.course_lecture_durations.get(course_id, 60)  # Default 60 minutes

        for day, hours in self.days_with_hours.items():
            start_hour, start_minute = map(int, hours['start'].split(':'))
            end_hour, end_minute = map(int, hours['end'].split(':'))

            start_time = datetime.strptime(f"{start_hour}:{start_minute}", "%H:%M")
            end_time = datetime.strptime(f"{end_hour}:{end_minute}", "%H:%M")

            # Calculate the number of minutes between start and end
            total_minutes = (end_time - start_time).seconds // 60

            # Generate time slots with the course's lecture duration
            # Add 5 minutes break between potential slots
            current_time = start_time
            while current_time + timedelta(minutes=lecture_duration) <= end_time:
                slot_start = current_time.strftime("%H:%M")
                slot_end = (current_time + timedelta(minutes=lecture_duration)).strftime("%H:%M")

                # Create a time slot
                time_slot = TimeSlot(day, slot_start, slot_end)

                # Check if this time slot is restricted
                is_restricted = False
                for restricted in self.restricted_times:
                    restricted_slot = TimeSlot(
                        restricted['day'],
                        restricted['start_time'],
                        restricted['end_time']
                    )
                    if time_slot.overlaps(restricted_slot):
                        is_restricted = True
                        break

                if not is_restricted:
                    all_time_slots.append(time_slot)

                # Move to the next potential start time (add lecture duration + break)
                current_time += timedelta(minutes=lecture_duration + 5)

        return all_time_slots

    def _is_professor_available(self,
                                professor_id: str,
                                time_slot: TimeSlot,
                                existing_schedule: List[ScheduleSection]) -> bool:
        """
        Check if a professor is available at a given time slot.

        Args:
            professor_id: Professor identifier
            time_slot: Time slot to check
            existing_schedule: Existing schedule sections

        Returns:
            True if the professor is available, False otherwise
        """
        # Check professor's preferred times if specified
        if professor_id in self.professor_preferred_times:
            preferred_times = self.professor_preferred_times[professor_id]
            if preferred_times:
                is_preferred = False
                for preferred in preferred_times:
                    preferred_slot = TimeSlot(
                        preferred['day'],
                        preferred['start_time'],
                        preferred['end_time']
                    )
                    # Check if the time slot is within the preferred time frame
                    if time_slot.day == preferred_slot.day:
                        time_slot_start = datetime.strptime(time_slot.start_time, "%H:%M")
                        time_slot_end = datetime.strptime(time_slot.end_time, "%H:%M")
                        preferred_start = datetime.strptime(preferred_slot.start_time, "%H:%M")
                        preferred_end = datetime.strptime(preferred_slot.end_time, "%H:%M")

                        if time_slot_start >= preferred_start and time_slot_end <= preferred_end:
                            is_preferred = True
                            break

                if not is_preferred:
                    return False

        # Check if the professor is already scheduled during this time slot
        for section in existing_schedule:
            if section.professor_id == professor_id and section.time_slot.overlaps(time_slot):
                return False

        return True

    def _is_hall_available(self,
                           hall_id: str,
                           time_slot: TimeSlot,
                           existing_schedule: List[ScheduleSection]) -> bool:
        """
        Check if a hall is available at a given time slot.

        Args:
            hall_id: Hall identifier
            time_slot: Time slot to check
            existing_schedule: Existing schedule sections

        Returns:
            True if the hall is available, False otherwise
        """
        for section in existing_schedule:
            if section.hall_id == hall_id and section.time_slot.overlaps(time_slot):
                return False

        return True

    def _find_suitable_professor(self,
                                 course_id: str,
                                 time_slot: TimeSlot,
                                 existing_schedule: List[ScheduleSection]) -> Optional[str]:
        """
        Find a suitable professor for a course at a given time slot.

        Args:
            course_id: Course identifier
            time_slot: Time slot to check
            existing_schedule: Existing schedule sections

        Returns:
            Professor identifier if found, None otherwise
        """
        suitable_professors = []

        # First, check professors with this course as a preferred course
        for professor_id, preferred_courses in self.professor_preferred_courses.items():
            if course_id in preferred_courses and self._is_professor_available(professor_id, time_slot,
                                                                               existing_schedule):
                # Check if professor has the right specialty for this course
                course_dept = None
                for dept, courses in self.department_courses.items():
                    if course_id in courses:
                        course_dept = dept
                        break

                if course_dept and professor_id in self.professor_specialties:
                    if course_dept in self.professor_specialties[professor_id]:
                        suitable_professors.append(professor_id)

        # If no preferred professors found, try all professors with the right specialty
        if not suitable_professors:
            course_dept = None
            for dept, courses in self.department_courses.items():
                if course_id in courses:
                    course_dept = dept
                    break

            if course_dept:
                for professor_id, specialties in self.professor_specialties.items():
                    if course_dept in specialties and self._is_professor_available(professor_id, time_slot,
                                                                                   existing_schedule):
                        suitable_professors.append(professor_id)

        # If still no suitable professors, try any available professor
        if not suitable_professors:
            for professor_id in self.professors:
                if self._is_professor_available(professor_id, time_slot, existing_schedule):
                    suitable_professors.append(professor_id)

        # Return a random professor from the suitable ones (for load balancing)
        if suitable_professors:
            return random.choice(suitable_professors)

        return None

    def _find_suitable_hall(self,
                            time_slot: TimeSlot,
                            existing_schedule: List[ScheduleSection]) -> Optional[str]:
        """
        Find a suitable hall for a given time slot.

        Args:
            time_slot: Time slot to check
            existing_schedule: Existing schedule sections

        Returns:
            Hall identifier if found, None otherwise
        """
        available_halls = []

        for hall_id in self.halls:
            if self._is_hall_available(hall_id, time_slot, existing_schedule):
                available_halls.append(hall_id)

        # Return a random hall from the available ones
        if available_halls:
            return random.choice(available_halls)

        return None

    def _are_sections_well_distributed(self,
                                       course_id: str,
                                       new_time_slot: TimeSlot,
                                       existing_schedule: List[ScheduleSection]) -> bool:
        """
        Check if adding a new section would result in a well-distributed schedule.

        Args:
            course_id: Course identifier
            new_time_slot: New time slot to check
            existing_schedule: Existing schedule sections

        Returns:
            True if the sections would be well distributed, False otherwise
        """
        # Get existing sections for this course
        course_sections = [
            section for section in existing_schedule
            if section.course_id == course_id
        ]

        # Check if we already have a section on the same day
        same_day_sections = [
            section for section in course_sections
            if section.time_slot.day == new_time_slot.day
        ]

        # If there are multiple sections and we already have one on this day,
        # prefer a different day for better distribution
        if course_sections and same_day_sections and len(self.school_days) > len(same_day_sections):
            return False

        return True

    def _is_level_schedule_balanced(self,
                                    level: str,
                                    course_id: str,
                                    new_time_slot: TimeSlot,
                                    existing_schedule: List[ScheduleSection]) -> bool:
        """
        Check if adding a new section would result in a balanced schedule for a level.

        Args:
            level: Level identifier
            course_id: Course identifier
            new_time_slot: New time slot to check
            existing_schedule: Existing schedule sections

        Returns:
            True if the level schedule would be balanced, False otherwise
        """
        # Get all courses for this level
        level_course_ids = self.level_courses.get(level, [])

        if course_id not in level_course_ids:
            return True  # Not a course for this level

        # Count sections per day for this level
        day_counts = {day: 0 for day in self.school_days}

        for section in existing_schedule:
            if section.course_id in level_course_ids:
                day_counts[section.time_slot.day] += 1

        # Add the new section
        day_counts[new_time_slot.day] += 1

        # Check if the distribution is reasonably balanced
        max_count = max(day_counts.values())
        min_count = min(day_counts.values())

        # Allow a difference of at most 2 sections between days
        return max_count - min_count <= 2

    def _evaluate_time_preference(self, course_id: str, time_slot: TimeSlot) -> float:
        """
        Evaluate how well a time slot matches the preferred time for a course.

        Args:
            course_id: Course identifier
            time_slot: Time slot to evaluate

        Returns:
            Score between 0 and 1, higher is better
        """
        if course_id not in self.course_preferred_times:
            return 0.5  # Neutral score for no preference

        preference = self.course_preferred_times[course_id]

        # Convert time to hours as float for comparison
        hours, minutes = map(int, time_slot.start_time.split(':'))
        time_as_hours = hours + minutes / 60

        # Define time ranges for early, middle, late
        day_start = self.days_with_hours.get(time_slot.day, {}).get('start', '08:00')
        day_end = self.days_with_hours.get(time_slot.day, {}).get('end', '18:00')

        start_hours, start_minutes = map(int, day_start.split(':'))
        end_hours, end_minutes = map(int, day_end.split(':'))

        day_start_hours = start_hours + start_minutes / 60
        day_end_hours = end_hours + end_minutes / 60
        day_duration = day_end_hours - day_start_hours

        early_end = day_start_hours + day_duration / 3
        middle_end = day_start_hours + 2 * day_duration / 3

        # Check which part of the day this time slot falls into
        time_of_day = None
        if time_as_hours < early_end:
            time_of_day = 'early'
        elif time_as_hours < middle_end:
            time_of_day = 'middle'
        else:
            time_of_day = 'late'

        # Return score based on preference match
        if preference == time_of_day:
            return 1.0
        else:
            return 0.2

    def generate_schedule(self) -> List[ScheduleSection]:
        """
        Generate an optimal class schedule based on the provided data and constraints.

        Returns:
            List of scheduled course sections
        """
        schedule = []

        # Sort courses by number of sections (decreasing) to schedule the most constrained courses first
        sorted_courses = sorted(
            self.courses,
            key=lambda c: self.course_sections_count.get(c, 1),
            reverse=True
        )

        for course_id in sorted_courses:
            num_sections = self.course_sections_count.get(course_id, 1)
            course_level = None

            # Find the level for this course
            for level, courses in self.level_courses.items():
                if course_id in courses:
                    course_level = level
                    break

            # Generate all possible time slots for this course
            possible_time_slots = self._generate_time_slots(course_id)

            # Shuffle time slots to avoid bias
            random.shuffle(possible_time_slots)

            sections_created = 0
            while sections_created < num_sections and possible_time_slots:
                best_slot = None
                best_score = -1
                best_professor = None
                best_hall = None

                for time_slot in possible_time_slots:
                    # Skip if we already have a section for this course on the same day
                    # and we want to distribute sections across different days
                    if not self._are_sections_well_distributed(course_id, time_slot, schedule):
                        continue

                    # Skip if adding this would make the level schedule unbalanced
                    if course_level and not self._is_level_schedule_balanced(
                            course_level, course_id, time_slot, schedule
                    ):
                        continue

                    # Find a suitable professor
                    professor_id = self._find_suitable_professor(course_id, time_slot, schedule)
                    if not professor_id:
                        continue

                    # Find a suitable hall
                    hall_id = self._find_suitable_hall(time_slot, schedule)
                    if not hall_id:
                        continue

                    # Calculate score based on time preference
                    score = self._evaluate_time_preference(course_id, time_slot)

                    if score > best_score:
                        best_score = score
                        best_slot = time_slot
                        best_professor = professor_id
                        best_hall = hall_id

                if best_slot:
                    # Create a new section with the best options
                    section = ScheduleSection(
                        course_id=course_id,
                        section_number=sections_created + 1,
                        professor_id=best_professor,
                        hall_id=best_hall,
                        time_slot=best_slot
                    )

                    schedule.append(section)
                    sections_created += 1

                    # Remove the used time slot from possibilities
                    possible_time_slots.remove(best_slot)
                else:
                    # If we couldn't find a suitable slot, break and log a warning
                    _logger.warning(
                        f"Could not schedule all sections for course {course_id}. "
                        f"Scheduled {sections_created} out of {num_sections}."
                    )
                    break

        return schedule

    def optimize_schedule(self, initial_schedule: List[ScheduleSection]) -> List[ScheduleSection]:
        """
        Optimize an existing schedule to improve professor and student efficiency.

        Args:
            initial_schedule: Initial schedule to optimize

        Returns:
            Optimized schedule
        """
        # This is a simplified optimization that could be expanded based on needs
        optimized_schedule = initial_schedule.copy()

        # Group sections by professor
        professor_sections = {}
        for section in optimized_schedule:
            if section.professor_id not in professor_sections:
                professor_sections[section.professor_id] = []
            professor_sections[section.professor_id].append(section)

        # Try to reduce the number of days a professor has to come to work
        for professor_id, sections in professor_sections.items():
            if len(sections) <= 1:
                continue  # No optimization needed

            # Group sections by day
            days_schedule = {}
            for section in sections:
                day = section.time_slot.day
                if day not in days_schedule:
                    days_schedule[day] = []
                days_schedule[day].append(section)

            # If a professor has to come for just one class on a certain day,
            # try to move it to another day (if possible)
            for day, day_sections in list(days_schedule.items()):
                if len(day_sections) != 1:
                    continue  # Only optimize days with a single section

                section_to_move = day_sections[0]

                # Find possible time slots on days when the professor is already teaching
                target_days = [d for d in days_schedule.keys() if d != day and len(days_schedule[d]) > 0]

                if not target_days:
                    continue  # No other days to consolidate with

                for target_day in target_days:
                    # Generate possible time slots for this course on the target day
                    possible_slots = [
                        slot for slot in self._generate_time_slots(section_to_move.course_id)
                        if slot.day == target_day
                    ]

                    for new_slot in possible_slots:
                        # Create a temporary schedule without the current section
                        temp_schedule = [s for s in optimized_schedule if s != section_to_move]

                        # Check if the hall is available
                        if not self._is_hall_available(section_to_move.hall_id, new_slot, temp_schedule):
                            continue

                        # Check if the professor is available
                        if not self._is_professor_available(professor_id, new_slot, temp_schedule):
                            continue

                        # Check distribution for this course
                        if not self._are_sections_well_distributed(section_to_move.course_id, new_slot, temp_schedule):
                            continue

                        # Find level for this course
                        course_level = None
                        for level, courses in self.level_courses.items():
                            if section_to_move.course_id in courses:
                                course_level = level
                                break

                        # Check level balance
                        if course_level and not self._is_level_schedule_balanced(
                                course_level, section_to_move.course_id, new_slot, temp_schedule
                        ):
                            continue

                        # Move the section
                        optimized_schedule.remove(section_to_move)
                        new_section = ScheduleSection(
                            course_id=section_to_move.course_id,
                            section_number=section_to_move.section_number,
                            professor_id=section_to_move.professor_id,
                            hall_id=section_to_move.hall_id,
                            time_slot=new_slot
                        )
                        optimized_schedule.append(new_section)

                        # Update the professor's schedule
                        days_schedule[day].remove(section_to_move)
                        if not days_schedule[day]:  # Remove empty day
                            del days_schedule[day]

                        if target_day not in days_schedule:
                            days_schedule[target_day] = []
                        days_schedule[target_day].append(new_section)

                        break  # Move on to the next section

                    if section_to_move not in optimized_schedule:
                        break  # Successfully moved this section

        return optimized_schedule

    def generate(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate an optimized class schedule based on the provided data.

        Args:
            data: Dictionary containing all necessary data for scheduling

        Returns:
            List of schedule sections as dictionaries
        """
        self.load_data(data)

        initial_schedule = self.generate_schedule()
        optimized_schedule = self.optimize_schedule(initial_schedule)

        # Convert to dictionaries for API response
        result = []
        for section in optimized_schedule:
            result.append({
                'course_id': section.course_id,
                'section_number': section.section_number,
                'professor_id': section.professor_id,
                'hall_id': section.hall_id,
                'day': section.time_slot.day,
                'start_time': section.time_slot.start_time,
                'end_time': section.time_slot.end_time
            })

        return result