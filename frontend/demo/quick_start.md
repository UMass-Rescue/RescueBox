<!--
  RescueBox quick start — edit this Markdown for the in-app guide at /demo/quick-start.

  Screenshots: add a line exactly like (file must exist in frontend/demo/):
  {{SCREENSHOT:rescuebox_home.png}}

  Markdown: blank line before "---" (else Setext heading). Blank line before a bullet list
  after a paragraph (else list runs together with the paragraph as one line).
-->

## Overview

RescueBox Desktop connects your browser to **plugins** (AI/ML tools for images, audio, text) to help with forensics  analysis.
You choose a plugin, fill in paths and options, run a **job**, then inspect **results** in **Jobs**


## Navbar 

This navigation bar is useful to navigate for daily use.
{{SCREENSHOT:navbar.png}}


## Home screen

- When you **start RescueBox for the first time**, enter a **unique user id**. It ties jobs to your browser session. 

{{SCREENSHOT:user_id.png}}

The welcome page lists the main actions. 

-- **Browse Plugins** opens the plugin details;

-- **Open Assistant** opens menu based or chat format options to run plugins.


{{SCREENSHOT:rescuebox_home.png}}

---

## Available Plugins description.

1. Open **[Browse Plugins](/models)**.
2. Each plugin card shows **Online** / **Offline**, version, and author.
3. Click **README** for **Plugin Details** — plugin documentation (inputs, outputs, notes).

---

## Running plugins

**RescueBox Assistant** — Open **Assistant**, click the **Menu** button to select a plugin. Complete **Inputs** / **Parameters** (use **Browse** for input paths where shown), then submit and track the job under **Jobs**.

**RescueBox Assistant** — Open **[Assistant](/chatbot)**, **type in a prompt**, to get a input form , Complete **Inputs** / **Parameters** (use **Browse** for input paths where shown), then submit and track the job under **Jobs**.

---

## Jobs

Open **[Jobs](/jobs)** for results and status. Open a job to see **results** (files, text, tables, previews).

- When a job is submitted, **case notes** can be added; they appear in the job output.

- Deleting a job removes its results permanently.

---

## Demo page & sample files

**[Demo](/demo)** includes this guide and a **read-only file explorer** for your demo folder (: **inputs**, **outputs**). 
Click folders to navigate.

---

## Tips

- Form paths are resolved on the **machine running RescueBox** (the server), not automatically on the user’s PC unless they are the same host.
- Plugins that require a **GPU** are labeled in cards and README; CPU-only may be slow.
- Result tables often support **sorting** (column headers) and **row actions** (e.g. open files, previews) — read the short tips under each result view.

---
