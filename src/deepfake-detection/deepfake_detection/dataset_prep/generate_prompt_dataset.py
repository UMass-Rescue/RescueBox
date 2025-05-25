# This code is an attempt to dynamically create prompts in order to construct a robust deepfake dataset.
# It will create a list of prompts that will be used for image generation. Prompts will be varied on the following attributes:

import random

# Variable Attributes


# Personal Attributes (Stuff about the subject)
possible_genders = ["Male", "Female"]  # Consider wording Man/Woman or Boy/Girl
possible_ages = ["Young", "Middle-aged", "Old"]  # Consider just doing an age range
possible_ethnicities = [
    "Caucasian",
    "African American",
    "East Asian",
    "Hispanic",
    "Middle Eastern",
    "Indian",
]
# possible_ethnicities = ["White", "Black", "Asian", "Latino", "Middle Eastern", "Indian"] #More informal terms
# possible_skin_tones = ["Light", "Medium", "Dark"] #Possible alternative or addition to ethnicities
possible_expressions = ["Happy", "Sad", "Angry", "Surprised", "Neutral"]

# This section should be cognizant of the fact that certain physical characterstics may not correlate well with certain personal attributes.
# Ex. a bald woman may not be a good image to use for a deepfake dataset.
possible_hair_colors = ["Black", "Brown", "Blonde", "Red", "Gray"]
possible_hair_styles = ["Short", "Medium", "Long", "Bald"]
possible_heights = [
    "Short",
    "Medium",
    "Tall",
]  # Consider using a neumerical range of heights or excluding this all together.
possible_body_types = [
    "Slim",
    "Athletic",
    "Average",
    "Overweight",
    "Obese",
]  # Don't really know how to phrase this one nicely

# possible_skin_markings = ["Freckles", "Scars", "Tattoos", "Moles", "Birthmarks"] #Usure about this one

possible_clothing_styles = [
    "Casual",
    "Formal",
    "Business Casual",
]  # maybe consider specific clothing items
accessories = ["Glasses", "Hat", "Jewelry"]

# Image Attributes (Stuff about the image)
possible_backgrounds = [
    "Nature",
    "Urban",
    "Indoor",
    "Outdoor",
]  # maybe split into categories and use subcategories
possible_background_complexity = [
    "Simple",
    "Detailed",
]  # maybe split into categories and use subcategories
possible_lighting_conditions = [
    "Day",
    "Night",
    "Artificial Light",
]  # maybe split into categories and use subcategories
possible_depth_of_field = [
    "Shallow (Blurred Background)",
    "Deep (Everything in Focus)",
]  # maybe split into categories and use subcategories
possible_camera_types = [
    "DSLR",
    "Mirrorless",
    "Smartphone",
    "Webcam",
    "Surveillance Camera",
]  # maybe split into categories and use subcategories

# possible_camera_angles = ["Close-up", "Medium Shot", "Wide Shot"] #Don't know if its good to specify this.
# Looking for shots that have the upper body

image_sizes = [
    512,
    1444,
]  # This is range that will determine the size of the image. Ex. x and y are between images_sizes[0] and images_sizes[1]


# Prompt generation logic.


# Subject attributes
always_present_attributes = []
always_present_attributes.append(possible_genders)
always_present_attributes.append(possible_ages)
always_present_attributes.append(possible_ethnicities)

sometimes_present_attributes = []
sometimes_present_attributes.append(possible_expressions)
sometimes_present_attributes.append(possible_hair_colors)
sometimes_present_attributes.append(possible_hair_styles)
sometimes_present_attributes.append(possible_heights)
sometimes_present_attributes.append(possible_body_types)
sometimes_present_attributes.append(possible_clothing_styles)
sometimes_present_attributes.append(accessories)


def create_subject_attributes(always_present_attributes, sometimes_present_attributes):
    selected_always_present = [
        random.choice(attribute) for attribute in always_present_attributes
    ]
    selected_sometimes_present = [
        random.choice(attribute) if random.random() < 0.25 else None
        for attribute in sometimes_present_attributes
    ]

    subject_attributes = {
        "Gender": selected_always_present[0],
        "Age": selected_always_present[1],
        "Ethnicity": selected_always_present[2],
        "Expression": selected_sometimes_present[0],
        "Hair Color": selected_sometimes_present[1],
        "Hair Style": selected_sometimes_present[2],
        "Height": selected_sometimes_present[3],
        "Body Type": selected_sometimes_present[4],
        "Clothing Style": selected_sometimes_present[5],
        "Accessories": selected_sometimes_present[6],
    }
    return subject_attributes


# subject_attributes = create_subject_attributes(always_present_attributes, sometimes_present_attributes)

# Remove any "None" valued keys
# subject_attributes = {k: v for k, v in subject_attributes.items() if v is not None}

# Image attributes

# image_attributes = {
#     "Background": random.choice(possible_backgrounds),
#     "Background Complexity": random.choice(possible_background_complexity),
#     "Lighting Conditions": random.choice(possible_lighting_conditions),
#     "Depth of Field": random.choice(possible_depth_of_field),
#     "Camera Type": random.choice(possible_camera_types),
#     "Image Size": "{}x{}".format(random.randint(image_sizes[0], image_sizes[1]), random.randint(image_sizes[0], image_sizes[1])),
# }


def create_image_attributes():
    image_x = random.randint(image_sizes[0], image_sizes[1])
    # image y is somewhere between half and twice the x value
    image_y = random.randint(image_x // 2, image_x * 2)
    image_attributes = {
        "Background": random.choice(possible_backgrounds),
        "Background Complexity": random.choice(possible_background_complexity),
        "Lighting Conditions": random.choice(possible_lighting_conditions),
        "Depth of Field": random.choice(possible_depth_of_field),
        "Camera Type": random.choice(possible_camera_types),
        "Image Size": "{}x{}".format(image_x, image_y),
    }
    return image_attributes


# image_attributes = create_image_attributes()

prompts = []
num_prompts = 100  # Number of prompts to generate
# Create a list of prompts
for i in range(num_prompts):
    prompt = "Generate an image of a person using the following: "
    subject_attributes = create_subject_attributes(
        always_present_attributes, sometimes_present_attributes
    )
    image_attributes = create_image_attributes()
    # Remove any "None" valued keys
    subject_attributes = {k: v for k, v in subject_attributes.items() if v is not None}
    prompt += "Subject Attributes: {"
    for key, value in subject_attributes.items():
        prompt += "{}: {}, ".format(key, value)
    prompt = prompt[:-2] + "}, "
    prompt += "Image Attributes: {"
    for key, value in image_attributes.items():
        prompt += "{}: {}, ".format(key, value)
    prompt = prompt[:-2] + "}"
    prompts.append(prompt)

# Print the prompts
for prompt in prompts:
    print(prompt)

# Save the prompts to a file
with open("prompts.txt", "w") as f:
    for prompt in prompts:
        f.write(prompt + "\n")
