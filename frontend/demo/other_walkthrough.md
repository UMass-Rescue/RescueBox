<!--
  Other plugins & pipeline walkthrough — /demo/other-walkthrough
-->

This guide walks a **demo user** through other interesting plugins like **Age & Gender**,  and **describe images** a **multi-step pipeline** where the assistant runs more than one plugin.

---

## Part A — run using Menu for Plugins

Use the **plugins menu** to run the desired operation.

1. Open **[Assistant](/chatbot)**.

2. In the toolbar, click the  **📋 Menu** button.

3. Choose **👤 Age & Gender** plugin

4. When the **input form** appears inline, use **Browse** to pick the **age-gender-classifier** subfolder **inputs**

5. **Submit Job**, add **case notes** as needed. 

6. After job completes open **View Job** 
    or **[Jobs](/jobs)** to inspect face metadata (age ranges, gender) in the results.

---

---

## Part B — run using  Chat Assistant prompts

Run the plugin job by typing a natural-language requests in the chat box (“Type your request”).

1. Open **[Assistant](/chatbot)**.
or
2. In the toolbar, click **[🧠 Chat](/chatbot)**.

3. Type in request:

   **describe these photos**.

4. Confirm the assistant proposes the right tool "image_summary/summarize-images"

5. fill **Browse** fields, **input** directory path and **output** directory path, choose the default model, and **Submit Job** .

6. click on **view job** results after job is completed successfully.

---

## Part C — Pipeline: age/gender + summarize 

When a single prompt implies **more than one plugin** in sequence (for example **age/gender** and then **describe/summarize images**), 

RescueBox runs such workflows in a pipeline:

   
**Type this prompt** in the chat assistant:

**Detect age and gender of these photos and summarize**

1. Run the **first** job (e.g. **`age-gender/predict`**) and collect per-file metadata.

       you set form inputs  "age-gender-classifier/inputs" , **Submit**" add case notes

2. Show a **popup** titled **“Filter files before next step”** so you can narrow which files feed the **next** step.

       you enter "Gender=Male, Age=<10"

3. Fill the next form to **summarize the images** that matched the filter criteria and run

4. view the **job results** on completion.

**What to expect:**

First run age-gender classifier plugin to scan the images that match gender/age filter and then summarize these matched images.


---

---

### See also

- [Image summary walkthrough](/demo/image-search-walkthrough) — Assistant + single-tool summarize  
- [Transcribe walkthrough](/demo/transcribe-walkthrough) — tool picker + audio  
- [Demo home](/demo) · [Quick start](/demo/quick-start)
