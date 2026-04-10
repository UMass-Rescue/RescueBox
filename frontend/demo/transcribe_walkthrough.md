<!--
  Transcribe walkthrough — edit this Markdown for /demo/transcribe-walkthrough

  Screenshots (optional): place PNGs in frontend/demo/ and add:
  {{SCREENSHOT:your_image.png}}
-->



This walkthrough is to run a **Transcribe Audio** rescuebox plugin using the **Menu Assistant**: pick the plugin, fill up the form, submit a job, and view results.

---

### Before you start

1. **User ID** — On the [Home](/) page, enter a **User ID** if prompted. Jobs and chat history are tied to this ID for this browser session.


---

### Step 1 — Use Menu Assistant and run transcribe audio

Click **[Assistant](/chatbot)** in the top nav (or use **Assistant** from the home page).


1. In the Assistant toolbar, clic the  **📋 Menu** button.

2. The **plugin selector menu** appears in the chat area with numbered options.

3. Click **🎤 Transcribe Audio** — it is option **1** in the picker (`audio/transcribe`).

4. The **input form** for transcription loads **inline** in the chat.

---

### Step 2 — Fill inputs and run

An input form opens with typical inputs , a folder of files saved on rescuebox server to process.

{{SCREENSHOT:transcribe-input.png}}

1.  Use **Browse** to select the **"transcribe-audio" folder , then select "inputs"** subfolder.

[Browse demo folders](/demo?walkthrough=transcribe#sample-inputs)

- this subfolder has a mp3 file that will be transcribed and output shown in the job result.



2. Click **Submit Job**

3. Add Case notes , like case number and any reminders you would like to associate with the results.

3. You should see status messages in the chat a **job running** indicator.


4. Wait till "Job Completed Successfully" box provides result with  **view  job button to click**
{{SCREENSHOT:job-completed.png}}

5. Review the **outputs and input details** of this job. In the main jobs page notice the "case notes" in the model column.

---

### Step 3 — Track and open results later.

1. Open **[Jobs](/jobs)** from the nav.

2. For the job # , review case notes for model **audio/transcribe** and view details.

3. If you **delete** this result all information is removed from rescuebox about this job.


---


### See Next

- [Image search walkthrough](/demo/image-search-walkthrough) — run with chat prompt Assistant 

