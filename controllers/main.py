import json
import logging
from odoo import http
from odoo.http import request, Response

from ..core.schedule_generator import ScheduleGenerator

_logger = logging.getLogger(__name__)


class UniversitySchedulerController(http.Controller):

    @http.route('/api/university_scheduler/generate', type='json', auth='public', methods=['POST'], csrf=False)
    def generate_schedule(self, **kwargs):
        """
        Generate a university schedule based on the provided data.

        Expected input data format:
        {
            "halls": ["Hall1", "Hall2", ...],
            "school_days": ["Monday", "Tuesday", ...],
            "departments": ["Mathematics", "Computer Science", ...],
            "professors": ["Prof1", "Prof2", ...],
            "courses": ["Course1", "Course2", ...],
            "level_courses": {
                "Level1": ["Course1", "Course2", ...],
                "Level2": ["Course3", "Course4", ...],
                ...
            },
            "department_courses": {
                "Mathematics": ["Course1", "Course2", ...],
                "Computer Science": ["Course3", "Course4", ...],
                ...
            },
            "professor_specialties": {
                "Prof1": ["Mathematics", "Computer Science", ...],
                "Prof2": ["Physics", ...],
                ...
            },
            "professor_preferred_courses": {
                "Prof1": ["Course1", "Course2", ...],
                "Prof2": ["Course3", "Course4", ...],
                ...
            },
            "professor_preferred_times": {
                "Prof1": [
                    {"day": "Monday", "start_time": "08:00", "end_time": "12:00"},
                    {"day": "Wednesday", "start_time": "13:00", "end_time": "17:00"},
                    ...
                ],
                ...
            },
            "course_preferred_times": {
                "Course1": "early",
                "Course2": "middle",
                "Course3": "late",
                ...
            },
            "restricted_times": [
                {"day": "Friday", "start_time": "12:00", "end_time": "14:00"},
                ...
            ],
            "days_with_hours": {
                "Monday": {"start": "08:00", "end": "18:00"},
                "Tuesday": {"start": "08:00", "end": "18:00"},
                ...
            },
            "course_lecture_durations": {
                "Course1": 60,  # Minutes
                "Course2": 90,
                ...
            },
            "course_sections_count": {
                "Course1": 2,
                "Course2": 3,
                ...
            }
        }

        Returns:
            List of scheduled course sections
        """
        try:
            # Get request data
            data = json.loads(request.httprequest.data)

            if not data:
                return {"success": False, "error": "No data provided"}

            # Validate required fields
            required_fields = [
                'halls', 'school_days', 'departments', 'professors', 'courses',
                'level_courses', 'department_courses', 'days_with_hours',
                'course_sections_count'
            ]

            for field in required_fields:
                if field not in data:
                    return {"success": False, "error": f"Missing required field: {field}"}

            # Initialize and run the scheduler
            scheduler = ScheduleGenerator()
            result = scheduler.generate(data)

            return {
                "success": True,
                "data": result
            }

        except Exception as e:
            _logger.exception("Error generating schedule")
            return {
                "success": False,
                "error": str(e)
            }

    @http.route('/api/university_scheduler/health', type='http', auth='none', methods=['GET'], csrf=False)
    def health_check(self):
        """Simple health check endpoint to verify API is running."""
        return Response(
            json.dumps({"status": "ok", "service": "university_scheduler"}),
            content_type='application/json'
        )
