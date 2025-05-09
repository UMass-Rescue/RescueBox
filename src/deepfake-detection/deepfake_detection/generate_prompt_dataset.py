# This code is an attempt to dynamically create prompts in order to construct a robust deepfake dataset.
# It will create a list of prompts that will be used for image generation. Prompts will be varied on the following attributes:

import random

# Variable Attributes


# Personal Attributes (Stuff about the subject)
possible_genders = ["Male", "Female"]  # Consider wording Man/Woman or Boy/Girl
possible_ages = [
    "Young (15-20)",
    "Young Adult (20-30)",
    "Adult (30-40)",
    "Middle Aged (40-64)",
    "Old (65+)",
]  # Consider using a numerical range of ages
possible_ethnicities = [
    "African Descent",
    "European",
    "American (Non-European)",
    "East Asian",
    "South Asian",
    "Hispanic",
    "Middle Eastern",
    "South American",
    "Southeast Asian",
    "Mixed",
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
    "Average",
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
    "Casual Wear",
    "Formal Wear",
    "Business Attire",
    "Business Casual",
    "Athletic Wear",
    "Streetwear",
    "Winter Wear",
    "Summer Wear",
    "Uniform",
]  # maybe consider specific clothing items
accessories = [
    "Eyewear",
    "Headwear",
    "Jewelry",
    "Bags or Backpacks",
    "Smartphone",
    "Face Coverings",
    "Outerwear Accessories",
    "Hair Accessories",
    "Watches or Wrist Accessories",
    "Headphones",
    "Hand Accessories",
]


# Image Attributes (Stuff about the image)
possible_backgrounds = [
    "Indoor",
    "Outdoor",
]  # maybe split into categories and use subcategories
indoor_backgrounds = [
    "Living Room",
    "Bedroom",
    "Office",
    "Classroom",
    "Kitchen",
    "Bathroom",
    "Gym",
    "Library",
    "Hallway",
    "Studio",
    "Conference Room",
    "Garage",
    "Basement",
    "Dining Room",
    "Lobby",
    "Elevator Interior",
    "Waiting Room",
    "Retail Store Interior",
    "Storage Room",
    "Restaurant Interior",
    "Auditorium",
    "College Campus",
]
outdoor_backgrounds = [
    "Urban Street",
    "Park",
    "Forest",
    "Beach",
    "Mountain Path",
    "Countryside",
    "City Skyline",
    "Rooftop",
    "Train Station Platform",
    "Outdoor Cafe",
    "Playground",
    "Open Field",
    "Residential Neighborhood",
    "Riverbank",
    "Sparse Parking Lot",
    "Street Market",
    "Suburban Sidewalk",
    "Snowy Landscape",
    "Garden",
]
possible_background_complexity = [
    "Simple",
    "Detailed",
]  # maybe split into categories and use subcategories
possible_lighting_conditions = [
    "Dim",
    "Bright",
    "Natural",
    "Artificial",
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
]  # maybe split into categories and use subcategories
possible_camera_angles = [
    "Close-up (Head and Shoulders)",
    "Medium Shot (Upper Body and Some Legs)",
    "Wide Shot (Full Body)",
    "Dynamic Angle (Non-Head-On, e.g., 45-degree Side Profile)",
]

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
always_present_attributes.append(possible_clothing_styles)
always_present_attributes.append(accessories)

sometimes_present_attributes = []
sometimes_present_attributes.append(possible_expressions)
sometimes_present_attributes.append(possible_hair_colors)
sometimes_present_attributes.append(possible_hair_styles)
sometimes_present_attributes.append(possible_heights)
sometimes_present_attributes.append(possible_body_types)


def create_subject_attributes(always_present_attributes, sometimes_present_attributes):
    selected_always_present = [
        random.choice(attribute) for attribute in always_present_attributes
    ]
    selected_sometimes_present = [
        random.choice(attribute) if random.random() < 0.33 else None
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
        "Clothing Style": selected_always_present[3],
        "Accessories": selected_always_present[4],
    }
    # For accessories, keep adding additional accessories with a 20% chance until no more are added
    while random.random() < 0.2:
        additional_accessory = random.choice(accessories)
        if additional_accessory not in subject_attributes["Accessories"]:
            subject_attributes["Accessories"] += f", {additional_accessory}"
    # If ethnicity is "Mixed", replace with Mixed (randomly select 2 from the list)
    if subject_attributes["Ethnicity"] == "Mixed":
        selected_ethnicities = random.sample(
            [eth for eth in possible_ethnicities if eth != "Mixed"], 2
        )
        subject_attributes["Ethnicity"] = (
            f"Mixed ({selected_ethnicities[0]} and {selected_ethnicities[1]})"
        )

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
    background_type = random.choice(possible_backgrounds)
    background = ""
    if background_type == "Indoor":
        background = random.choice(indoor_backgrounds)
    else:
        background = random.choice(outdoor_backgrounds)

    image_attributes = {
        "Background": background,
        "Background Complexity": random.choice(possible_background_complexity),
        "Lighting Conditions": random.choice(possible_lighting_conditions),
        "Depth of Field": random.choice(possible_depth_of_field),
        "Camera Type": random.choice(possible_camera_types),
        "Camera Angle": random.choice(possible_camera_angles),
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
    if random.random() < 0.5:
        prompt += (
            " Ensure the final image does not have any dominant color wash or filter."
        )
    else:
        prompt += " Ensure you use a neutral/cool color temperature."
    prompts.append(prompt)

# Print the prompts
for prompt in prompts:
    print(prompt)

# Save the prompts to a file
with open("prompts.txt", "w") as f:
    for prompt in prompts:
        f.write(prompt + "\n")
