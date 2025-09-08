We have just launched our Service Map API (Something Customer have been looking to get for a while)

Docs: https://api-docs.honeycomb.io/api/service-maps

There are two areas where Customer need some help to make sure they get the maximum value from the Service Map API. We're also leaning in more heavily here since there is a large HFO opportunity in play.

1. Dependency Data Extraction and Validation
Topic: Support integration of Honeycomb dependency data with internal systems

What / Why:

The customer wants to fetch and validate service dependency data from Honeycomb to cross-check against internal systems.

This includes verifying if the dependencies match and tracking “first seen” and “last seen” for changes over time.
Action

Ask:

Work with the customer to define the correct API calls and process flow.

Help build a repeatable, efficient script/process to retrieve and write the data into their internal systems.

Ensure flexibility for time-based querying (e.g., for a 7-day window).

2. Supporting Large-Scale Service Lists
Topic: Handling thousands of services as input

What / Why:

The customer cannot pass thousands of services manually into API calls. They’d prefer to provide a file with the service list to avoid overhead and enable automation.

Ask:

Collaborate with the customer to develop a script or CLI that:

Accepts a file as input,

Parses the service list,

Makes the appropriate Honeycomb API calls in the background.
