# 🪖 heltect

**AI-Powered Safety Helmet Detection**

[English](README.md) | [ภาษาไทย](README.th.md)

## Overview

**heltect** is an AI-powered safety helmet detection system designed to improve workplace safety through Computer Vision and Object Detection technologies.

The project primarily focuses on detecting whether workers are wearing safety helmets. It also explores helmet color classification and zone-based verification to identify potential safety violations and notify responsible personnel.

## Project Goals

- Apply AI and Computer Vision to support workplace safety.
- Develop and evaluate a safety helmet detection model.
- Explore helmet color classification using OpenCV.
- Verify helmet usage and color compliance based on area-specific safety requirements.
- Integrate detection results with an automated alert notification system.


## Features

- **Helmet Detection** — Detect safety helmets and identify potential violations of helmet-wearing requirements.
- **Color Classification** — Analyze and classify helmet colors using image processing techniques.
- **Zone Verification** — Verify helmet colors against safety requirements for designated work areas.
- **Alert Notification** — Notify safety personnel through LINE when a potential safety violation is detected.

*These features represent the proposed system and may be refined based on development and testing results.*

## How It Works

The proposed system follows four main steps:

1. **Detect** — Detect safety helmets using an AI model.
2. **Classify** — Analyze and classify helmet colors using OpenCV.
3. **Verify** — Check helmet usage and color compliance with area-specific safety requirements.
4. **Alert** — Send notifications through LINE when a potential safety violation is detected.

## Tech Stack

| Technology | Purpose |
|---|---|
| Python | System development and integration |
| YOLO11 | AI-based object detection |
| Roboflow | Dataset sourcing and preparation |
| OpenCV | Image processing and helmet color classification |
| LINE Messaging API | Automated safety alert notifications |

## Dataset

This project uses the **Safety Helmet Dataset** provided by Helmet TF on Roboflow Universe for training and evaluating the safety helmet detection model.

| Information | Details |
|---|---|
| Dataset | [Safety Helmet Dataset](https://universe.roboflow.com/helmet-tf/safety-helmet-4mhdt) |
| Author | Helmet TF |
| Publisher | Roboflow Universe |
| Published | April 2022 |
| License | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) |
| Accessed | October 10, 2026 |

The dataset is used in accordance with the Creative Commons Attribution 4.0 International license. Credit is given to the original author, and any modifications made during dataset preparation will be documented.

### Dataset Citation

Helmet TF. (2022). *Safety Helmet Dataset*. Roboflow Universe. https://universe.roboflow.com/helmet-tf/safety-helmet-4mhdt


## Project Status

🚧 **In Development**

heltect is an academic prototype currently under development and testing. Model performance, full system integration, and real-world reliability have not yet been validated.

Implementation details, experimental results, and usage instructions will be added as the project progresses.

## Development Team

heltect is collaboratively developed by students enrolled in **INT182 — Data Science and Artificial Intelligence Fundamentals**, with responsibilities divided into two sub-teams.

### AI Team
*Model Development & Evaluation*

Responsible for dataset preparation, AI model training and testing, performance analysis, and model evaluation.

1. [pasayakorn](https://github.com/pasayakorn)
2. [Millerz17](https://github.com/Millerz17)
3. [109Suthairut](https://github.com/109Suthairut)

### Solution Team
*System Development & Integration*

Responsible for integrating the AI model into the system, implementing helmet color classification, zone-based safety verification, and alert notifications.

1. [poommer](https://github.com/poommer)
2. [nyxfelis](https://github.com/nyxfelis)



## License

To be determined.