# Existing Project Research Findings

- **Session ID:** `28a8c6cf-20c9-45e8-8707-0d4162a66742`
- **Total Findings:** 8
- **Search Queries Run:** `real-time hate speech detection transformer`, `streaming toxic comment classification BERT`, `high throughput toxicity detection twitter`, `explainable hate speech detection transformer`, `hate speech detection`, `hate speech detection explainable`, `jigsaw toxic comment`

## Notes
Executed 7 search queries (4 on GitHub, 3 on Hugging Face). One GitHub query ('high throughput toxicity detection twitter') returned zero results. All other queries yielded candidate repositories, models, or dataset. Fields not explicitly described in source material are marked as 'not found'.

## Findings

### 1. ali-saied/hate-speech-detection-xai (Github Repository)
- **URL:** [https://github.com/ali-saied/hate-speech-detection-xai](https://github.com/ali-saied/hate-speech-detection-xai)
- **Problem Solved:** Explainable Hate Speech Detection using Transformer Models
- **Input / Output:** Text comment input; model returns classification with explainability output (details not specified)
- **Dataset:** not found
- **Model & Architecture:** Transformer model (unspecified) with explainable AI
- **Method:** Explainable AI techniques applied to transformer-based classifier (model architecture unspecified)
- **Evaluation & Results:** not found
- **Repository Details:** Stars: 0 | License: not found | Language: Jupyter Notebook | Last Update: 2026-04-21T18:24:01Z | Archived: not found
- **Reproducibility:** not found
- **Known Limitations:** not found

**Field Sources:**

### 2. lotachipro-prog/hate-speech-detection-nlp (Github Repository)
- **URL:** [https://github.com/lotachipro-prog/hate-speech-detection-nlp](https://github.com/lotachipro-prog/hate-speech-detection-nlp)
- **Problem Solved:** Automated hate speech detection with SHAP token-level explanations
- **Input / Output:** Text comment input; classification output with SHAP token explanations and confidence scores
- **Dataset:** Jigsaw Toxic Comment Classification Challenge (Kaggle)
- **Model & Architecture:** BERT (bert-base-uncased), RoBERTa (roberta-base), HateBERT fine-tuned
- **Method:** Fine-tuning BERT, RoBERTa, HateBERT; SHAP for explainability; Gradio demo deployment
- **Evaluation & Results:** Macro F1 0.9134, AUC-ROC 0.9767 (BERT); HateBERT F1 0.9125; Test set Macro F1 0.8005, AUC-ROC 0.9638, Recall 0.9041
- **Repository Details:** Stars: 0 | License: not found | Language: Jupyter Notebook | Last Update: 2026-04-20T00:26:34Z | Archived: not found
- **Reproducibility:** Full notebook pipeline (EDA, baseline, transformer training, SHAP explainability, Gradio demo, test evaluation) with Google Colab instructions
- **Known Limitations:** Focus on binary toxic vs non‑toxic; may not handle multilingual or sarcasm; no streaming architecture

**Field Sources:**

### 3. Karangarg01/peft-hate-speech-detection (Github Repository)
- **URL:** [https://github.com/Karangarg01/peft-hate-speech-detection](https://github.com/Karangarg01/peft-hate-speech-detection)
- **Problem Solved:** Hate speech detection using DistilBERT fine-tuned with Parameter‑Efficient Fine‑Tuning (LoRA) for reduced computation
- **Input / Output:** Text comment input; binary classification output (toxic vs non‑toxic) with confidence scores
- **Dataset:** Civil Comments dataset (binary toxicity scores converted to labels)
- **Model & Architecture:** DistilBERT with LoRA fine‑tuning
- **Method:** PEFT (LoRA) applied to DistilBERT; weighted loss for class imbalance; Streamlit UI for real‑time inference
- **Evaluation & Results:** not found
- **Repository Details:** Stars: 0 | License: not found | Language: Python | Last Update: 2026-04-14T21:14:04Z | Archived: not found
- **Reproducibility:** Training script (train.py), Streamlit app (app.py), requirements.txt, step‑by‑step usage instructions provided
- **Known Limitations:** Difficulty detecting sarcasm and implicit hate speech; limited multilingual support; performance depends on dataset quality

**Field Sources:**

### 4. sntsemilio/Hate-Speech-Detection-System (Github Repository)
- **URL:** [https://github.com/sntsemilio/Hate-Speech-Detection-System](https://github.com/sntsemilio/Hate-Speech-Detection-System)
- **Problem Solved:** Advanced hate speech detection with custom lightweight transformer for real‑time inference
- **Input / Output:** Text comment input; classification label (hate speech vs normal) with confidence and ~45 ms latency
- **Dataset:** not explicitly stated (project mentions a dataset used for a course project)
- **Model & Architecture:** Custom transformer (847K parameters); also BERT and RoBERTa benchmarks
- **Method:** Custom transformer architecture (16 heads, d_model=64); Keras Tuner hyperparameter optimization; Streamlit interactive demo; benchmark against BERT and RoBERTa
- **Evaluation & Results:** Accuracy 93%, Macro F1 0.74, Inference time 45 ms, 847K parameters
- **Repository Details:** Stars: 0 | License: MIT | Language: Jupyter Notebook | Last Update: 2025-07-03T19:54:05Z | Archived: not found
- **Reproducibility:** Notebook pipeline (EDA, baseline, transformer training, SHAP explainability, Gradio demo, test evaluation), requirements.txt, Streamlit app, model files with clear installation instructions
- **Known Limitations:** Difficulty with sarcasm and implicit hate speech; English‑only; not tested on streaming pipelines

**Field Sources:**

### 5. 0xSatish/multilingual-hate-speech-detector (Github Repository)
- **URL:** [https://github.com/0xSatish/multilingual-hate-speech-detector](https://github.com/0xSatish/multilingual-hate-speech-detector)
- **Problem Solved:** Real‑time multilingual hate speech and abusive language detection via Chrome extension and FastAPI backend
- **Input / Output:** Extracted text from web pages; classification into Hate, Offensive, Neutral with confidence; optional content blurring
- **Dataset:** not found
- **Model & Architecture:** Hugging Face transformer model (unspecified) with rule‑based multilingual enhancements
- **Method:** Chrome extension captures DOM text; FastAPI backend tokenizes and runs transformer model; rule‑based multilingual checks; badges injected into page
- **Evaluation & Results:** not found
- **Repository Details:** Stars: 0 | License: not found | Language: Python | Last Update: 2026-07-03T20:47:48Z | Archived: not found
- **Reproducibility:** Source code for extension and backend provided; architecture diagrams included; training scripts and model files not included
- **Known Limitations:** Multilingual focus; lacks explicit latency/throughput metrics; model details unspecified

**Field Sources:**

### 6. Gladiaio/hate-speech-detection_bert-base-uncased-hatexplain_base_traced (Huggingface Model)
- **URL:** [https://huggingface.co/Gladiaio/hate-speech-detection_bert-base-uncased-hatexplain_base_traced](https://huggingface.co/Gladiaio/hate-speech-detection_bert-base-uncased-hatexplain_base_traced)
- **Problem Solved:** Hate speech detection using BERT‑base‑uncased fine‑tuned on the HateXplain dataset and exported as a traced model for fast inference
- **Input / Output:** Text input; classification output (toxicity label) (specific output format not detailed)
- **Dataset:** not found
- **Model & Architecture:** BERT‑base‑uncased fine‑tuned on HateXplain, exported as traced model
- **Method:** Fine‑tuning on HateXplain; model tracing (TorchScript) for accelerated inference
- **Evaluation & Results:** not found
- **Repository Details:** Stars: 0 | License: not found | Language: not found | Last Update: not found | Archived: not found
- **Reproducibility:** not found
- **Known Limitations:** not found

**Field Sources:**

### 7. eclat12450/fine-tuned-KcELECTRA-base-hatespeechdetection (Huggingface Model)
- **URL:** [https://huggingface.co/eclat12450/fine-tuned-KcELECTRA-base-hatespeechdetection](https://huggingface.co/eclat12450/fine-tuned-KcELECTRA-base-hatespeechdetection)
- **Problem Solved:** Hate speech detection using KcELECTRA‑base fine‑tuned for text classification
- **Input / Output:** Text input; classification output (toxicity label) (details not provided)
- **Dataset:** not found
- **Model & Architecture:** KcELECTRA‑base fine‑tuned for hate speech detection
- **Method:** Fine‑tuning KcELECTRA‑base on a hate speech dataset (unspecified) using PyTorch Transformers
- **Evaluation & Results:** not found
- **Repository Details:** Stars: 0 | License: not found | Language: not found | Last Update: not found | Archived: not found
- **Reproducibility:** not found
- **Known Limitations:** not found

**Field Sources:**

### 8. affahrizain/jigsaw-toxic-comment (Huggingface Dataset)
- **URL:** [https://huggingface.co/datasets/affahrizain/jigsaw-toxic-comment](https://huggingface.co/datasets/affahrizain/jigsaw-toxic-comment)
- **Problem Solved:** Provides annotated toxic comment data for training and evaluating hate speech detection models
- **Input / Output:** Each record contains 'comment_clean' (text) and 'labels' (binary toxicity label)
- **Dataset:** Jigsaw Toxic Comment dataset (train 159,100 examples; dev 22,393; test 63,978)
- **Model & Architecture:** not applicable
- **Method:** Dataset hosted on Hugging Face Datasets library; available in parquet format; can be loaded via datasets.load_dataset
- **Evaluation & Results:** not applicable
- **Repository Details:** Stars: not applicable | License: not found | Language: not applicable | Last Update: not found | Archived: not found
- **Reproducibility:** Dataset card provides details and loading instructions
- **Known Limitations:** Binary label only; annotator bias may affect fairness

**Field Sources:**
