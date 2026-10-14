# Existing Project Research Findings

- **Session ID:** `72356611-f0ef-4258-9ed1-17feb57880c3`
- **Total Findings:** 6
- **Search Queries Run:** `coffee leaf disease detection tensorflow`, `coffee leaf disease dataset`, `coffee leaf disease`, `ROCOLE`

## Notes
Search queries run: 1) 'coffee leaf disease detection tensorflow' (GitHub); 2) 'coffee leaf disease dataset' (GitHub); 3) 'coffee leaf disease' (GitHub and Hugging Face models); 4) 'coffee leaf disease' (Hugging Face datasets); 5) 'ROCOLE' (Hugging Face datasets). Most missing fields were evaluation results and detailed limitations. All tool calls succeeded within budget.

## Findings

### 1. Coffee-Image-Classification (Github Repository)
- **URL:** [https://github.com/randellmwania/Coffee-Image-Classification](https://github.com/randellmwania/Coffee-Image-Classification)
- **Problem Solved:** Detect coffee leaf diseases (Rust, Cercospora, Phoma, Healthy) from images
- **Input / Output:** Input: photo of a coffee leaf; Output: disease label
- **Dataset:** Arabica coffee leaf images from Mendeley datasets and web scraping (links in README)
- **Model & Architecture:** CNN models (specific architecture not detailed)
- **Method:** Convolutional Neural Network with data augmentation and preprocessing
- **Evaluation & Results:** not found
- **Repository Details:** Stars: 2 | License: not found | Language: Jupyter Notebook | Last Update: 2024-02-14T08:07:29Z | Archived: False
- **Reproducibility:** Code and notebooks provided in repository (README indicates use of Jupyter notebooks)
- **Known Limitations:** not found

**Field Sources:**
- *dataset*: `[github_get_readme | https://api.github.com/repos/randellmwania/Coffee-Image-Classification/readme | 2026-10-07T13:15:13.527919+00:00]`
- *evaluation_and_results*: `not found`
- *input_output*: `[github_get_readme | https://api.github.com/repos/randellmwania/Coffee-Image-Classification/readme | 2026-10-07T13:15:13.527919+00:00]`
- *known_limitations*: `not found`
- *method*: `[github_get_readme | https://api.github.com/repos/randellmwana/Coffee-Image-Classification/readme | 2026-10-07T13:15:13.527919+00:00]`
- *model_and_architecture*: `[github_get_readme | https://api.github.com/repos/randellmwania/Coffee-Image-Classification/readme | 2026-10-07T13:15:13.527919+00:00]`
- *problem_solved*: `[github_get_readme | https://api.github.com/repos/randellmwania/Coffee-Image-Classification/readme | 2026-10-07T13:15:13.527919+00:00]`
- *repository_details*: `[github_get_repository | https://api.github.com/repos/randellmwania/Coffee-Image-Classification | 2026-10-07T13:15:11.103902+00:00]`
- *reproducibility*: `[github_get_readme | https://api.github.com/repos/randellmwania/Coffee-Image-Classification/readme | 2026-10-07T13:15:13.527919+00:00]`

### 2. Coffee_Recognize (Github Repository)
- **URL:** [https://github.com/Lucs1590/Coffee_Recognize](https://github.com/Lucs1590/Coffee_Recognize)
- **Problem Solved:** Detect coffee leaf disease and quantify contamination percentage
- **Input / Output:** Input: coffee leaf image; Output: disease label and severity percentage
- **Dataset:** not found
- **Model & Architecture:** Convolutional Neural Network based object detector (specific architecture not detailed)
- **Method:** CNN object detection with OpenCV, k-means, and AFSoft for severity estimation
- **Evaluation & Results:** Average precision 81.5% for detection; no significant statistical difference for severity estimation
- **Repository Details:** Stars: 10 | License: GPL-2.0 | Language: TypeScript | Last Update: 2026-02-03T22:12:54Z | Archived: False
- **Reproducibility:** Instructions to install dependencies and run via Ionic framework provided in README
- **Known Limitations:** not found

**Field Sources:**
- *dataset*: `not found`
- *evaluation_and_results*: `[github_get_readme | https://api.github.com/repos/Lucs1590/Coffee_Recognize/readme | 2026-10-07T13:15:17.196146+00:00]`
- *input_output*: `[github_get_readme | https://api.github.com/repos/Lucs1590/Coffee_Recognize/readme | 2026-10-07T13:15:17.196146+00:00]`
- *known_limitations*: `not found`
- *method*: `[github_get_readme | https://api.github.com/repos/Lucs1590/Coffee_Recognize/readme | 2026-10-07T13:15:17.196146+00:00]`
- *model_and_architecture*: `[github_get_readme | https://api.github.com/repos/Lucs1590/Coffee_Recognize/readme | 2026-10-07T13:15:17.196146+00:00]`
- *problem_solved*: `[github_get_readme | https://api.github.com/repos/Lucs1590/Coffee_Recognize/readme | 2026-10-07T13:15:17.196146+00:00]`
- *repository_details*: `[github_get_repository | https://api.github.com/repos/Lucs1590/Coffee_Recognize | 2026-10-07T13:15:15.006561+00:00]`
- *reproducibility*: `[github_get_readme | https://api.github.com/repos/Lucs1590/Coffee_Recognize/readme | 2026-10-07T13:15:17.196146+00:00]`

### 3. coffee-leaf-diseases (Github Repository)
- **URL:** [https://github.com/iam-stanis/coffee-leaf-diseases](https://github.com/iam-stanis/coffee-leaf-diseases)
- **Problem Solved:** Classify coffee leaf disease from photos
- **Input / Output:** Input: leaf photo; Output: disease label
- **Dataset:** Kaggle coffee leaf diseases dataset, RoCoLe dataset, Ugandan Coffee dataset (links in README)
- **Model & Architecture:** ResNet50 and ResNet101
- **Method:** Transfer learning with ResNet CNNs
- **Evaluation & Results:** not found
- **Repository Details:** Stars: 0 | License: CC0-1.0 | Language: Jupyter Notebook | Last Update: 2025-10-10T09:28:37Z | Archived: False
- **Reproducibility:** Jupyter notebooks provided; dataset links included
- **Known Limitations:** not found

**Field Sources:**
- *dataset*: `[github_get_readme | https://api.github.com/repos/iam-stanis/coffee-leaf-diseases/readme | 2026-10-07T13:15:20.087970+00:00]`
- *evaluation_and_results*: `not found`
- *input_output*: `[github_get_readme | https://api.github.com/repos/iam-stanis/coffee-leaf-diseases/readme | 2026-10-07T13:15:20.087970+00:00]`
- *known_limitations*: `not found`
- *method*: `[github_get_readme | https://api.github.com/repos/iam-stanis/coffee-leaf-diseases/readme | 2026-10-07T13:15:20.087970+00:00]`
- *model_and_architecture*: `[github_get_readme | https://api.github.com/repos/iam-stanis/coffee-leaf-diseases/readme | 2026-10-07T13:15:20.087970+00:00]`
- *problem_solved*: `[github_get_readme | https://api.github.com/repos/iam-stanis/coffee-leaf-diseases/readme | 2026-10-07T13:15:20.087970+00:00]`
- *repository_details*: `[github_get_repository | https://api.github.com/repos/iam-stanis/coffee-leaf-diseases | 2026-10-07T13:15:18.669204+00:00]`
- *reproducibility*: `[github_get_readme | https://api.github.com/repos/iam-stanis/coffee-leaf-diseases/readme | 2026-10-07T13:15:20.087970+00:00]`

### 4. arabica-coffee-leaf-disease-efficientnet-b0 (Huggingface Model)
- **URL:** [https://huggingface.co/Huyt/arabica-coffee-leaf-disease-efficientnet-b0](https://huggingface.co/Huyt/arabica-coffee-leaf-disease-efficientnet-b0)
- **Problem Solved:** Classify Arabica coffee leaf disease from images
- **Input / Output:** Input: image crop of coffee leaf; Output: disease label (5 classes)
- **Dataset:** Project-AgML/arabica_coffee_leaf_disease_classification
- **Model & Architecture:** EfficientNet B0 (4.0M parameters) fine‑tuned
- **Method:** Transfer learning with timm EfficientNet on deduplicated dataset
- **Evaluation & Results:** Test accuracy 0.9911, macro‑F1 0.9941 (honest split)
- **Repository Details:** Stars: not found | License: cc-by-4.0 | Language: not found | Last Update: 2026-07-17T09:22:07.000Z | Archived: False
- **Reproducibility:** Model card lists dataset and training details; includes tags for timm library
- **Known Limitations:** Dataset contains high duplication; model trained on deduplicated split may not reflect original large size

**Field Sources:**
- *dataset*: `[hf_get_details | https://huggingface.co/api/models/Huyt/arabica-coffee-leaf-disease-efficientnet-b0 | 2026-10-07T13:15:22.078791+00:00]`
- *evaluation_and_results*: `[hf_get_details | https://huggingface.co/api/models/Huyt/arabica-coffee-leaf-disease-efficientnet-b0 | 2026-10-07T13:15:22.078791+00:00]`
- *input_output*: `[hf_get_details | https://huggingface.co/api/models/Huyt/arabica-coffee-leaf-disease-efficientnet-b0 | 2026-10-07T13:15:22.078791+00:00]`
- *known_limitations*: `[hf_get_details | https://huggingface.co/api/models/Huyt/arabica-coffee-leaf-disease-efficientnet-b0 | 2026-10-07T13:15:22.078791+00:00]`
- *method*: `[hf_get_details | https://huggingface.co/api/models/Huyt/arabica-coffee-leaf-disease-efficientnet-b0 | 2026-10-07T13:15:22.078791+00:00]`
- *model_and_architecture*: `[hf_get_details | https://huggingface.co/api/models/Huyt/arabica-coffee-leaf-disease-efficientnet-b0 | 2026-10-07T13:15:22.078791+00:00]`
- *problem_solved*: `[hf_get_details | https://huggingface.co/api/models/Huyt/arabica-coffee-leaf-disease-efficientnet-b0 | 2026-10-07T13:15:22.078791+00:00]`
- *repository_details*: `[hf_get_details | https://huggingface.co/api/models/Huyt/arabica-coffee-leaf-disease-efficientnet-b0 | 2026-10-07T13:15:22.078791+00:00]`
- *reproducibility*: `[hf_get_details | https://huggingface.co/api/models/Huyt/arabica-coffee-leaf-disease-efficientnet-b0 | 2026-10-07T13:15:22.078791+00:00]`

### 5. vit-coffee-leaf-diseases (Huggingface Model)
- **URL:** [https://huggingface.co/brainer-fp66/vit-coffee-leaf-diseases](https://huggingface.co/brainer-fp66/vit-coffee-leaf-diseases)
- **Problem Solved:** Classify coffee leaf disease using Vision Transformer
- **Input / Output:** Input: coffee leaf image; Output: disease label
- **Dataset:** brainer-fp66/coffee-leaf-diseases
- **Model & Architecture:** Vision Transformer (google/vit-base-patch16-224-in21k) fine‑tuned
- **Method:** Fine‑tuning of pre‑trained ViT using Transformers Trainer
- **Evaluation & Results:** not found
- **Repository Details:** Stars: not found | License: apache-2.0 | Language: not found | Last Update: 2025-08-17T16:42:05.000Z | Archived: False
- **Reproducibility:** Training hyperparameters and framework versions listed in model card
- **Known Limitations:** not found

**Field Sources:**
- *dataset*: `[hf_get_details | https://huggingface.co/api/models/brainer-fp66/vit-coffee-leaf-diseases | 2026-10-07T13:15:23.540171+00:00]`
- *evaluation_and_results*: `not found`
- *input_output*: `[hf_get_details | https://huggingface.co/api/models/brainer-fp66/vit-coffee-leaf-diseases | 2026-10-07T13:15:23.540171+00:00]`
- *known_limitations*: `not found`
- *method*: `[hf_get_details | https://huggingface.co/api/models/brainer-fp66/vit-coffee-leaf-diseases | 2026-10-07T13:15:23.540171+00:00]`
- *model_and_architecture*: `[hf_get_details | https://huggingface.co/api/models/brainer-fp66/vit-coffee-leaf-diseases | 2026-10-07T13:15:23.540171+00:00]`
- *problem_solved*: `[hf_get_details | https://huggingface.co/api/models/brainer-fp66/vit-coffee-leaf-diseases | 2026-10-07T13:15:23.540171+00:00]`
- *repository_details*: `[hf_get_details | https://huggingface.co/api/models/brainer-fp66/vit-coffee-leaf-diseases | 2026-10-07T13:15:23.540171+00:00]`
- *reproducibility*: `[hf_get_details | https://huggingface.co/api/models/brainer-fp66/vit-coffee-leaf-diseases | 2026-10-07T13:15:23.540171+00:00]`

### 6. arabica_coffee_leaf_disease_classification (Huggingface Dataset)
- **URL:** [https://huggingface.co/datasets/Project-AgML/arabica_coffee_leaf_disease_classification](https://huggingface.co/datasets/Project-AgML/arabica_coffee_leaf_disease_classification)
- **Problem Solved:** Provides a large labeled dataset for Arabica coffee leaf disease classification
- **Input / Output:** Input: images of coffee leaves; Output: class label (5 disease/health classes)
- **Dataset:** not applicable
- **Model & Architecture:** not applicable
- **Method:** not applicable
- **Evaluation & Results:** not applicable
- **Repository Details:** Stars: not found | License: cc-by-4.0 | Language: not found | Last Update: 2026-07-07T19:51:34.000Z | Archived: False
- **Reproducibility:** Dataset card includes download scripts, splits, and feature schema
- **Known Limitations:** High duplication of images (93.6% duplicate rows) noted in related model cards

**Field Sources:**
- *dataset*: `not applicable`
- *evaluation_and_results*: `not applicable`
- *input_output*: `[hf_get_details | https://huggingface.co/api/datasets/Project-AgML/arabica_coffee_leaf_disease_classification | 2026-10-07T13:15:25.779315+00:00]`
- *known_limitations*: `not applicable`
- *method*: `not applicable`
- *model_and_architecture*: `not applicable`
- *problem_solved*: `[hf_get_details | https://huggingface.co/api/datasets/Project-AgML/arabica_coffee_leaf_disease_classification | 2026-10-07T13:15:25.779315+00:00]`
- *repository_details*: `[hf_get_details | https://huggingface.co/api/datasets/Project-AgML/arabica_coffee_leaf_disease_classification | 2026-10-07T13:15:25.779315+00:00]`
- *reproducibility*: `[hf_get_details | https://huggingface.co/api/datasets/Project-AgML/arabica_coffee_leaf_disease_classification | 2026-10-07T13:15:25.779315+00:00]`
