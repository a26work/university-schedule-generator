# University Schedule Generator API Documentation

This document provides comprehensive guidance on using the University Schedule Generator API. This API allows you to generate optimized class schedules for universities and colleges based on various constraints and preferences.

## Table of Contents

1. [API Overview](#api-overview)
2. [API Endpoints](#api-endpoints)
3. [Input Data Schema](#input-data-schema)
4. [Output Data Schema](#output-data-schema)
5. [Example Requests](#example-requests)
6. [Error Handling](#error-handling)
7. [Optimization Strategies](#optimization-strategies)

## API Overview

The University Schedule Generator API creates optimal class schedules based on various constraints including:

- Available halls
- School days and hours
- Academic departments and levels
- Professors' specialties and preferences
- Course requirements and restrictions
- Time and space constraints

The scheduling algorithm uses constraint satisfaction techniques with heuristic optimization to create schedules that:

1. Prevent conflicts (same professor, same hall, or overlapping times)
2. Distribute courses optimally across days
3. Accommodate professor and course time preferences
4. Allow flexibility for students to choose appropriate times
5. Create efficient schedules for both students and professors

## API Endpoints

### Generate Schedule

Creates a new class schedule based on the provided data.

**Endpoint:** `/api/university_scheduler/generate`

**Method:** `POST`

**Content-Type:** `application/json`

**Authentication:** Required

**Response Format:** JSON

### Health Check

Verifies that the API is functioning properly.

**Endpoint:** `/api/university_scheduler/health`

**Method:** `GET`

**Authentication:** None required

**Response Format:** JSON

## Input Data Schema

The API expects a JSON object with the following structure:

```json
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
        "Course1": 60,  // Minutes
        "Course2": 90,
        ...
    },
    "course_sections_count": {
        "Course1": 2,
        "Course2": 3,
        ...
    }
}
```

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `halls` | Array of strings | Yes | List of all available halls/rooms |
| `school_days` | Array of strings | Yes | List of school days (e.g., "Monday", "Tuesday") |
| `departments` | Array of strings | Yes | List of academic departments |
| `professors` | Array of strings | Yes | List of all professors |
| `courses` | Array of strings | Yes | List of all courses |
| `level_courses` | Object | Yes | Mapping of levels to their courses |
| `department_courses` | Object | Yes | Mapping of departments to their courses |
| `professor_specialties` | Object | No | Mapping of professors to departments they can teach |
| `professor_preferred_courses` | Object | No | Mapping of professors to courses they prefer to teach |
| `professor_preferred_times` | Object | No | Mapping of professors to their preferred teaching times |
| `course_preferred_times` | Object | No | Mapping of courses to preferred time of day (early, middle, late) |
| `restricted_times` | Array of objects | No | List of time slots when lectures should not be scheduled |
| `days_with_hours` | Object | Yes | Mapping of days to their start and end times |
| `course_lecture_durations` | Object | No | Mapping of courses to their lecture durations in minutes (default: 60) |
| `course_sections_count` | Object | Yes | Mapping of courses to the number of sections to be created |

## Output Data Schema

The API returns a JSON response with the following structure:

```json
{
    "success": true,
    "data": [
        {
            "course_id": "Course1",
            "section_number": 1,
            "professor_id": "Prof1",
            "hall_id": "Hall1",
            "day": "Monday",
            "start_time": "08:00",
            "end_time": "09:00"
        },
        {
            "course_id": "Course1",
            "section_number": 2,
            "professor_id": "Prof2",
            "hall_id": "Hall2",
            "day": "Wednesday",
            "start_time": "10:00",
            "end_time": "11:00"
        },
        // ... more sections
    ]
}
```

In case of an error, the response will be:

```json
{
    "success": false,
    "error": "Error message"
}
```

## Example Requests

### Example 1: Generate Schedule

```bash
curl -X POST \
  http://your-odoo-server/api/university_scheduler/generate \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer your-access-token' \
  -d '{
    "halls": ["Hall1", "Hall2", "Hall3"],
    "school_days": ["Monday", "Tuesday", "Wednesday", "Thursday"],
    "departments": ["Mathematics", "Computer Science"],
    "professors": ["Prof1", "Prof2", "Prof3"],
    "courses": ["Math101", "CS101", "CS102"],
    "level_courses": {
        "Level1": ["Math101", "CS101"],
        "Level2": ["CS102"]
    },
    "department_courses": {
        "Mathematics": ["Math101"],
        "Computer Science": ["CS101", "CS102"]
    },
    "professor_specialties": {
        "Prof1": ["Mathematics"],
        "Prof2": ["Computer Science"],
        "Prof3": ["Mathematics", "Computer Science"]
    },
    "professor_preferred_courses": {
        "Prof1": ["Math101"],
        "Prof2": ["CS102"],
        "Prof3": ["CS101"]
    },
    "days_with_hours": {
        "Monday": {"start": "08:00", "end": "16:00"},
        "Tuesday": {"start": "08:00", "end": "16:00"},
        "Wednesday": {"start": "08:00", "end": "16:00"},
        "Thursday": {"start": "08:00", "end": "16:00"}
    },
    "course_sections_count": {
        "Math101": 2,
        "CS101": 1,
        "CS102": 1
    }
}'
```

### Example 2: Health Check

```bash
curl -X GET http://your-odoo-server/api/university_scheduler/health
```

Expected response:

```json
{
    "status": "ok",
    "service": "university_scheduler"
}
```

## Error Handling

The API uses standard HTTP status codes and provides detailed error messages in the response body.

| Status Code | Meaning |
|-------------|---------|
| 200 | Success |
| 400 | Bad Request - Missing or invalid data |
| 401 | Unauthorized - Authentication failed |
| 500 | Internal Server Error - Something went wrong on the server |

Common error scenarios:

1. Missing required fields
2. Invalid data types or formats
3. Impossible scheduling constraints
4. Server-side processing errors

## Optimization Strategies

The scheduler employs several strategies to create optimal schedules:

1. **Constraint Satisfaction**: Ensures all hard constraints (no conflicts) are met
2. **Course Distribution**: Tries to distribute sections of the same course on different days
3. **Level Balancing**: Balances courses for each academic level across days
4. **Professor Efficiency**: Optimizes professor schedules to reduce unnecessary travel and waiting times
5. **Time Preference Matching**: Assigns courses to preferred time slots when possible
6. **Hall Utilization**: Distributes classes across available halls

When the algorithm cannot satisfy all constraints and preferences, it prioritizes:

1. No scheduling conflicts (highest priority)
2. Professor availability and specialty matching
3. Course distribution across days
4. Level schedule balance
5. Time preferences (lowest priority)

If the algorithm cannot schedule all sections due to constraints, it will schedule as many as possible and log warnings about the sections it couldn't schedule.