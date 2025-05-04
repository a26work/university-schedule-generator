# University Schedule Generator - Technical Design Document

## 1. Introduction

This document provides a detailed technical overview of the University Schedule Generator module for Odoo 17. The module implements an algorithm for generating optimal university class schedules based on various constraints and preferences.

## 2. Problem Definition

University class scheduling is a complex constraint satisfaction problem (CSP) with the following characteristics:

- **Resources**: Professors, halls, time slots, courses
- **Hard Constraints**: No scheduling conflicts, respecting availability
- **Soft Constraints**: Preferences for times, days, and course assignments
- **Optimization Goals**: Efficient schedules for both students and professors

This problem is NP-hard and requires a heuristic approach to find good (though not necessarily optimal) solutions in reasonable time.

## 3. Solution Architecture

### 3.1 Module Structure

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

### 3.2 Component Responsibilities

#### Core Components

- **ScheduleGenerator**: Main algorithm that generates and optimizes schedules
- **TimeSlot**: Represents a time slot with day, start time, and end time
- **ScheduleSection**: Represents a scheduled course section with all details

#### API Components

- **UniversitySchedulerController**: Exposes API endpoints and handles requests

### 3.3 Data Flow

1. Client sends a request with scheduling data to the API endpoint
2. Controller validates input data and calls the scheduler
3. ScheduleGenerator loads data and generates an initial schedule
4. ScheduleGenerator optimizes the initial schedule
5. Controller formats the result and returns it to the client

## 4. Algorithm Design

### 4.1 Key Classes

#### TimeSlot

Represents a specific time period on a specific day. Provides methods to check for overlaps with other time slots.

#### ScheduleSection

Represents a scheduled course section with:
- Course ID
- Section number
- Assigned professor
- Assigned hall
- Assigned time slot

#### ScheduleGenerator

Main class that implements the scheduling algorithm.

### 4.2 Algorithm Overview

The scheduling algorithm follows these major steps:

1. **Data Loading**: Process input data and create internal data structures
2. **Time Slot Generation**: Generate all possible time slots for each course
3. **Initial Schedule Creation**: Create a valid initial schedule
4. **Schedule Optimization**: Improve the initial schedule

### 4.3 Detailed Algorithm Flow

#### 4.3.1 Initial Schedule Generation

```
Sort courses by number of sections (decreasing)
For each course:
    For each section to be created:
        Generate all possible time slots
        Shuffle time slots for randomness
        For each time slot:
            Check if sections are well distributed
            Check if level schedule is balanced
            Find a suitable professor
            Find a suitable hall
            Calculate time preference score
            Update best options if better than current best
        If best options found:
            Create a new section with best options
            Add to schedule
        Else:
            Log warning and continue
```

#### 4.3.2 Schedule Optimization

```
Group sections by professor
For each professor:
    Group their sections by day
    For each day with a single section:
        Try to move to a day when professor is already teaching
        Check constraints (hall availability, professor availability)
        Check distribution and balance
        If all constraints satisfied:
            Move the section
```

### 4.4 Constraint Handling

#### Hard Constraints

- No professor can teach two classes at the same time
- No hall can host two classes at the same time
- Classes must be scheduled within school hours
- Classes must not be scheduled during restricted times

#### Soft Constraints (Preferences)

- Distribute sections of the same course across different days
- Balance courses for each level across days
- Schedule courses at their preferred times
- Respect professor preferred times and courses
- Reduce the number of days professors need to come to work

### 4.5 Scoring and Selection

For each potential time slot, a score is calculated based on:
- Time preference match score (higher is better)
- Additional factors could be added for more sophisticated scoring

## 5. Implementation Details

### 5.1 Key Data Structures

- **Dictionary mappings**: Used for quick lookup of relationships (e.g., level_courses, professor_specialties)
- **Lists**: Used for collections of entities (e.g., halls, professors)
- **Custom objects**: Used for rich domain entities (TimeSlot, ScheduleSection)

### 5.2 Efficiency Considerations

- **Pre-computing time slots**: Avoids recalculating during the scheduling process
- **Sorting courses**: Schedules most constrained courses first
- **Early constraint checking**: Quickly eliminates invalid options
- **Random shuffling**: Avoids bias in equally scored options

### 5.3 Error Handling

- Input validation at API level
- Logging of warnings when constraints cannot be satisfied
- Graceful handling of impossible scheduling situations

## 6. Algorithm Complexity Analysis

### 6.1 Time Complexity

- **Time slot generation**: O(D * H * C) where D is the number of days, H is the number of hours per day, and C is the number of courses
- **Initial scheduling**: O(C * S * T * P * H) where C is the number of courses, S is the average number of sections, T is the average number of time slots, P is the number of professors, and H is the number of halls
- **Optimization**: O(P * D * D * T) where P is the number of professors, D is the number of days, and T is the average number of time slots

### 6.2 Space Complexity

- O(C * S + T + P + H) where C is the number of courses, S is the average number of sections, T is the total number of time slots, P is the number of professors, and H is the number of halls

## 7. Extension Points

The algorithm can be extended in several ways:

### 7.1 Additional Constraints

Additional constraints can be added by:
1. Adding new data fields to the input schema
2. Implementing constraint checking methods
3. Incorporating the constraint checks in the scheduling process

### 7.2 Alternative Optimization Strategies

Alternative optimization strategies can be implemented by:
1. Creating new optimization methods
2. Adding them to the optimization phase

### 7.3 Advanced Scoring Functions

The scoring function for time slots can be enhanced to consider additional factors:
1. Distance between consecutive classes for professors
2. Room capacity vs. expected enrollment
3. Equipment needs for specific courses
4. Historical data on preferred times

## 8. Testing Approach

### 8.1 Unit Testing

Unit tests should focus on:
- Core constraint checking methods
- Time slot generation
- Schedule optimization

### 8.2 Integration Testing

Integration tests should verify:
- API request handling
- End-to-end schedule generation
- Error handling

### 8.3 Performance Testing

Performance tests should measure:
- Execution time for different problem sizes
- Memory usage
- Solution quality metrics

## 9. Conclusion

The University Schedule Generator implements a sophisticated algorithm for solving the complex university scheduling problem. By using a combination of constraint satisfaction techniques and heuristic optimization, it produces high-quality schedules that respect various constraints and preferences.

The modular design allows for easy extension and customization to address specific university scheduling requirements. The clean API interface enables seamless integration with external systems.