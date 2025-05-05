"""
University Schedule Generator Core Algorithm - Improved Version
-------------------------------------------
This module contains the enhanced core algorithm for generating university class schedules based on a set of constraints and preferences.
"""
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, List, Set, Tuple, Optional, Any
from collections import defaultdict

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
        # Cache datetime objects for performance
        self._start_dt = datetime.strptime(start_time, "%H:%M")
        self._end_dt = datetime.strptime(end_time, "%H:%M")

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

        # Use cached datetime objects for better performance
        return not (self._end_dt <= other._start_dt or other._end_dt <= self._start_dt)

    def get_minutes_difference(self, other: 'TimeSlot') -> int:
        """
        Calculate the minutes between this time slot and another on the same day.
        Positive if other is after this slot, negative if other is before.

        Args:
            other: Another time slot on the same day

        Returns:
            Minutes difference between the slots, or None if not on same day
        """
        if self.day != other.day:
            return None

        if self._end_dt <= other._start_dt:  # This slot ends before other starts
            return int((other._start_dt - self._end_dt).total_seconds() / 60)
        elif other._end_dt <= self._start_dt:  # Other slot ends before this starts
            return -int((self._start_dt - other._end_dt).total_seconds() / 60)
        else:  # Slots overlap
            return 0


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
    Enhanced scheduling algorithm that generates university class schedules based on
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
        self.professor_courses = defaultdict(list)  # Maps professors to their courses
        self.course_professors = defaultdict(list)  # Maps courses to qualified professors
        self.restricted_time_slots = []  # Pre-computed restricted time slots

    def load_data(self, data: Dict[str, Any]) -> None:
        """
        Load input data for scheduling and precompute useful mappings.

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

        # Precompute professor-course relationships
        self._precompute_course_professor_mappings()

        # Precompute restricted time slots
        self._precompute_restricted_time_slots()

    def _precompute_course_professor_mappings(self):
        """Precompute mappings between professors and courses they can teach."""
        self.professor_courses = defaultdict(list)
        self.course_professors = defaultdict(list)

        # First, map courses to departments
        course_to_dept = {}
        for dept, courses in self.department_courses.items():
            for course in courses:
                course_to_dept[course] = dept

        # Map professors to courses they can teach based on specialty
        for professor_id, specialties in self.professor_specialties.items():
            for specialty in specialties:
                # Find all courses in this specialty's department
                for course in self.department_courses.get(specialty, []):
                    self.professor_courses[professor_id].append(course)
                    self.course_professors[course].append(professor_id)

        # Add preferred courses
        for professor_id, preferred_courses in self.professor_preferred_courses.items():
            for course in preferred_courses:
                if course not in self.professor_courses[professor_id]:
                    self.professor_courses[professor_id].append(course)
                    self.course_professors[course].append(professor_id)

    def _precompute_restricted_time_slots(self):
        """Precompute restricted time slots for faster checks."""
        self.restricted_time_slots = []
        for restricted in self.restricted_times:
            self.restricted_time_slots.append(
                TimeSlot(restricted['day'], restricted['start_time'], restricted['end_time'])
            )

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
                for restricted_slot in self.restricted_time_slots:
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
        # Check if the professor is already scheduled during this time slot
        for section in existing_schedule:
            if section.professor_id == professor_id and section.time_slot.overlaps(time_slot):
                return False

        return True

    def _is_professor_preferred_time(self, professor_id: str, time_slot: TimeSlot) -> bool:
        """
        Check if a time slot is preferred by a professor.

        Args:
            professor_id: Professor identifier
            time_slot: Time slot to check

        Returns:
            True if the time slot is within a preferred time, False otherwise
        """
        if professor_id not in self.professor_preferred_times:
            return True  # No preferences specified, so any time is okay

        preferred_times = self.professor_preferred_times[professor_id]
        if not preferred_times:
            return True  # No specific preferences, so any time is okay

        for preferred in preferred_times:
            preferred_slot = TimeSlot(
                preferred['day'],
                preferred['start_time'],
                preferred['end_time']
            )
            # Check if the time slot is within the preferred time frame
            if time_slot.day == preferred_slot.day:
                if (time_slot._start_dt >= preferred_slot._start_dt and
                    time_slot._end_dt <= preferred_slot._end_dt):
                    return True

        return False

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
        Find a suitable professor for a course at a given time slot,
        prioritizing those who prefer this course and time.

        Args:
            course_id: Course identifier
            time_slot: Time slot to check
            existing_schedule: Existing schedule sections

        Returns:
            Professor identifier if found, None otherwise
        """
        # Get all professors who can teach this course
        candidates = list(self.course_professors.get(course_id, []))

        # If no specific professors for this course, try all professors
        if not candidates:
            candidates = self.professors

        # Score and rank professors by suitability
        scored_candidates = []
        for professor_id in candidates:
            if not self._is_professor_available(professor_id, time_slot, existing_schedule):
                continue

            score = 0

            # Higher score for professors who prefer this course
            if professor_id in self.professor_preferred_courses and course_id in self.professor_preferred_courses[professor_id]:
                score += 30

            # Higher score for professors who specialize in the course's department
            course_dept = None
            for dept, courses in self.department_courses.items():
                if course_id in courses:
                    course_dept = dept
                    break

            if course_dept and professor_id in self.professor_specialties:
                if course_dept in self.professor_specialties[professor_id]:
                    score += 20

            # Higher score for professors who prefer this time slot
            if self._is_professor_preferred_time(professor_id, time_slot):
                score += 10

            # Add workload balance factor - prefer professors with fewer courses
            prof_sections = sum(1 for section in existing_schedule if section.professor_id == professor_id)
            score -= prof_sections * 2  # Penalize heavily loaded professors

            scored_candidates.append((professor_id, score))

        # Sort by score (highest first)
        scored_candidates.sort(key=lambda x: x[1], reverse=True)

        # Return the best candidate, or None if no suitable professor found
        return scored_candidates[0][0] if scored_candidates else None

    def _find_suitable_hall(self,
                            time_slot: TimeSlot,
                            existing_schedule: List[ScheduleSection]) -> Optional[str]:
        """
        Find a suitable hall for a given time slot, prioritizing balanced usage.

        Args:
            time_slot: Time slot to check
            existing_schedule: Existing schedule sections

        Returns:
            Hall identifier if found, None otherwise
        """
        # Count current usage of each hall
        hall_usage = {hall_id: 0 for hall_id in self.halls}
        for section in existing_schedule:
            hall_usage[section.hall_id] = hall_usage.get(section.hall_id, 0) + 1

        # Find available halls
        available_halls = []
        for hall_id in self.halls:
            if self._is_hall_available(hall_id, time_slot, existing_schedule):
                available_halls.append((hall_id, hall_usage[hall_id]))

        # Sort by usage (least used first)
        available_halls.sort(key=lambda x: x[1])

        # Return the least used available hall
        return available_halls[0][0] if available_halls else None

    def _are_sections_well_distributed(self,
                                       course_id: str,
                                       new_time_slot: TimeSlot,
                                       existing_schedule: List[ScheduleSection]) -> float:
        """
        Evaluate how well distributed the sections would be if a new section is added.

        Args:
            course_id: Course identifier
            new_time_slot: New time slot to check
            existing_schedule: Existing schedule sections

        Returns:
            Score between 0 and 1, higher is better distribution
        """
        # Get existing sections for this course
        course_sections = [
            section for section in existing_schedule
            if section.course_id == course_id
        ]

        # Get number of sections required for this course
        total_sections_needed = self.course_sections_count.get(course_id, 1)

        # If no sections exist yet, any day is fine
        if not course_sections:
            return 1.0

        # If only one section needed, any day is fine
        if total_sections_needed == 1:
            return 1.0

        # Count sections per day
        day_counts = defaultdict(int)
        for section in course_sections:
            day_counts[section.time_slot.day] += 1

        # Add the potential new section
        day_counts[new_time_slot.day] += 1

        # Calculate ideal distribution
        ideal_per_day = total_sections_needed / len(self.school_days)

        # Calculate variance from ideal
        variance = sum((count - ideal_per_day) ** 2 for count in day_counts.values())

        # Normalize to 0-1 score (lower variance is better)
        # Maximum possible variance is when all sections are on one day
        max_variance = (total_sections_needed - ideal_per_day) ** 2 + (len(self.school_days) - 1) * (ideal_per_day ** 2)

        if max_variance == 0:  # Edge case
            return 1.0

        distribution_score = 1.0 - (variance / max_variance)

        # Check if we can improve spacing between sections on the same day
        if day_counts[new_time_slot.day] > 1:
            # Check spacing between sections on this day
            same_day_sections = [section for section in course_sections
                                if section.time_slot.day == new_time_slot.day]

            min_spacing = float('inf')
            for section in same_day_sections:
                spacing = abs(new_time_slot.get_minutes_difference(section.time_slot) or 0)
                min_spacing = min(min_spacing, spacing)

            # Normalize spacing factor (0 is bad, 120+ minutes is ideal)
            spacing_factor = min(min_spacing / 120.0, 1.0)

            # Combine scores with spacing as a smaller factor
            distribution_score = 0.75 * distribution_score + 0.25 * spacing_factor

        return distribution_score

    def _is_level_schedule_balanced(self,
                                    level: str,
                                    course_id: str,
                                    new_time_slot: TimeSlot,
                                    existing_schedule: List[ScheduleSection]) -> float:
        """
        Evaluate how balanced the level schedule would be after adding a new section.

        Args:
            level: Level identifier
            course_id: Course identifier
            new_time_slot: New time slot to check
            existing_schedule: Existing schedule sections

        Returns:
            Score between 0 and 1, higher is better balance
        """
        # Get all courses for this level
        level_course_ids = self.level_courses.get(level, [])

        if course_id not in level_course_ids:
            return 1.0  # Not a course for this level

        # Count sections per day for this level
        day_counts = {day: 0 for day in self.school_days}

        for section in existing_schedule:
            if section.course_id in level_course_ids:
                day_counts[section.time_slot.day] += 1

        # Add the new section
        day_counts[new_time_slot.day] += 1

        # Calculate average sections per day
        avg_count = sum(day_counts.values()) / len(day_counts)

        # Calculate standard deviation
        variance = sum((count - avg_count) ** 2 for count in day_counts.values()) / len(day_counts)
        std_dev = variance ** 0.5

        # Calculate a balance score (lower std_dev is better)
        # Normalize to 0-1 range
        max_imbalance = avg_count  # Worst case: all sections on one day

        if max_imbalance == 0:  # Edge case
            return 1.0

        balance_score = 1.0 - (std_dev / max_imbalance)

        # Check for time slot distribution within the day
        # Group existing sections by time of day (morning, afternoon, evening)
        time_of_day_counts = {'morning': 0, 'afternoon': 0, 'evening': 0}

        for section in existing_schedule:
            if section.course_id in level_course_ids and section.time_slot.day == new_time_slot.day:
                hours = int(section.time_slot.start_time.split(':')[0])
                if hours < 12:
                    time_of_day_counts['morning'] += 1
                elif hours < 17:
                    time_of_day_counts['afternoon'] += 1
                else:
                    time_of_day_counts['evening'] += 1

        # Add the new section
        hours = int(new_time_slot.start_time.split(':')[0])
        if hours < 12:
            time_of_day_counts['morning'] += 1
        elif hours < 17:
            time_of_day_counts['afternoon'] += 1
        else:
            time_of_day_counts['evening'] += 1

        # Check time of day distribution
        tod_avg = sum(time_of_day_counts.values()) / 3
        tod_variance = sum((count - tod_avg) ** 2 for count in time_of_day_counts.values()) / 3

        if tod_avg == 0:  # Edge case
            tod_balance = 1.0
        else:
            tod_balance = 1.0 - (tod_variance ** 0.5 / tod_avg)

        # Combine day balance and time-of-day balance
        return 0.7 * balance_score + 0.3 * tod_balance

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
            # More nuanced scoring based on how far from preferred
            if preference == 'early':
                if time_of_day == 'middle':
                    return 0.5
                else:  # late
                    return 0.2
            elif preference == 'middle':
                return 0.5  # Both early and late are equally less preferred
            else:  # late
                if time_of_day == 'middle':
                    return 0.5
                else:  # early
                    return 0.2

    def _evaluate_candidate(self,
                           course_id: str,
                           time_slot: TimeSlot,
                           professor_id: str,
                           hall_id: str,
                           existing_schedule: List[ScheduleSection],
                           course_level: Optional[str] = None) -> float:
        """
        Evaluate a candidate schedule section with a comprehensive scoring system.

        Args:
            course_id: Course identifier
            time_slot: Time slot to evaluate
            professor_id: Professor identifier
            hall_id: Hall identifier
            existing_schedule: Existing schedule
            course_level: Course level (if known)

        Returns:
            Composite score between 0 and 1, higher is better
        """
        # Weight factors for different criteria
        weights = {
            'time_preference': 0.20,
            'distribution': 0.25,
            'level_balance': 0.20,
            'professor_preference': 0.15,
            'hall_utilization': 0.10,
            'gaps': 0.10
        }

        scores = {}

        # Course time preference score
        scores['time_preference'] = self._evaluate_time_preference(course_id, time_slot)

        # Distribution score
        scores['distribution'] = self._are_sections_well_distributed(course_id, time_slot, existing_schedule)

        # Level balance score
        if course_level:
            scores['level_balance'] = self._is_level_schedule_balanced(
                course_level, course_id, time_slot, existing_schedule
            )
        else:
            scores['level_balance'] = 0.5  # Neutral if no level

        # Professor preference score
        is_preferred_time = self._is_professor_preferred_time(professor_id, time_slot)
        is_preferred_course = (professor_id in self.professor_preferred_courses and
                              course_id in self.professor_preferred_courses[professor_id])

        if is_preferred_time and is_preferred_course:
            scores['professor_preference'] = 1.0
        elif is_preferred_time:
            scores['professor_preference'] = 0.7
        elif is_preferred_course:
            scores['professor_preference'] = 0.6
        else:
            scores['professor_preference'] = 0.3

        # Hall utilization balance score
        hall_usage = sum(1 for section in existing_schedule if section.hall_id == hall_id)
        avg_usage = len(existing_schedule) / len(self.halls) if self.halls else 0

        if avg_usage == 0:
            scores['hall_utilization'] = 1.0
        else:
            utilization_ratio = hall_usage / avg_usage
            if utilization_ratio <= 1.0:
                scores['hall_utilization'] = 1.0
            else:
                scores['hall_utilization'] = max(0.0, 1.0 - (utilization_ratio - 1.0) / 2)

        # Professor gaps score - avoid small gaps between classes
        prof_sections = [section for section in existing_schedule
                        if section.professor_id == professor_id and
                           section.time_slot.day == time_slot.day]

        if not prof_sections:
            scores['gaps'] = 1.0  # No classes yet on this day
        else:
            # Check for small gaps
            min_gap = float('inf')
            for section in prof_sections:
                gap_minutes = time_slot.get_minutes_difference(section.time_slot)
                if gap_minutes is not None:
                    gap_minutes = abs(gap_minutes)
                    if 0 < gap_minutes < 60:  # Small gap
                        min_gap = min(min_gap, gap_minutes)

            if min_gap == float('inf'):
                scores['gaps'] = 1.0  # No small gaps
            else:
                scores['gaps'] = min(min_gap / 60, 1.0)  # Higher score for larger gaps

        # Calculate weighted composite score
        composite_score = sum(weight * scores[factor] for factor, weight in weights.items())

        return composite_score

    def generate_schedule(self) -> List[ScheduleSection]:
        """
        Generate an optimal class schedule based on the provided data and constraints.

        Returns:
            List of scheduled course sections
        """
        schedule = []

        # Sort courses by number of sections (decreasing) to schedule the most constrained courses first
        # Also consider the total schedule slots available vs. required
        total_slots_needed = sum(self.course_sections_count.get(c, 1) for c in self.courses)

        # Log info about scheduling demand
        _logger.info(f"Total sections needed: {total_slots_needed}")
        _logger.info(f"Total halls: {len(self.halls)}")
        _logger.info(f"Total school days: {len(self.school_days)}")

        # Calculate a priority score for each course
        course_priority = {}
        for course_id in self.courses:
            sections_needed = self.course_sections_count.get(course_id, 1)
            professors_available = len(self.course_professors.get(course_id, []))

            # Higher priority for courses with more sections and fewer available professors
            if professors_available == 0:
                priority = sections_needed * 1000  # Very high priority if no specific professors
            else:
                priority = sections_needed * (100 / professors_available)

            course_priority[course_id] = priority

                    # Sort courses by priority (highest first)
        sorted_courses = sorted(self.courses, key=lambda c: course_priority[c], reverse=True)

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

            # No random shuffle - we'll evaluate all slots systematically
            sections_created = 0
            while sections_created < num_sections and possible_time_slots:
                best_slot = None
                best_professor = None
                best_hall = None
                best_score = -1

                # Try all possible time slots
                for time_slot in possible_time_slots:
                    # Find a suitable professor
                    professor_id = self._find_suitable_professor(course_id, time_slot, schedule)
                    if not professor_id:
                        continue

                    # Find a suitable hall
                    hall_id = self._find_suitable_hall(time_slot, schedule)
                    if not hall_id:
                        continue

                    # Comprehensively evaluate this candidate
                    score = self._evaluate_candidate(
                        course_id, time_slot, professor_id, hall_id, schedule, course_level
                    )

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

                    _logger.info(f"Scheduled {course_id} section {sections_created} with score {best_score:.2f}")
                else:
                    # If we couldn't find a suitable slot, log a warning
                    _logger.warning(
                        f"Could not schedule all sections for course {course_id}. "
                        f"Scheduled {sections_created} out of {num_sections}."
                    )
                    break

        return schedule

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

        # Convert to dictionaries for API response
        result = []
        for section in initial_schedule:
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
