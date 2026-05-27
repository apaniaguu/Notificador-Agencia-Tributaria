# Spec: Vehicle Scraper

## Requirements

### Requirement: Data Fetching
The scraper SHALL fetch vehicle data from the AEAT public JS file.

#### Scenario: Successful fetch
- **GIVEN** the AEAT server is reachable
- **WHEN** the scraper runs
- **THEN** it downloads `bienes.js` and parses the `vehiculosSubasta` array

#### Scenario: Fetch failure
- **WHEN** the download fails (network error, 404, etc.)
- **THEN** the scraper logs an error and exits gracefully
- **AND** does not produce partial output

### Requirement: Data Parsing
The scraper SHALL parse raw vehicle data into structured objects.

#### Scenario: Parse valid vehicle
- **GIVEN** a vehicle object with all required fields
- **WHEN** the scraper processes it
- **THEN** it creates a structured vehicle record with all fields mapped

#### Scenario: Parse incomplete vehicle
- **GIVEN** a vehicle object missing optional fields
- **WHEN** the scraper processes it
- **THEN** it includes the record with null/empty values for missing fields

### Requirement: Filtering
The scraper SHALL filter vehicles based on configurable criteria.

#### Scenario: Filter by province
- **GIVEN** a province code filter is applied
- **WHEN** vehicles are filtered
- **THEN** only vehicles matching that province are returned

#### Scenario: Filter by end date
- **GIVEN** a max end date filter is applied
- **WHEN** vehicles are filtered
- **THEN** only vehicles with finSubasta <= that date are returned

#### Scenario: Filter by vehicle type
- **GIVEN** a vehicle type filter is applied
- **WHEN** vehicles are filtered
- **THEN** only vehicles matching that tipo code are returned

### Requirement: Notification
The system SHALL send notifications for vehicles matching criteria.

#### Scenario: New vehicle match
- **GIVEN** a vehicle matches all filter criteria and was not seen before
- **WHEN** the notification is triggered
- **THEN** a notification is sent with vehicle details
- **AND** the vehicle is recorded as seen

#### Scenario: No matches
- **GIVEN** no vehicles match the criteria
- **WHEN** the notification is triggered
- **THEN** the scraper logs "No matching vehicles found" and exits

### Requirement: Vehicle Deduplication
The system SHALL deduplicate vehicles across scrapes using vehicle ID.

#### Scenario: Duplicate vehicle detected
- **GIVEN** a vehicle with ID "X" was already scraped in a previous run
- **WHEN** the scraper runs again and finds vehicle "X"
- **THEN** the vehicle is recorded as "unchanged"
- **AND** no notification is sent for it

#### Scenario: New vehicle detected
- **GIVEN** no previous record exists for vehicle ID "X"
- **WHEN** the scraper finds vehicle "X" in current run
- **THEN** the vehicle is recorded as "new"
- **AND** it is included in notifications if it matches filters

#### Scenario: Disappeared vehicle
- **GIVEN** vehicle "X" was present in a previous scrape
- **WHEN** vehicle "X" does not appear in the current scrape
- **THEN** the vehicle is recorded as "disappeared"
- **AND** a log entry is created for the disappearance

### Requirement: History Storage
The system SHALL persist scrape results to a local SQLite database.

#### Scenario: First scrape
- **GIVEN** no history database exists
- **WHEN** the scraper runs
- **THEN** the database is created automatically
- **AND** all scraped vehicles are stored with timestamp and scrape_id

#### Scenario: Subsequent scrapes
- **GIVEN** a history database with previous scrapes
- **WHEN** the scraper runs
- **THEN** new vehicles are appended with a new scrape_id
- **AND** existing vehicles are marked as unchanged
- **AND** disappeared vehicles are logged

#### Scenario: History query
- **GIVEN** multiple scrapes stored in the database
- **WHEN** the history is queried
- **THEN** results include all vehicles with their scrape timestamps
- **AND** results can be filtered by date, province, and type

### Requirement: Retention Policy
The system SHALL enforce a configurable retention policy for history.

#### Scenario: Default retention
- **GIVEN** no retention policy is configured
- **WHEN** history is cleaned up
- **THEN** the last 30 scrapes are kept
- **AND** older scrapes are removed

#### Scenario: Custom retention
- **GIVEN** a retention policy of N scrapes is configured
- **WHEN** history is cleaned up
- **THEN** the last N scrapes are kept
- **AND** older scrapes are removed
