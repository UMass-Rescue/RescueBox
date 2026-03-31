<!--
  Other plugins & pipeline walkthrough — /demo/other-walkthrough
-->

This guide walks a **demo user** through other interesting plugins like **Age & Gender**, **Detect Deepfakes**,  and finally a **multi-step pipeline** where the assistant runs more than one plugin.

---

## Part A — Tool picker (Plugins)

Use the **numbered tool picker** first so you see each plugin’s form on its own.

### Step 1 — Open Assistant and Plugins

1. Open **[Assistant](/chatbot)**.
2. In the toolbar, click the  **📋 Menu** button.
3. The **tool picker** lists numbered options in the chat area.

---

### Step 2 — Age & Gender (`age-gender/predict`)

1. Choose **👤 Age & Gender** — maps to endpoint **`age-gender/predict`** (typically option **3** in the picker; numbering can vary if your deployment differs).
2. When the **input form** appears inline, use **Browse** to pick the **age-gender-classifier** subfolder **inputs**
3. **Submit Job**, add **case notes** if asked, then open **View Job** or **[Jobs](/jobs)** to inspect face metadata (age ranges, gender) in the results.

---

### Step 3 — Detect Deepfakes (`deepfake_detection/predict`)

1. Open **📋 Menu** again.
2. Choose **🔍 Detect Deepfakes** — **`deepfake_detection/predict`** (often option **4**).
3. Browse and  set inputs at  folder  **deepfake-detection/inputs** , outputs at **deepfake-detection/outputs**,  **submit**, and review the job output.

---

## Part B — Same tools via Assistant Chat prompts

Repeat the plugin jobs by typing a natural-language requests in the chat box (“Type your request”).

1. Open **[Assistant](/chatbot)**.
or
2. In the toolbar, click **[🧠 Chat](/chatbot)**.

**Examples:**

- Ask to **classify age and gender** for faces in a folder, 
   e.g. *Run age and gender on the photos in /tmp*.
- Ask to **check for deepfakes***.

Confirm the assistant proposes the right tool, fill any **Browse** fields, and **Submit Job** as usual.

---

## Part C — Complex pipeline: age/gender + summarize + filter dialog

When a single prompt implies **more than one plugin** in sequence (for example **age/gender** then **describe/summarize images**), RescueBox workflow:

   
**Try this prompt** :

> **Detect age and gender of photos in `/tmp` and summarize**

1. Run the **first** job (e.g. **`age-gender/predict`**) and collect per-file metadata.
  --you set form inputs  "age-gender-classifier/inputs" , **Submit**" add case notes

2. Show a **popup** titled **“Filter files before next step”** so you can narrow which files feed the **next** step.
   --you enter "Gender=Male, Age=<10"


What to expect:

- The assistant plans a **pipeline**: typically **`age-gender/predict`** first, then **`image_summary/summarize-images`** 
- After the age/gender job completes, the **dialog** appears with:
  - Short help text, e.g. *e.g. Gender:Female, Age:>30. Leave empty to use all.*
  - A text field with placeholder like **`Gender:Female, Age:>30`**
  

Then complete the **next** form (output folder, model choice if shown), **submit**, and open the job to read summaries for the filtered set.

---

---

### See also

- [Image summary walkthrough](/demo/image-summary-walkthrough) — Assistant + single-tool summarize  
- [Transcribe walkthrough](/demo/transcribe-walkthrough) — tool picker + audio  
- [Demo home](/demo) · [Quick start](/demo/quick-start)
