# vehicle-scraper Specification

## Purpose
TBD - created by archiving change scrape-vehiculos. Update Purpose after archive.
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

