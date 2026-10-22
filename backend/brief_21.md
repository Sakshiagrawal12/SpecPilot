**Technology preferences:** React for the front‑end, Node.js with Express for the API, and PostgreSQL for data storage

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

## Eventhub - Sprint Plan

- **Sprints:**
  - **Sprint 1**
    - **Goal:** Establish core backend services for event creation and ticketing.
    - **Task titles:**
      - Create Event API Endpoint
      - Ticket Management API
  - **Sprint 2**
    - **Goal:** Enable event creation from the frontend and provide basic ticket inventory.
    - **Task titles:**
      - Event Creation Frontend Form
      - Ticket Inventory Frontend
  - **Sprint 3**
    - **Goal:** Add scheduling capabilities and integrate event details page.
    - **Task titles:**
      - Event Scheduler UI Component
      - Event Details Page
  - **Sprint 4**
    - **Goal:** Build organizer analytics and dashboard UI.
    - **Task titles:**
      - Organizer Dashboard Data Aggregation
      - Organizer Dashboard UI
  - **Sprint 5**
    - **Goal:** Implement notification system for event lifecycle events.
    - **Task titles:**
      - Notification System for Event Lifecycle
  - **Sprint 6**
    - **Goal:** Final integration, testing, and polish.
- **Capacity assumptions:**
  - Assume a small team of 2 developers working full‑time (40 hrs/week) with a 2‑week sprint cadence, yielding roughly 80 developer‑hours per sprint.
- **Dependencies:**
  - **Item**
    - **Task:** Event Scheduler UI Component
    - **Depends on:**
      - Create Event API Endpoint
    - **Reason:** Allows organizers to schedule sessions; depends on event creation.
  - **Item**
    - **Task:** Ticket Inventory Frontend
    - **Depends on:**
      - Ticket Management API
    - **Reason:** Displays ticket data to users; depends on ticket API.
  - **Item**
    - **Task:** Organizer Dashboard Data Aggregation
    - **Depends on:**
      - Ticket Management API
      - Event Scheduler UI Component
    - **Reason:** Aggregates metrics for dashboard; depends on ticket API and scheduler UI.
  - **Item**
    - **Task:** Organizer Dashboard UI
    - **Depends on:**
      - Organizer Dashboard Data Aggregation
    - **Reason:** Visualizes aggregated data; depends on data aggregation service.
  - **Item**
    - **Task:** Event Details Page
    - **Depends on:**
      - Create Event API Endpoint
      - Ticket Management API
      - Ticket Inventory Frontend
    - **Reason:** Public-facing page that requires event and ticket data; depends on API and inventory UI.
  - **Item**
    - **Task:** Notification System for Event Lifecycle
    - **Depends on:**
      - Create Event API Endpoint
      - Ticket Management API
    - **Reason:** Sends emails based on event and ticket events; depends on event and ticket APIs.
- **Independent tasks:**
  - Create Event API Endpoint
  - Event Creation Frontend Form
  - Ticket Management API

## Task Breakdown

### Task 1: Create Event API Endpoint  _[High | Backend Development | EventCreationModule | Medium | Todo]_

Implement a RESTful endpoint to create a new event with title, description, date, location, imagery, and settings.

**Acceptance criteria:**
POST /api/events returns 201 with event ID and stored data matches input; validation errors return 400.

### Task 2: Event Creation Frontend Form  _[High | Frontend Development | EventCreationModule | Medium | Todo]_

Build a React form for organizers to input event details, upload imagery, and configure settings.

**Acceptance criteria:**
Form submits data to API, displays success message, and redirects to event page.

### Task 3: Event Scheduler UI Component  _[High | Frontend Development | EventSchedulerModule | Large | Todo]_

Create a calendar view to add and arrange sessions for an event.

**Acceptance criteria:**
Sessions can be added with title, speaker, start time, duration; changes persist via API.

**Depends on:**
- Create Event API Endpoint

### Task 4: Ticket Management API  _[High | Backend Development | TicketManagementModule | Large | Todo]_

Implement endpoints to define ticket types, set pricing, quantity, and availability dates for an event.

**Acceptance criteria:**
POST /api/events/:id/tickets creates ticket types; GET returns current inventory.

**Depends on:**
- Create Event API Endpoint

### Task 5: Ticket Inventory Frontend  _[High | Frontend Development | TicketAvailabilityModule | Medium | Todo]_

Build UI to display ticket types, pricing, and real‑time availability on the event page.

**Acceptance criteria:**
Ticket list updates instantly after inventory changes; availability shown accurately.

**Depends on:**
- Ticket Management API

### Task 6: Organizer Dashboard Data Aggregation  _[Medium | Backend Development | OrganizerDashboardModule | Large | Todo]_

Create backend services to aggregate metrics (registrations, sales, revenue) for the dashboard.

**Acceptance criteria:**
Dashboard API returns correct metrics within 2 seconds for up to 100 events.

**Depends on:**
- Ticket Management API
- Event Scheduler UI Component

### Task 7: Organizer Dashboard UI  _[Medium | Frontend Development | OrganizerDashboardModule | Large | Todo]_

Implement a React dashboard to display metrics, filters, and export options.

**Acceptance criteria:**
Dashboard shows correct data, filters work, and export CSV functions.

**Depends on:**
- Organizer Dashboard Data Aggregation

### Task 8: Event Details Page  _[High | Frontend Development | EventDetailsModule | Medium | Todo]_

Create a public event page displaying title, description, schedule, and ticket options.

**Acceptance criteria:**
Page renders all event data correctly and links to ticket purchase.

**Depends on:**
- Create Event API Endpoint
- Ticket Inventory Frontend

### Task 9: Notification System for Event Lifecycle  _[Medium | Backend Development | NotificationSystemModule | Medium | Todo]_

Implement email notifications for event creation, session updates, and ticket sales.

**Acceptance criteria:**
Emails are sent on relevant events and contain correct event details.

**Depends on:**
- Create Event API Endpoint
- Ticket Management API
