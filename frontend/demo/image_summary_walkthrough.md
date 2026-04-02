<!--
  Image summary walkthrough — /demo/image-summary-walkthrough
-->

Run **describe Images** (`image_summary/summarize-images`) from the **Assistant** using a **natural-language prompt**. 

The model proposes the tool; you confirm inputs, submit the job, then open results.

---

---

### Step 1 — Open Assistant

1. Go to **[Assistant](/chatbot)** (nav or Home).
2. click on **chat** button.

---

### Step 2 — Prompt for image summary

1. In the chat input, ("Type your request") type a request prompt, for example:
   - **summarize the images in /tmp**
   - or **describe photos under the /data/case123**
2. Send the message. The assistant should respond with an input form for Describe Images plugin  **`image_summary/summarize-images`**.

note: if you type something not understood by rescuebox, you should see a help output

---

### Step 3 — Fill the form and submit

1. Use **Browse** to choose an **inputs** folder (or files) on the server—e.g. under your **demo** tree, pick the **describe-images** subfolder **inputs** ,sample images for this plugin.
2. Use the next **Browse** button and select **outputs** subfolder.
3. This plugin provides a list of AI model to use for this run. see list , select the first one for quick output.
4. Click **Submit Job**. Add **case notes** if prompted.
5. Wait for the **Job completed** message; use **View Job** to open the job detail page.

---

### Step 4 — Job Results

1. **[Jobs](/jobs)** — View the run details by endpoint **image_summary/summarize-images**, case notes.
2. Open the job to read **summaries / outputs**. Deleting the job removes its stored results.

---

### See also

- [Other walkthrough](/demo/other-walkthrough) — age/gender, deepfakes, Assistant prompts, multi-step filter dialog  
- [Demo](/demo) · [Transcribe walkthrough](/demo/transcribe-walkthrough) · [Quick start](/demo/quick-start)
