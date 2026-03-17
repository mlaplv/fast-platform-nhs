# Changelog

All notable changes to the **Fast Platform Core** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- **VoiceHandler (STT Context Loss):** Fixed a hallucination bug where STT confirmation keywords (e.g., "ok", "đúng") overwrote the original intent payload during campaign creation.
  - *Details:* Implemented Advanced Context Resolution in `VoiceHandler.handle_request` to prioritize `intent_data['cleaned_transcript']` over the raw literal transcript.
  - *Refactoring:* Isolated confirmation keywords from task resumption triggers to prevent conflict between intent recovery and workflow continuation.

### Changed
- **ContentOrchestrator Logic:** Tighter semantic checks introduced when mapping new voice inputs to active campaigns to avoid false positives.

---
*Note: This log follows the War Room Protocol (R00) and Evolution Protocol (R03) of Elite V2.2 Architecture.*
