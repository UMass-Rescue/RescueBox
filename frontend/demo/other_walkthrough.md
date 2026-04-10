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

- [Browse demo folders](/demo?walkthrough=other#sample-inputs)

5. **Submit Job**, add **case notes** as needed. 

6. After job completes open **View Job** 
    or **[Jobs](/jobs)** to inspect face metadata (age ranges, gender) in the results.

---

---

## Part B — run using  Chat Assistant prompts

Run the **Describe Images plugin** job by typing a natural-language requests in the chat box (“Type your request”).

1. Open **[Assistant](/chatbot)**.
or
2. In the toolbar, click **[🧠 Chat](/chatbot)**.

3. Type in request:

   **describe these photos**.

4. Confirm the assistant proposes the right tool "image_summary/summarize-images"

5. fill **Browse** fields, **input** directory path and **output** directory path, 
choose the default model, and **Submit Job** .

- [Browse demo folders](/demo?walkthrough=other#sample-inputs)

6. click on **view job** results after job is completed successfully.

---

## Part C — Pipeline: age/gender + summarize 

**Type this prompt** in the chat assistant **[🧠 Chat](/chatbot)**.:

**Detect age and gender of these photos and summarize**

1. Run the **first** job (e.g. **`age-gender/predict`**) and collect per-file metadata.

       you set form inputs  "age-gender-classifier/inputs" , **Submit Job**"

2.  A **popup** titled **“Filter files before next step”** is shown so that you can narrow      files to feed the **next** step.

       you enter **Gender=Male, Age<10**

3. Fill the next form for **summarize the images** 

- input is pre populated with the inputs for the previous plugin (expected).

- enter output directory for **describe-images/outputs**

4. view the **job results** on completion.

**What to expect:**

**Pipeline workflow** : First run age-gender classifier plugin to scan the images predict age-gender , then match gender/age filter and proceed to describe only the matched images.

---

