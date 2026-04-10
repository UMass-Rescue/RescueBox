<!--
  Image search walkthrough — /demo/image-search-walkthrough
-->

Run **search Images**  from the chat **Assistant** using a **natural-language prompt**. 

- The **Search Images** plugin is a ML based app that scan images and provides descriptions. 

- you provide a query string to find an image that matches this string.
  example : **search these images for a small child**

- The rescuebox assistant proposes the tool; you confirm inputs, submit the job, then view results.

---

---

### Step 1 — Open Assistant

1. Go to **[Assistant](/chatbot)** (nav or Home).

2. click on **chat** button.

---

### Step 2 — Chat prompt for Search Images

1. In the chat input, ("Type your request") type a request prompt, for example:
   - **search these images for a small child**
{{SCREENSHOT:chat.png}}

2. Send the message. The chat assistant should respond with an input form for the plugin.

note: if you type something not understood by rescuebox, you should see a help output

---

### Step 3 — Fill the form and submit

1. Use **Browse** to choose a **Directory Path** folder (or files).
 
  pick the **search-images** subfolder **inputs** , containing images to run this plugin.

  [Browse demo folders](/demo?walkthrough=image-search#sample-inputs)

2. For **Text query to find the most similar images** input,

  if its not already set type "**small child**"

3. For other inputs keep the defaults.

4. Click **Submit Job**. Add **case notes** when prompted.

5. Wait for the **Job completed sucessfully** message; use **View Job** to open the job detail page.

---

### Step 4 — Job Results

1. **[Jobs](/jobs)** — View the run details

2. Open the job to view **outputs**. A list of top-5 likely matches in images is returned. 

NOTE: Some of these "**low similiarity**" rows could be incorrect, for example "small child" is replaced with "age < 10"

---

### See Next

- [Next walkthrough](/demo/other-walkthrough) — age/gender, summarize images, multi-step pipeline.  

