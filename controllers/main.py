import json
import logging
from odoo import http
from odoo.http import request, Response

from ..core.schedule_generator import ScheduleGenerator

_logger = logging.getLogger(__name__)


class UniversitySchedulerController(http.Controller):

    @http.route('/api/university_scheduler/generate', type='json', auth='public', methods=['POST'], csrf=False)
    def generate_schedule(self, **kwargs):
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
