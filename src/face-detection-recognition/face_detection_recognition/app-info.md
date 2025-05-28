# FaceMatch

FaceMatch is an advanced system designed for identifying facial matches within an image database. This platform enables users to create comprehensive image databases and facilitates efficient searches to find matches for individuals by uploading query images.

## 1. Creating a Database of Individuals

To populate a database with images, utilize the **Bulk Upload** link.

### Inputs

- **Image Directory:** A directory containing images to be added to the database.

    - For multiple directories, repeat the upload process sequentially, ensuring that each previous directory has been successfully added before proceeding.

- **Choose collection:** A dropdown menu to select either an existing collection to upload the images to or the option to create a new collection.

- **New Collection Name (Optional):** A text input field to enter the name for the new collection. Don't include underscores.

> NOTE: 
> Use only if you would like to create a new collection.
> Ensure that the "Create a new collection" option is selected in 'Choose Collection' dropdown.

### Outputs

- Refer to the results section for the status of the upload process.

## 2. Search for matches 

- To search for facial matches within the existing database, use the **Find Face Bulk** link.

### Inputs

- **Query Directory:** query images to be compared against the database.

- **Collection Name:** Choose the collection to search within.

- **Similarity Threshold:** A threshold value to determine the minimum similarity score required for a match to be considered a positive match. 

Default value provides a tradeoff between two things, it tries to ensure we find the right person when they are in the database while also avoiding finding someone when they aren't there.  This setting can be adjusted depending on whether you want to focus more on finding as many matches as possible (decrease threshold) or being extra careful to avoid wrong ones (increase threshold).


**Guide to tuning threshold:** 
- Increase the threshold value to narrow down the search to higher similarity faces. 

   **Sample case:** You could increase threshold if the search image is clear and up-to-date, so you can look for a match with a high degree of confidence.

- Decrese the threshold if you wish to broaden the search to include more variability in faces. 

    **Sample case:** You could decrease threshold if the search image is blurry or outdated, so you are open to some variability in the possible matches.

### Outputs 

- Refer to the results section for the matches found within the database. May have to click dropdown arrow to view.

## 3. Search for matches for multiple images at once

### Inputs

 - **Query Directory** Path to directory of query images to be compared against the database.

 - **Collection Name:** Choose the collection to search within

 - **Similarity Threshold:** A threshold value to determine the minimum similarity score required for a match to be considered a positive match. 

 ### Outputs 

- Refer to the results section. Current output is the doubly nested array of outputs where each subarray contains the matches for each query. Empty array indicates no matches found. Further changes to Rescuebox likely required to flesh out this output.