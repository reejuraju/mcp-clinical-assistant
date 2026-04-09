MCP Clinical Assistant
An MCP-based virtual receptionist built on Claude, designed for healthcare practice management. Connects natural language queries to live clinical scheduling and patient data via Model Context Protocol (MCP) servers.

⚠️ This repository documents the architecture and design of a production system. Source code is maintained in a private repository.

Overview
Healthcare front-desk workflows involve a lot of repetitive, context-heavy tasks — checking appointment availability, looking up patient records, handling scheduling conflicts, answering common queries. This project replaces or augments that workflow with a Claude-powered agent that can understand natural language and take action against live clinical systems.
The agent runs via MCP servers that expose scheduling and patient data as tools Claude can call. Rather than building a rigid chatbot with fixed intents, the system leverages Claude's reasoning to handle the full range of queries a receptionist would face.

Architecture
1. User sends a natural language query (e.g. "Is Dr. Smith available Thursday afternoon?")
2. Claude receives the query and decides which tools to call and in what order
3. MCP Server Layer exposes the clinical system as structured tools Claude can invoke:

        scheduling-server — appointment availability and bookings
        patient-server — patient lookup and demographics
        practitioner-server — practitioner schedules and availability

4. Clinical SaaS Platform — the underlying REST API that the MCP servers connect to
Claude combines the results and returns a coherent, contextual response to the user.
  
Claude acts as the reasoning layer. The MCP servers act as structured tool interfaces between Claude and the underlying clinical platform. Claude decides which tools to call, in what order, and how to combine results into a coherent response.

MCP Servers
scheduling-server
Exposes appointment and scheduling tools:

get_available_slots — returns available appointment slots for a given practitioner and date range
book_appointment — creates a new appointment against a patient and practitioner
cancel_appointment — cancels an existing appointment with optional reason capture
get_upcoming_appointments — lists upcoming appointments for a patient or practitioner

patient-server
Exposes patient data tools:

lookup_patient — searches by name, DOB, or patient ID
get_patient_summary — returns key demographics and recent visit history
get_contact_details — returns phone/email for communication workflows

practitioner-server
Exposes practitioner availability tools:

get_practitioner_list — returns active practitioners and their specialties
get_practitioner_schedule — returns working hours and leave for a given date range


Example Interactions
Scheduling query:
User:  "Can I get an appointment with Dr. Smith this week?"
Agent: Calls get_available_slots → returns Thursday 2pm and Friday 10am
       "Dr. Smith has availability on Thursday at 2:00 PM or Friday at 10:00 AM — which works for you?"
Patient lookup:
User:  "Can you pull up Sarah Johnson's next appointment?"
Agent: Calls lookup_patient → get_upcoming_appointments
       "Sarah Johnson has an appointment on Tuesday 14th at 11:00 AM with Dr. Lee."

Tech Stack
LayerTechnologyAI / ReasoningClaude (Anthropic API)Agent ProtocolModel Context Protocol (MCP)MCP Server RuntimeNode.js / TypeScriptBackend PlatformC# / .NET CoreClinical PlatformHealthcare SaaS Platform (REST API)InfrastructureAWS (EC2, RDS, Lambda)

Design Decisions
Why MCP over a traditional function-calling approach?
MCP provides a standardised protocol for exposing tools to language models. Rather than hardcoding tool definitions into each API call, MCP servers act as reusable, composable interfaces. This makes it easier to add new capabilities (new servers, new tools) without changing the core agent logic.
Why Claude?
Clinical workflows require careful, context-aware reasoning — understanding that "this afternoon" means something different at 9am vs 4pm, or that a patient asking about "my usual doctor" needs a lookup before availability can be checked. Claude handles this kind of multi-step reasoning well without requiring rigid prompt engineering for every scenario.
No proprietary data exposure
All MCP tools return only what is needed for the specific query. Patient data access is scoped and audited. The agent does not retain information between sessions.

Related Work
Other AI features built as part of the same platform:

LLM-powered clinical documentation — auto-generates clinical notes from practitioner inputs using the Claude API
Voice transcription pipeline — converts consultation audio into structured clinical notes (Whisper + post-processing)


Status
Active development. Core scheduling and patient lookup flows are functional. Expanding tool coverage and adding confirmation/rollback flows for write operations.
