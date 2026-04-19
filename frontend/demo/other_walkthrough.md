<!--
  Other plugins & pipeline walkthrough — /demo/other-walkthrough
-->

This guide walks a **demo user** through other interesting plugins like **Age & Gender**,  and **describe images** a **multi-step pipeline** where the assistant runs more than one plugin.

---

## Part A — run using Menu for Plugins

Use the **plugins menu** to run the desired operation.

1. Open **[Assistant](/chatbot)** and click the  **Menu** button.

2. Choose **👤 Age & Gender** plugin

3. the **input form** appears, use **Browse** to pick the **age-gender-classifier** subfolder **inputs**

- [Browse input folders](/demo?walkthrough=other#sample-inputs)

4. **Submit Job**. and review esults.


---

---

## Part B — run using  Chat Assistant prompts

Run the **Describe Images plugin** job by typing a natural-language requests in the chat box (“Type your request”).

1. Open **[Assistant](/chatbot)**.

3. Type in request:

   **describe these photos**.

3. fill **Browse** fields, **input** directory path and **output** directory path, 
choose the default model, and **Submit Job** .

- [Browse input folders](/demo?walkthrough=other#sample-inputs)

4. click on **view job** results after job is completed successfully.

---

## Part C — Pipeline: detect age/gender, filter and summarize 

**Type this prompt** in the chat assistant **[Chat](/chatbot)**.:

**Detect age and gender of these photos and summarize**

1. Run the **first** job (e.g. **`age-gender/predict`**) and collect per-file metadata.

       you set form inputs to "age-gender-classifier/inputs" folder, and click on **Submit Job**"

2.  A **popup** titled **“Filter files before next step”** is shown so that you can narrow files to feed the **next** step.

       you pick **Gender=Male, Age "less than" 10** and **apply filter**

3. Fill the next form for **summarize the images** 

- input is pre populated with the inputs for the previous age-gender task (expected).

- enter output directory for **describe-images/outputs**

4. view the **job results** on completion.

**What to expect:**

**Pipeline workflow** : First run age-gender classifier plugin to scan the images predict age-gender , then match gender/age filter and proceed to describe only the matched images.

---

