# Existing Project Research Findings

- **Session ID:** `72356611-f0ef-4258-9ed1-17feb57880c3`
- **Total Findings:** 6
- **Search Queries Run:** `coffee leaf disease dataset`, `coffee leaf disease model`, `coffee leaf disease tflite`, `RoCoLe coffee leaf`, `coffee leaf disease`, `coffee leaf tensorflow lite`, `coffee leaf tflite`

## Notes
Ran four search queries across GitHub and Hugging Face: 'coffee leaf disease dataset', 'coffee leaf disease model', 'coffee leaf disease tflite', and 'RoCoLe coffee leaf'. Most fields missing were evaluation results and detailed limitations. All findings sourced from tool outputs. No budget limit reached.

## Findings

### 1. Project-AgML/arabica_coffee_leaf_disease_classification (Huggingface Dataset)
- **URL:** [https://huggingface.co/datasets/Project-AgML/arabica_coffee_leaf_disease_classification](https://huggingface.co/datasets/Project-AgML/arabica_coffee_leaf_disease_classification)
- **Problem Solved:** Coffee leaf disease classification
- **Input / Output:** Input: image of Arabica coffee leaf; Output: disease label (Cerscospora, Healthy, Leaf_rust, Miner, Phoma)
- **Dataset:** 58,549 images across 5 classes of Arabica coffee leaf diseases.
- **Model & Architecture:** not found
- **Method:** image classification (supervised learning)
- **Evaluation & Results:** not found
- **Repository Details:** Stars: not found | License: cc-by-4.0 | Language: not found | Last Update: 2026-07-07T19:51:34.000Z | Archived: False
- **Reproducibility:** Dataset provided via Hugging Face Datasets library; splits described in card.
- **Known Limitations:** not found

**Field Sources:**
- *archived*: `not found`
- *dataset*: `[hf_get_details | https://huggingface.co/api/datasets/Project-AgML/arabica_coffee_leaf_disease_classification | 2026-10-02T14:43:56.480383+00:00]`
- *evaluation_and_results*: `not found`
- *input_output*: `[hf_get_details | https://huggingface.co/api/datasets/Project-AgML/arabica_coffee_leaf_disease_classification | 2026-10-02T14:43:56.480383+00:00]`
- *known_limitations*: `not found`
- *language*: `not found`
- *last_update*: `[hf_get_details | https://huggingface.co/api/datasets/Project-AgML/arabica_coffee_leaf_disease_classification | 2026-10-02T14:43:56.480383+00:00]`
- *license*: `[hf_get_details | https://huggingface.co/api/datasets/Project-AgML/arabica_coffee_leaf_disease_classification | 2026-10-02T14:43:56.480383+00:00]`
- *method*: `not found`
- *model_and_architecture*: `not found`
- *problem_solved*: `[hf_get_details | https://huggingface.co/api/datasets/Project-AgML/arabica_coffee_leaf_disease_classification | 2026-10-02T14:43:56.480383+00:00]`
- *reproducibility*: `[hf_get_details | https://huggingface.co/api/datasets/Project-AgML/arabica_coffee_leaf_disease_classification | 2026-10-02T14:43:56.480383+00:00]`
- *stars*: `not found`

### 2. brainer-fp66/coffee-leaf-diseases (Huggingface Dataset)
- **URL:** [https://huggingface.co/datasets/brainer-fp66/coffee-leaf-diseases](https://huggingface.co/datasets/brainer-fp66/coffee-leaf-diseases)
- **Problem Solved:** Coffee leaf disease classification
- **Input / Output:** Input: image of coffee leaf; Output: disease label (Healthy, Miner, Phoma, Red Spider Mite, Rust)
- **Dataset:** Images of coffee leaves in five classes with train/validation/test splits (70/15/15).
- **Model & Architecture:** not found
- **Method:** image classification
- **Evaluation & Results:** not found
- **Repository Details:** Stars: not found | License: not found | Language: not found | Last Update: 2025-08-16T22:32:26.000Z | Archived: False
- **Reproducibility:** Provided as Hugging Face dataset in parquet format; intended for Vision Transformer experiments.
- **Known Limitations:** not found

**Field Sources:**
- *archived*: `not found`
- *dataset*: `[hf_get_details | https://huggingface.co/api/datasets/brainer-fp66/coffee-leaf-diseases | 2026-10-02T14:43:58.682534+00:00]`
- *evaluation_and_results*: `not found`
- *input_output*: `[hf_get_details | https://huggingface.co/api/datasets/brainer-fp66/coffee-leaf-diseases | 2026-10-02T14:43:58.682534+00:00]`
- *known_limitations*: `not found`
- *language*: `not found`
- *last_update*: `[hf_get_details | https://huggingface.co/api/datasets/brainer-fp66/coffee-leaf-diseases | 2026-10-02T14:43:58.682534+00:00]`
- *license*: `[hf_get_details | https://huggingface.co/api/datasets/brainer-fp66/coffee-leaf-diseases | 2026-10-02T14:43:58.682534+00:00]`
- *method*: `not found`
- *model_and_architecture*: `not found`
- *problem_solved*: `[hf_get_details | https://huggingface.co/api/datasets/brainer-fp66/coffee-leaf-diseases | 2026-10-02T14:43:58.682534+00:00]`
- *reproducibility*: `[hf_get_details | https://huggingface.co/api/datasets/brainer-fp66/coffee-leaf-diseases | 2026-10-02T14:43:58.682534+00:00]`
- *stars*: `not found`

### 3. Huyt/arabica-coffee-leaf-disease-efficientnet-b0 (Huggingface Model)
- **URL:** [https://huggingface.co/Huyt/arabica-coffee-leaf-disease-efficientnet-b0](https://huggingface.co/Huyt/arabica-coffee-leaf-disease-efficientnet-b0)
- **Problem Solved:** Classification of Arabica coffee leaf disease
- **Input / Output:** Input: image of coffee leaf; Output: disease class label
- **Dataset:** Trained on Project-AgML/arabica_coffee_leaf_disease_classification
- **Model & Architecture:** efficientnet_b0 (4.0M parameters) fine-tuned with timm library
- **Method:** Supervised fine-tuning of EfficientNetB0 on image classification task
- **Evaluation & Results:** Honest split accuracy 0.9911, macro-F1 0.9941 (reported in card).
- **Repository Details:** Stars: not found | License: cc-by-4.0 | Language: not found | Last Update: 2026-07-17T09:22:07.000Z | Archived: False
- **Reproducibility:** Model card lists dataset, hyperparameters, and training framework versions.
- **Known Limitations:** Dataset contains many duplicate images; reported accuracy may be inflated on naive splits.

**Field Sources:**
- *archived*: `not found`
- *dataset*: `[hf_get_details | https://huggingface.co/api/models/Huyt/arabica-coffee-leaf-disease-efficientnet-b0 | 2026-10-02T14:44:00.983802+00:00]`
- *evaluation_and_results*: `[hf_get_details | https://huggingface.co/api/models/Huyt/arabica-coffee-leaf-disease-efficientnet-b0 | 2026-10-02T14:44:00.983802+00:00]`
- *input_output*: `[hf_get_details | https://huggingface.co/api/models/Huyt/arabica-coffee-leaf-disease-efficientnet-b0 | 2026-10-02T14:44:00.983802+00:00]`
- *known_limitations*: `[hf_get_details | https://huggingface.co/api/models/Huyt/arabica-coffee-leaf-disease-efficientnet-b0 | 2026-10-02T14:44:00.983802+00:00]`
- *language*: `not found`
- *last_update*: `[hf_get_details | https://huggingface.co/api/models/Huyt/arabica-coffee-leaf-disease-efficientnet-b0 | 2026-10-02T14:44:00.983802+00:00]`
- *license*: `[hf_get_details | https://huggingface.co/api/models/Huyt/arabica-coffee-leaf-disease-efficientnet-b0 | 2026-10-02T14:44:00.983802+00:00]`
- *method*: `[hf_get_details | https://huggingface.co/api/models/Huyt/arabica-coffee-leaf-disease-efficientnet-b0 | 2026-10-02T14:44:00.983802+00:00]`
- *model_and_architecture*: `[hf_get_details | https://huggingface.co/api/models/Huyt/arabica-coffee-leaf-disease-efficientnet-b0 | 2026-10-02T14:44:00.983802+00:00]`
- *problem_solved*: `[hf_get_details | https://huggingface.co/api/models/Huyt/arabica-coffee-leaf-disease-efficientnet-b0 | 2026-10-02T14:44:00.983802+00:00]`
- *reproducibility*: `[hf_get_details | https://huggingface.co/api/models/Huyt/arabica-coffee-leaf-disease-efficientnet-b0 | 2026-10-02T14:44:00.983802+00:00]`
- *stars*: `not found`

### 4. brainer-fp66/vit-coffee-leaf-diseases (Huggingface Model)
- **URL:** [https://huggingface.co/brainer-fp66/vit-coffee-leaf-diseases](https://huggingface.co/brainer-fp66/vit-coffee-leaf-diseases)
- **Problem Solved:** Coffee leaf disease classification
- **Input / Output:** Input: image of coffee leaf; Output: disease class label
- **Dataset:** Trained on brainer-fp66/coffee-leaf-diseases
- **Model & Architecture:** Vision Transformer (ViT) fine-tuned from google/vit-base-patch16-224-in21k
- **Method:** Supervised fine-tuning of ViT on image classification
- **Evaluation & Results:** not found
- **Repository Details:** Stars: not found | License: apache-2.0 | Language: not found | Last Update: 2025-08-17T16:42:05.000Z | Archived: False
- **Reproducibility:** Model card includes training hyperparameters and framework versions.
- **Known Limitations:** not found

**Field Sources:**
- *archived*: `not found`
- *dataset*: `[hf_get_details | https://huggingface.co/api/models/brainer-fp66/vit-coffee-leaf-diseases | 2026-10-02T14:44:04.492947+00:00]`
- *evaluation_and_results*: `not found`
- *input_output*: `[hf_get_details | https://huggingface.co/api/models/brainer-fp66/vit-coffee-leaf-diseases | 2026-10-02T14:44:04.492947+00:00]`
- *known_limitations*: `not found`
- *language*: `not found`
- *last_update*: `[hf_get_details | https://huggingface.co/api/models/brainer-fp66/vit-coffee-leaf-diseases | 2026-10-02T14:44:04.492947+00:00]`
- *license*: `[hf_get_details | https://huggingface.co/api/models/brainer-fp66/vit-coffee-leaf-diseases | 2026-10-02T14:44:04.492947+00:00]`
- *method*: `[hf_get_details | https://huggingface.co/api/models/brainer-fp66/vit-coffee-leaf-diseases | 2026-10-02T14:44:04.492947+00:00]`
- *model_and_architecture*: `[hf_get_details | https://huggingface.co/api/models/brainer-fp66/vit-coffee-leaf-diseases | 2026-10-02T14:44:04.492947+00:00]`
- *problem_solved*: `[hf_get_details | https://huggingface.co/api/models/brainer-fp66/vit-coffee-leaf-diseases | 2026-10-02T14:44:04.492947+00:00]`
- *reproducibility*: `[hf_get_details | https://huggingface.co/api/models/brainer-fp66/vit-coffee-leaf-diseases | 2026-10-02T14:44:04.492947+00:00]`
- *stars*: `not found`

### 5. guifnpaiva/coffee-leaf-disease-classification-case-study (Github Repository)
- **URL:** [https://github.com/guifnpaiva/coffee-leaf-disease-classification-case-study](https://github.com/guifnpaiva/coffee-leaf-disease-classification-case-study)
- **Problem Solved:** Coffee leaf disease classification on-device using TensorFlow Lite
- **Input / Output:** Input: photo of coffee leaf; Output: disease label (healthy/unhealthy classes)
- **Dataset:** Uses RoCoLe robust coffee leaf image dataset
- **Model & Architecture:** CNN (MobileNetV2) converted to TensorFlow Lite
- **Method:** Supervised CNN training, quantization, on-device inference with Flutter UI
- **Evaluation & Results:** not found
- **Repository Details:** Stars: 0 | License: not found | Language: not found | Last Update: 2026-05-12T03:14:51Z | Archived: False
- **Reproducibility:** README describes dataset, preprocessing, model selection, TFLite conversion steps.
- **Known Limitations:** Source code not available; only case study description.

**Field Sources:**
- *archived*: `[github_get_repository | https://api.github.com/repos/guifnpaiva/coffee-leaf-disease-classification-case-study | 2026-10-02T14:44:07.042610+00:00]`
- *dataset*: `[github_get_readme | https://api.github.com/repos/guifnpaiva/coffee-leaf-disease-classification-case-study/readme | 2026-10-02T14:44:09.898744+00:00]`
- *evaluation_and_results*: `not found`
- *input_output*: `[github_get_readme | https://api.github.com/repos/guifnpaiva/coffee-leaf-disease-classification-case-study/readme | 2026-10-02T14:44:09.898744+00:00]`
- *known_limitations*: `[github_get_readme | https://api.github.com/repos/guifnpaiva/coffee-leaf-disease-classification-case-study/readme | 2026-10-02T14:44:09.898744+00:00]`
- *language*: `[github_get_repository | https://api.github.com/repos/guifnpaiva/coffee-leaf-disease-classification-case-study | 2026-10-02T14:44:07.042610+00:00]`
- *last_update*: `[github_get_repository | https://api.github.com/repos/guifnpaiva/coffee-leaf-disease-classification-case-study | 2026-10-02T14:44:07.042610+00:00]`
- *license*: `[github_get_repository | https://api.github.com/repos/guifnpaiva/coffee-leaf-disease-classification-case-study | 2026-10-02T14:44:07.042610+00:00]`
- *method*: `[github_get_readme | https://api.github.com/repos/guifnpaiva/coffee-leaf-disease-classification-case-study/readme | 2026-10-02T14:44:09.898744+00:00]`
- *model_and_architecture*: `[github_get_readme | https://api.github.com/repos/guifnpaiva/coffee-leaf-disease-classification-case-study/readme | 2026-10-02T14:44:09.898744+00:00]`
- *problem_solved*: `[github_get_repository | https://api.github.com/repos/guifnpaiva/coffee-leaf-disease-classification-case-study | 2026-10-02T14:44:07.042610+00:00]`
- *reproducibility*: `[github_get_readme | https://api.github.com/repos/guifnpaiva/coffee-leaf-disease-classification-case-study/readme | 2026-10-02T14:44:09.898744+00:00]`
- *stars*: `[github_get_repository | https://api.github.com/repos/guifnpaiva/coffee-leaf-disease-classification-case-study | 2026-10-02T14:44:07.042610+00:00]`

### 6. iam-stanis/coffee-leaf-diseases (Github Repository)
- **URL:** [https://github.com/iam-stanis/coffee-leaf-diseases](https://github.com/iam-stanis/coffee-leaf-diseases)
- **Problem Solved:** Classification of coffee leaf diseases using ResNet models
- **Input / Output:** Input: coffee leaf photos; Output: disease label
- **Dataset:** Combines Kaggle coffee leaf disease dataset, RoCoLe robust coffee leaf dataset, and Ugandan coffee dataset.
- **Model & Architecture:** ResNet50 and ResNet101 (trained via Jupyter notebooks)
- **Method:** Supervised training of ResNet CNNs; notebooks for reproducibility.
- **Evaluation & Results:** not found
- **Repository Details:** Stars: 0 | License: CC0-1.0 | Language: Jupyter Notebook | Last Update: 2025-10-10T09:28:37Z | Archived: False
- **Reproducibility:** README lists dataset sources; notebooks provide training code.
- **Known Limitations:** not found

**Field Sources:**
- *archived*: `[github_get_repository | https://api.github.com/repos/iam-stanis/coffee-leaf-diseases | 2026-10-02T14:44:14.312830+00:00]`
- *dataset*: `[github_get_readme | https://api.github.com/repos/iam-stanis/coffee-leaf-diseases/readme | 2026-10-02T14:44:16.391105+00:00]`
- *evaluation_and_results*: `not found`
- *input_output*: `[github_get_repository | https://api.github.com/repos/iam-stanis/coffee-leaf-diseases | 2026-10-02T14:44:14.312830+00:00]`
- *known_limitations*: `not found`
- *language*: `[github_get_repository | https://api.github.com/repos/iam-stanis/coffee-leaf-diseases | 2026-10-02T14:44:14.312830+00:00]`
- *last_update*: `[github_get_repository | https://api.github.com/repos/iam-stanis/coffee-leaf-diseases | 2026-10-02T14:44:14.312830+00:00]`
- *license*: `[github_get_repository | https://api.github.com/repos/iam-stanis/coffee-leaf-diseases | 2026-10-02T14:44:14.312830+00:00]`
- *method*: `[github_get_repository | https://api.github.com/repos/iam-stanis/coffee-leaf-diseases | 2026-10:14.312830+00:00]`
- *model_and_architecture*: `[github_get_repository | https://api.github.com/repos/iam-stanis/coffee-leaf-diseases | 2026-10:14.312830+00:00]`
- *problem_solved*: `[github_get_repository | https://api.github.com/repos/iam-stanis/coffee-leaf-diseases | 2026-10-02T14:44:14.312830+00:00]`
- *reproducibility*: `[github_get_readme | https://api.github.com/repos/iam-stanis/coffee-leaf-diseases/readme | 2026-10-02T14:44:16.391105+00:00]`
- *stars*: `[github_get_repository | https://api.github.com/repos/iam-stanis/coffee-leaf-diseases | 2026-10-02T14:44:14.312830+00:00]`
