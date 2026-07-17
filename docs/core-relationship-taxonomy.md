# Core Relationship Taxonomy

## Core Entity Types
All actors are cataloged in the central `Entity` model, using appropriate subtype or classification fields:
1. **Person**: Individual political actors, donors, candidates, treasurers, consultants, or executives.
2. **Campaign**: An election effort for a candidate or ballot measure (associated with a specific cycle and office).
3. **Committee**: Recipient committees, PACs, ballot measure committees, or sponsored committees.
4. **Political Consultant**: Specialized firms or individuals advising campaign strategies.
5. **Public-Affairs Firm**: Public relations, lobbying, or strategic consulting companies.
6. **Lobbying Firm**: Registered firms representing clients to target government agencies.
7. **Campaign Vendor**: Businesses or service providers receiving campaign expenditures.
8. **Business**: Private corporations, partnerships, or LLCs.
9. **Industry Group / Trade Association**: Coalitions representing specific business sectors.
10. **Union**: Labor organizations and their political action arms.
11. **Nonprofit**: 501(c)(3) or 501(c)(4) entities engaging in civic or political advocacy.
12. **Donor**: Entities making campaign contributions.
13. **Employer**: Entities employing individuals.
14. **Client**: Businesses or organizations retaining lobbyists or public affairs firms.

## Controlled Predicates (Relationship Types)
The database uses a standardized vocabulary of controlled relationship predicates:

| Predicate | Source Entity Type | Target Entity Type | Description |
|---|---|---|---|
| `CONSULTANT_TO` | Political Consultant / Person | Campaign / Committee | The entity acts as a campaign consultant. |
| `CAMPAIGN_MANAGER_FOR` | Person | Campaign | The individual acts as campaign manager. |
| `TREASURER_FOR` | Person | Committee | The individual acts as campaign treasurer. |
| `VENDOR_TO` | Campaign Vendor | Campaign / Committee | The vendor provided goods or services. |
| `PAID_BY_COMMITTEE` | Campaign Vendor / Consultant | Committee | The entity received expenditure payments. |
| `DONATED_TO` | Donor / Person / Business | Committee | The entity made monetary or non-monetary contribution. |
| `CLIENT_OF` | Client / Business | Lobbying / Public-Affairs Firm | The client retained the services of the firm. |
| `REPRESENTED_BY` | Client / Business | Lobbying / Public-Affairs Firm | The client is represented by the firm. |
| `EMPLOYED_BY` | Person | Business / Organization | The individual is an employee of the target entity. |
| `PRINCIPAL_OF` | Person | Consultant / Firm | The individual is a partner or principal of the firm. |
| `OWNER_OF` | Person | Business | The individual owns the target business. |
| `BOARD_MEMBER_OF` | Person | Nonprofit / Business / Board | The individual serves on the board of directors. |
| `ENDORSED` | Person / Organization | Campaign / Candidate | The actor officially endorses a candidate or measure. |
| `SUPPORTED` | Committee / Organization | Campaign / Candidate | The committee supports a ballot measure or candidate. |
| `OPPOSED` | Committee / Organization | Campaign / Candidate | The committee opposes a ballot measure or candidate. |
| `SPONSORED` | Organization / Union | Committee | The committee is sponsored by the target organization. |
| `CONTROLLED_COMMITTEE_OF` | Committee | Person (Candidate) | The committee is controlled by the candidate. |
| `INTERMEDIARY_FOR` | Person / Business | Donor | The actor served as a contribution intermediary. |
| `SUBCONTRACTOR_TO` | Vendor / Consultant | Vendor / Consultant | The actor served as a subcontractor to another vendor/firm. |
| `MEMBER_OF_INDUSTRY_GROUP` | Business / Organization | Industry Group | The entity is a member of the trade association. |
| `AFFILIATED_WITH` | Entity | Entity | Documented affiliation between two entities. |

## Derived Relationships (Shared Connections)
1. **Types**:
   - `SHARED_CONSULTANT_WITH`
   - `SHARED_VENDOR_WITH`
   - `SHARED_DONOR_WITH`
2. **Attribution Integrity**: Shared relationships are derived dynamically. They must not exist as independent unbacked records; instead, they must resolve and point directly back to the underlying transaction records or campaign-role documents in the system.
