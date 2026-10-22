# Eventhub - Product Requirements Document

## Product Overview

Eventhub is a web-based platform that streamlines the creation, management, and promotion of events for organizers, colleges, and companies, built with React, Node.js/Express, and PostgreSQL.

## Goals and Objectives

- Help organizers create, manage, and promote events efficiently.

## Target Users

- Event organiser
- colleges
- companies

## Functional Requirements

- **FR-001**: Plan events
- **FR-002**: Manage tickets
- **FR-003**: Event scheduler
- **FR-004**: Organizer dashboard
- **FR-005**: Notification system
- **FR-006**: Event details
- **FR-007**: Ticket availability

## User Workflows

- **Create and Customize Event**
  - Actor: Event organiser
  - Trigger: Organizer chooses to create a new event
  - Steps:
    1. Navigate to the event creation page
    2. Enter event details such as title, description, date, and location
    3. Upload event imagery and branding assets
    4. Configure event settings (public/private, registration requirements)
    5. Save the event configuration
  - Expected result: A new event page is created and stored in the system, ready for further scheduling and ticketing
- **Schedule Event Sessions**
  - Actor: Event organiser
  - Trigger: Organizer selects the event scheduler tool
  - Steps:
    1. Open the scheduler for the chosen event
    2. Add sessions by specifying title, speaker, start time, and duration
    3. Arrange sessions on a timeline or calendar view
    4. Save the session schedule
  - Expected result: The event’s session schedule is updated in the system and visible to attendees
- **Manage Ticket Inventory**
  - Actor: Event organiser
  - Trigger: Organizer accesses the ticket management section
  - Steps:
    1. Define ticket types (e.g., early bird, regular, VIP)
    2. Set pricing, quantity limits, and availability dates for each ticket type
    3. Publish the ticket inventory to the event page
    4. Monitor ticket sales and adjust inventory as needed
  - Expected result: Ticket inventory is accurately reflected on the event page, and real‑time availability updates are available to attendees
- **View Organizer Dashboard**
  - Actor: Event organiser
  - Trigger: Organizer logs into the platform and selects the dashboard
  - Steps:
    1. Access the organizer dashboard
    2. Review key metrics such as total registrations, ticket sales, revenue, and attendee engagement
    3. Filter data by date range or event
    4. Export reports or generate insights for decision making
  - Expected result: The organizer sees up‑to‑date analytics and performance data for their events, enabling informed management decisions

## Acceptance Criteria

- **FR-001**
- **FR-002**
- **FR-003**
- **FR-004**
- **FR-005**
- **FR-006**
- **FR-007**

## Sections not specified

- Problem Statement
- Business Rules
- Non-Functional Requirements
- Assumptions and Dependencies

_These sections were left empty. Do not invent content for them._
