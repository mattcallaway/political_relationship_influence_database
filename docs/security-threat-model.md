# Security Threat Model

## Threat Vectors & Countermeasures
1. **Document Injection / Script Execution**: PDFs are stripped of active scripts during text layer extraction.
2. **Path Traversal**: Uploaded file paths are sanitized and stored using randomized UUID filenames on disk.
3. **Malware / Malicious Uploads**: Dedicated validation hook checks file MIME types and size boundaries.
4. **Unauthorized Entity Merging**: Entity merging operations require reviewer role permissions and leave an auditable `ChangeLog` trail.
