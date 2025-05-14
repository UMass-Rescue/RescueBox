import bert_score
import matplotlib.pyplot as plt
import numpy as np

# Human-written summaries
human_summaries = [
    "A car is driving straight on a multi-lane road during the daytime when an SUV in the adjacent right lane abruptly swerves to the left, colliding with the car and causing a crash. After which people are seen coming out of the car to check on each other and assess the accident situation.",
    "Two girls kick things off with a fun game of 'Never Have I Ever.' One of them introduces herself and her friend, Ms. Puram, who’s already busy scrolling for questions to ask. As the game rolls on, Ms. Puram throws out playful prompts like 'Have you ever broken a bone?', 'Traveled solo?', and even 'Have you Googled yourself?' The vibe is super relaxed, they’re clearly just enjoying the moment, chatting comfortably, and having a good time together while filming.",
    "In the scene, a girl is seen walking casually with a bag when, out of nowhere, three men ambush her. Judging by their old-school cowboy-style outfits, it feels like the setting might be from the 70s or 80s. The men quickly cover her mouth, likely to keep her from screaming, and tie her hands to stop her from fighting back. A bag is then placed over her head to block her vision, and they wrap her in rope before dragging her to a cart. She’s forced inside, clearly being taken away against her will. The whole moment is intense and unsettling.",
    "The scene opens with a sudden, shocking moment, out of nowhere, a man in a yellow shirt shoots a woman wearing a burgundy jacket. She also has a gun and tries to fight back, but he gets to her first. Nearby, there’s another man who’s tied up, clearly struggling to break free as the chaos unfolds. As the woman falls, the tied-up man finally manages to escape, rushes at the shooter from behind, and stabs him in the stomach. Once it's over, he looks at the woman in burgundy, devastated. He drops to his knees, overwhelmed with emotion, crying as he stares at her lifeless body. The entire moment is intense, emotional, and deeply tragic.",
    "As the elevator doors begin to close, a woman receives a call that clearly rattles her—she drops her phone in panic. The caller, who she identifies as Officer Burke, urgently tries to warn her about something, but the connection is poor, making it hard for her to understand him. He manages to tell her that a man with hooks is going to kill her. The tension rises immediately, especially since the man standing right behind her is holding hooks in his hand. Realizing this, she panics and tries to escape, but in the struggle, her braid gets tangled in the man's hooks. She desperately tries to pull away, but in the chaos, her head gets caught between the elevator doors. Two people outside try to help, but it’s too late—the elevator moves, and in a horrifying moment, it decapitates her. The people inside scream, stunned and horrified by what just happened.",
]

# LLM-generated summaries
llm_summaries = [
    "The video depicts a collision between a silver car and a dark-colored minivan in a parking lot. Initially, a silver car is rapidly moving across a cracked asphalt surface before colliding with the minivan. Following the impact, multiple individuals – a man and a woman – are seen exiting the damaged minivan, with one man attempting to open the silver car’s driver-side door. Ultimately, police officers arrive to investigate the scene after the collision.",
    "The video features two young women, Purum and her friend, engaging in a “Never Have I Ever” style game. Visually, they’re sitting together, smiling and interacting with each other. The audio reveals a lighthearted and silly conversation as they answer increasingly personal questions. They recount humorous and surprising experiences, like breaking a bone (but not a *broken* one), Googling themselves, laughing so hard they spit out their drink, and attending parties where people pretend to know them. Overall, the video is a fun, spontaneous, and relatable glimpse into a casual conversation and a silly game.",
    "This video appears to be a fragmented and somewhat surreal collection of scenes, drawing heavily on Western, adventure, and potentially thriller tropes. Recurring elements include men in hats, women in red clothing (often distressed), and moments of struggle, restraint, and tense encounters. The visuals shift between Western landscapes, dimly lit interiors, and even jungle and cave environments, suggesting a narrative that is loosely assembled and possibly exploring themes of conflict, rescue, and potentially danger. It feels like a patchwork of different stories and genres, creating a disjointed and intriguing viewing experience.",
    "The video appears to depict a tense, possibly violent, incident unfolding within a classroom setting. Initially, we see a man in a gray suit, often with gray hair, frequently observing, examining objects, and appearing concerned or distressed – sometimes peering intently, sometimes slumped over a desk. This individual is often in dim lighting. A significant portion of the video focuses on a young woman who is ultimately found injured and motionless on the classroom floor, covered in blood, suggesting she has been shot. Evidence of a struggle is present, with scattered debris and a handgun nearby. The final frames depict a weathered, serious man with gray hair, seemingly observing the aftermath, adding an element of quiet reflection to the chaotic scene. Essentially, the video seems to portray an event, possibly a shooting, within a classroom, with an individual observing the scene, while a young woman suffers serious injury and remains motionless on the floor.",
    "This video depicts a disturbing and fragmented encounter. Visually, we see recurring shots of a man – likely Nora – in a confined, metallic space, often near a metal frame or wall, with a distressed expression. The audio reveals a frantic, disoriented individual named Nora, repeatedly asking “Who is this?” and expressing fear – “hooks is going to kill you.” The audio also contains nonsensical phrases like We’re imp car… We’re all impplayful, suggesting a possible mental health crisis or altered state of consciousness. The overall impression is one of a person trapped, possibly experiencing a delusion or hallucination, and desperately trying to communicate with an unknown figure. Do you want me to focus on a specific aspect of this summary, such as the potential psychological themes or the significance of the metallic setting?",
]

precisions, recalls, f1s = [], [], []
for i, (human, llm) in enumerate(zip(human_summaries, llm_summaries), start=1):
    P, R, F1 = bert_score.score([llm], [human], lang="en", verbose=False)
    p, r, f1 = P.item(), R.item(), F1.item()
    precisions.append(p)
    recalls.append(r)
    f1s.append(f1)
    print(f"Pair {i}:")
    print(f"  Precision: {p:.4f}")
    print(f"  Recall:    {r:.4f}")
    print(f"  F1 Score:  {f1:.4f}")
    print()

# Print average scores
avg_precision = np.mean(precisions)
avg_recall = np.mean(recalls)
avg_f1 = np.mean(f1s)

print("Average Scores:")
print(f"  Avg Precision: {avg_precision:.4f}")
print(f"  Avg Recall:    {avg_recall:.4f}")
print(f"  Avg F1 Score:  {avg_f1:.4f}")

# Plotting
x_labels = [f"Pair {i+1}" for i in range(len(human_summaries))]
x = np.arange(len(x_labels))
width = 0.25

plt.figure(figsize=(12, 6))
plt.bar(x - width, precisions, width, label="Precision")
plt.bar(x, recalls, width, label="Recall")
plt.bar(x + width, f1s, width, label="F1 Score")

plt.xlabel("Summary Pairs")
plt.ylabel("Score")
plt.title("BERTScore Evaluation: Human vs LLM Summaries")
plt.xticks(x, x_labels)
plt.ylim(0, 1)
plt.legend()
plt.grid(True, axis="y", linestyle="--", alpha=0.7)
plt.tight_layout()
plt.show()
