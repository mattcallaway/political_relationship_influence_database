# Source Acquisition Priority

To ensure platform integrity and avoid product drift, source acquisition and ingestion pipelines must follow this priority hierarchy:

## Priority 1: Campaign Finance Disclosures (FPPC Filings)
* **Form 460 (Schedule A & E)**: Primary records documenting donors, campaign committees, campaign vendors, consultants, payment codes, and descriptions of services.
* **Form 410**: Committee Organization statements tracking treasurers, candidate controls, and sponsoring organizations.
* **Form 496 & 497**: Late independent expenditure and late contribution filings.
* **Official Campaign Finance Exports**: Electronic datasets of contributions and expenditures directly from municipal or state filing portals.

## Priority 2: Consultant & Public-Affairs Registries
* **Lobbying Disclosures**: Ingesting firm-client registries identifying target government departments and compensation values.
* **Consultant & Public-Affairs Firm Websites**: Archival scraping of team members, clients represented, and campaigns run.
* **Campaign & Committee Websites**: Capturing staff rosters, campaign managers, treasurers, and endorsements.

## Priority 3: Endorsement & Mailer Literature
* **Campaign Mailers**: Documenting slate mailers, printers, distributors, and campaign vendor logos.
* **Endorsement Lists**: Capturing candidate endorsements from political groups, labor unions, and individuals.

## Secondary / Low Priority: Government Records
* **Board & Commission Rosters**: Board terms, appointments, and seat descriptions.
* **Meeting Agendas, Minutes, and Votes**: Kept strictly as secondary sources. Ingested and linked *only* when they document specific lobbying target meetings, public contracts, or appointments. Do not prioritize general minutes acquisition.
