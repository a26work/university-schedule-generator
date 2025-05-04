# University Schedule Generator

An Odoo 17 module for generating optimal university class schedules based on complex constraints and preferences.

## Overview

The University Schedule Generator module provides a powerful scheduling algorithm that creates time tables for university classes. It takes into account various constraints and preferences to produce optimal schedules that:

- Prevent scheduling conflicts (same professor, hall, or time)
- Distribute courses optimally across days
- Respect professor preferences and specialties
- Create efficient schedules for both students and faculty
- Provide flexibility for students to choose appropriate times

## Features

- **Intelligent Scheduling Algorithm** - Uses constraint satisfaction and optimization techniques to create valid schedules
- **Flexible Constraints** - Accommodates various scheduling requirements and preferences
- **API-First Design** - Easily integrates with external systems through a well-defined API
- **Optimized Results** - Creates schedules that maximize efficiency and satisfaction for all stakeholders
- **No Frontend Dependency** - Operates as a pure API service without requiring UI components

## Technical Details

### Installation

1. Copy the `university_scheduler` directory to your Odoo addons folder
2. Update the addons list in Odoo
3. Install the "University Schedule Generator" module

### Architecture

The module is structured as follows:

```
university_scheduler/
├── __init__.py
├── __manifest__.py
├── controllers/
│   ├── __init__.py
│   └── main.py
├── core/
│   ├── __init__.py
│   └── schedule_generator.py
├── api_docs.md
├── technical_design.md
├── small_test_data.json
├── huge_test_data.json
└── README.md
```

- **core/schedule_generator.py**: Contains the main scheduling algorithm
- **controllers/main.py**: Exposes the API endpoints

### API Usage

The module exposes a JSON API at `/api/university_scheduler/generate`. See the [API Documentation](api_docs.md) for detailed information on request/response formats and examples.

## Algorithm

The schedule generation algorithm uses a constraint-satisfaction approach with heuristic optimization:

1. **Initial Schedule Generation**:
   - Sorts courses by the number of sections (most constrained first)
   - For each course and section:
     - Generates all possible valid time slots
     - Scores time slots based on constraints and preferences
     - Assigns the best available slot, professor, and hall

2. **Schedule Optimization**:
   - Attempts to consolidate professor schedules to reduce travel days
   - Balances course distribution across days for each level
   - Ensures an even distribution of teaching load

3. **Constraint Handling**:
   - Hard constraints (e.g., no scheduling conflicts) are strictly enforced
   - Soft constraints (e.g., preferred times) influence slot scoring
   - When all constraints cannot be satisfied, the algorithm prioritizes essential constraints

## Requirements

- Odoo 17
- Python 3.8+

## Limitations

- The algorithm may not find a perfect solution if constraints are too restrictive
- Very large scheduling problems (hundreds of courses with many sections) may require significant processing time
- Some complex university-specific constraints may require customization

## Support

For issues, feature requests, or general questions, please contact with us.