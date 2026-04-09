"""
MCP Clinical Assistant – Prototype
A minimal demonstration of the agent pattern used in the production system.
Uses the Anthropic API with tool use to simulate an MCP-connected receptionist.

Mock data only – no real patient or clinical data.
"""

import anthropic
import json
from datetime import datetime

# ── Mock Data ─────────────────────────────────────────────────────────────────

PRACTITIONERS = {
    "P001": {"name": "Dr. Sarah Smith", "specialty": "Physiotherapy"},
    "P002": {"name": "Dr. James Lee",   "specialty": "Occupational Therapy"},
    "P003": {"name": "Dr. Anne Brown",  "specialty": "Sports Medicine"},
}

PATIENTS = {
    "PT001": {"name": "John Carter",   "dob": "1985-03-12", "phone": "021-555-0101"},
    "PT002": {"name": "Maria Garcia",  "dob": "1992-07-24", "phone": "021-555-0182"},
    "PT003": {"name": "Tom Wilson",    "dob": "1978-11-05", "phone": "021-555-0193"},
}

APPOINTMENTS = [
    {"id": "A001", "patient_id": "PT001", "practitioner_id": "P001", "datetime": "2026-04-14 09:00", "status": "confirmed"},
    {"id": "A002", "patient_id": "PT002", "practitioner_id": "P002", "datetime": "2026-04-14 10:30", "status": "confirmed"},
    {"id": "A003", "patient_id": "PT001", "practitioner_id": "P003", "datetime": "2026-04-16 14:00", "status": "confirmed"},
    {"id": "A004", "patient_id": "PT003", "practitioner_id": "P001", "datetime": "2026-04-15 11:00", "status": "confirmed"},
]

AVAILABLE_SLOTS = {
    "P001": ["2026-04-14 11:00", "2026-04-15 09:00", "2026-04-17 10:00", "2026-04-17 14:00"],
    "P002": ["2026-04-14 13:00", "2026-04-15 15:00", "2026-04-16 09:00"],
    "P003": ["2026-04-15 10:00", "2026-04-16 11:00", "2026-04-17 09:00"],
}

# ── Tool Definitions ───────────────────────────────────────────────────────────

TOOLS = [
    {
        "name": "lookup_patient",
        "description": "Search for a patient by name. Returns patient ID, date of birth, and contact details.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Full or partial patient name"}
            },
            "required": ["name"]
        }
    },
    {
        "name": "get_available_slots",
        "description": "Get available appointment slots for a practitioner. Optionally filter by date.",
        "input_schema": {
            "type": "object",
            "properties": {
                "practitioner_name": {"type": "string", "description": "Full or partial practitioner name"},
                "date_filter":       {"type": "string", "description": "Optional date to filter by, e.g. '2026-04-17'"}
            },
            "required": ["practitioner_name"]
        }
    },
    {
        "name": "get_upcoming_appointments",
        "description": "Get upcoming appointments for a patient or practitioner.",
        "input_schema": {
            "type": "object",
            "properties": {
                "patient_name":      {"type": "string", "description": "Patient name to look up appointments for"},
                "practitioner_name": {"type": "string", "description": "Practitioner name to look up appointments for"}
            }
        }
    }
]

# ── Tool Handlers ──────────────────────────────────────────────────────────────

def lookup_patient(name: str) -> dict:
    name_lower = name.lower()
    matches = [
        {"id": pid, **pdata}
        for pid, pdata in PATIENTS.items()
        if name_lower in pdata["name"].lower()
    ]
    if not matches:
        return {"error": f"No patient found matching '{name}'"}
    return {"patients": matches}


def get_available_slots(practitioner_name: str, date_filter: str = None) -> dict:
    name_lower = practitioner_name.lower()
    match = next(
        ((pid, pdata) for pid, pdata in PRACTITIONERS.items()
         if name_lower in pdata["name"].lower()),
        None
    )
    if not match:
        return {"error": f"No practitioner found matching '{practitioner_name}'"}

    pid, pdata = match
    slots = AVAILABLE_SLOTS.get(pid, [])

    if date_filter:
        slots = [s for s in slots if s.startswith(date_filter)]

    return {
        "practitioner": pdata["name"],
        "specialty":    pdata["specialty"],
        "available_slots": slots if slots else ["No available slots for the requested period"]
    }


def get_upcoming_appointments(patient_name: str = None, practitioner_name: str = None) -> dict:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    results = []

    for appt in APPOINTMENTS:
        if appt["datetime"] < now:
            continue

        patient     = PATIENTS.get(appt["patient_id"], {})
        practitioner = PRACTITIONERS.get(appt["practitioner_id"], {})

        if patient_name and patient_name.lower() not in patient.get("name", "").lower():
            continue
        if practitioner_name and practitioner_name.lower() not in practitioner.get("name", "").lower():
            continue

        results.append({
            "appointment_id":  appt["id"],
            "datetime":        appt["datetime"],
            "patient":         patient.get("name"),
            "practitioner":    practitioner.get("name"),
            "specialty":       practitioner.get("specialty"),
            "status":          appt["status"]
        })

    if not results:
        return {"message": "No upcoming appointments found."}
    return {"appointments": results}


def handle_tool_call(tool_name: str, tool_input: dict) -> str:
    if tool_name == "lookup_patient":
        result = lookup_patient(**tool_input)
    elif tool_name == "get_available_slots":
        result = get_available_slots(**tool_input)
    elif tool_name == "get_upcoming_appointments":
        result = get_upcoming_appointments(**tool_input)
    else:
        result = {"error": f"Unknown tool: {tool_name}"}
    return json.dumps(result)

# ── Agent Loop ─────────────────────────────────────────────────────────────────

def run_receptionist(user_query: str):
    client = anthropic.Anthropic()  # uses ANTHROPIC_API_KEY env var

    print(f"\n{'─'*60}")
    print(f"User: {user_query}")
    print(f"{'─'*60}")

    messages = [{"role": "user", "content": user_query}]

    system_prompt = """You are a helpful clinical receptionist assistant. 
You have access to tools to look up patients, check practitioner availability, 
and retrieve upcoming appointments. Always be concise and friendly."""

    # Agentic loop — keep going until Claude stops calling tools
    while True:
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=1024,
            system=system_prompt,
            tools=TOOLS,
            messages=messages
        )

        # Collect any tool calls from this response
        tool_calls = [b for b in response.content if b.type == "tool_use"]

        if not tool_calls:
            # No more tool calls — print final response and exit
            final = next((b.text for b in response.content if b.type == "text"), "")
            print(f"\nAssistant: {final}\n")
            break

        # Process all tool calls
        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for tool_call in tool_calls:
            print(f"  [tool] {tool_call.name}({json.dumps(tool_call.input)})")
            result = handle_tool_call(tool_call.name, tool_call.input)
            tool_results.append({
                "type":        "tool_result",
                "tool_use_id": tool_call.id,
                "content":     result
            })

        messages.append({"role": "user", "content": tool_results})

# ── Run ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Try a few example queries
    run_receptionist("Is Dr. Smith available this Thursday or Friday?")
    run_receptionist("Can you pull up John Carter's upcoming appointments?")
    run_receptionist("I need to book with a sports medicine specialist — what's available?")
