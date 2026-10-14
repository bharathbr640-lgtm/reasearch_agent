# Paper Research Findings: Closely Related Work (No Exact Match)

No research paper addressed the exact research problem (e.g. offline mobile edge deployment without cloud connectivity). The following closely related papers provide empirical evidence on models, datasets, and architectures.

- **Session ID:** `72356611-f0ef-4258-9ed1-17feb57880c3`
- **Match Status:** **No exact research paper was found in the searched sources (Closely Related Research Presented)**
- **Total Candidates Discovered & Documented:** 10
- **Search Queries Run:** `mobile offline coffee leaf disease detection deep learning Android TensorFlow Lite`, `coffee leaf disease classification deep learning`, `offline mobile app plant disease detection Android TensorFlow Lite tomato`, `smartphone coffee leaf disease detection app`

## Research Notes & Methodology
Search queries executed (4): "mobile offline coffee leaf disease detection deep learning Android TensorFlow Lite", "coffee leaf disease classification deep learning", "offline mobile app plant disease detection Android TensorFlow Lite tomato", "smartphone coffee leaf disease detection app". Candidate papers verified with full-text reading (5): A smartphone application to detection and classification of coffee leaf miner and coffee leaf rust, EffResViT-SE FusionNet: A Hybrid Deep Learning Framework for Accurate Classification of Coffee Leaf Diseases., DeepEMPR: coffee leaf disease detection with deep learning and enhanced multivariance product representation., Arabica coffee leaf images dataset for coffee leaf disease detection and classification., GreenAid: a confidence-weighted ensemble deep learning system for real-time plant disease detection and management.. Candidate papers with search snippet only (5): LeafLiteX mobile application for leaf disease detection using U-Net segmentation and lightweight deep learning., Multi-Class Plant Leaf Disease Detection: A CNN-based Approach with Mobile App Integration, PMVT: a lightweight vision transformer for plant disease identification on mobile devices., Plant disease detection model for edge computing devices., Mobile-Friendly Deep Learning for Plant Disease Detection: A Lightweight CNN Benchmark Across 101 Classes of 33 Crops. Validator rejected fields (22): problem_addressed (quote not found in paper text), research_objective (quote not found in paper text), domain (quote not found in paper text), dataset_name (quote not found in paper text).

## Top Research Paper Findings

### 1. A smartphone application to detection and classification of coffee leaf miner and coffee leaf rust [CLOSELY RELATED]
- **Authors:** not found
- **Year:** not found | **DOI:** not found
- **Paper URL:** [https://arxiv.org/abs/1904.00742](https://arxiv.org/abs/1904.00742)
- **Citation:** not found
- **Match Classification:** `closely_related` (Reason: offline operation not stated in the text (found: "implementation as an App that allow the detection of the foliar damages"))
- **Problem Addressed:** not found
- **Research Objective:** not found
- **Input / Output:** Input: Smartphone‑captured coffee leaf image | Output: Disease class (rust or leaf miner) and severity percentage
- **Dataset:** Name: not found | Description: not found | Size: not found | Source: not found
- **Model & Architecture:** Model: Artificial Neural Network (Backpropagation) and Extreme Learning Machine | Architecture: Hidden layer with 10 neurons, ReLu activation | Backbone: not found | Components: not found
- **Methodology:** not found
- **Experiments & Results:**
  - Setup: not found
  - Metrics: sensitivity and precision (also accuracy, precision, recall)
  - Results: 96.013% accuracy
  - Baselines: Artificial Neural Network trained with Backpropagation
  - Evidence Location: `a smartphone application to detection and classification of coffee leaf miner and coffee leaf rust, abstract, 1\. introduction, 2\. algorithms for digital image processing of coffee leaves, 2.1.1. the color space ycbcr`
- **Limitations (Author-Stated):** Camera automatic adjustment causes color variations that hurt segmentation, especially with non‑white backgrounds
- **Research Gap (Evidenced):** Need more robust segmentation methods that work across varied backgrounds
- **Code Repository:** [not found](not found) (Official: not found, Framework: not found)
- **Key Verified Evidence:**
  > [results] "In this work, artificial neural network trained with Backpropagation algorithms and extreme learning machine was used."
  > [results] "96.013 ± 0.950"
  > [conclusion] "The camera’s automatic adjustment, which depends on the ambient colors, generated images with different shades of green."
  > [conclusion] "The next steps for future work is to investigate segmentation methods that are more robust, i.e., that present good results for various types of backgrounds."
  > [abstract] "implementation as an App that allow the detection of the foliar damages"
- **Traceable Source URLs:** [https://arxiv.org/abs/1904.00742](https://arxiv.org/abs/1904.00742)

### 2. EffResViT-SE FusionNet: A Hybrid Deep Learning Framework for Accurate Classification of Coffee Leaf Diseases. [CLOSELY RELATED]
- **Authors:** not found
- **Year:** not found | **DOI:** not found
- **Paper URL:** [https://pmc.ncbi.nlm.nih.gov/articles/PMC12689465/](https://pmc.ncbi.nlm.nih.gov/articles/PMC12689465/)
- **Citation:** not found
- **Match Classification:** `closely_related` (Reason: offline operation not stated in the text)
- **Problem Addressed:** Detection and classification of coffee leaf diseases
- **Research Objective:** Develop a hybrid deep learning framework for accurate coffee leaf disease classification
- **Input / Output:** Input: RGB leaf image (224 × 224 × 3) | Output: not found
- **Dataset:** Name: Kaggle coffee leaf disease dataset | Description: Kaggle coffee leaf disease dataset | Size: 58,555 images | Source: not found
- **Model & Architecture:** Model: EffResViT‑SE FusionNet | Architecture: not found | Backbone: not found | Components: not found
- **Methodology:** not found
- **Experiments & Results:**
  - Setup: not found
  - Metrics: accuracy, precision, recall, F1‑score
  - Results: validation accuracy ≈ 99%
  - Baselines: not found
  - Evidence Location: `effresvit-se fusionnet: a hybrid deep learning framework for accurate classification of coffee leaf diseases, bhoomika mehta, salil bharany, dalia h elkamchouchi, ateeq ur rehman`
- **Limitations (Author-Stated):** High parameter count prevents real‑time edge/mobile use
- **Research Gap (Evidenced):** not found
- **Code Repository:** [not found](not found) (Official: not found, Framework: not found)
- **Key Verified Evidence:**
  > [abstract] "Coffee is a vital agricultural commodity that sustains millions of farmers worldwide, yet its cultivation is increasingly threatened by devastating leaf diseases such as Leaf Rust, Phoma, Cercospora, and Leaf Miner."
  > [abstract] "To address these challenges, we propose EffResViT‑SE FusionNet, a novel hybrid deep learning framework that integrates EfficientNetB3 and ResNet50 enhanced with Squeeze‑and‑Excitation (SE) blocks for adaptive local feature recalibration, along with a Vision Transformer (ViT) for modeling global contextual dependencies."
  > [3.1. input dataset] "This study utilized the publicly available dataset from the Kaggle repository."
  > [3.1. input dataset] "The dataset consists of 58,555 images across five categories"
  > [3.3. proposed effresvit-se fusionnet model] "The proposed EffResViT‑SE FusionNet model"
  > [4.5. results on proposed effresvit-se fusionnet model] "the validation accuracy maintains itself, increasing from approximately 0.6 to approximately 0.99."
  > [5. conclusion and future work] "The EfficientNetB3‑ResNet50‑ViT hybrid model complicates and raises the number of parameters, which prevents real‑time use in the edge and mobile environment."
- **Traceable Source URLs:** [https://pmc.ncbi.nlm.nih.gov/articles/PMC12689465/](https://pmc.ncbi.nlm.nih.gov/articles/PMC12689465/)

### 3. DeepEMPR: coffee leaf disease detection with deep learning and enhanced multivariance product representation. [CLOSELY RELATED]
- **Authors:** not found
- **Year:** not found | **DOI:** not found
- **Paper URL:** [https://pmc.ncbi.nlm.nih.gov/articles/PMC11623072/](https://pmc.ncbi.nlm.nih.gov/articles/PMC11623072/)
- **Citation:** not found
- **Match Classification:** `closely_related` (Reason: offline operation not stated in the text)
- **Problem Addressed:** Plant diseases threaten agricultural sustainability by reducing crop yields.
- **Research Objective:** enhancing the classification of diseases and estimating their severity in coffee leaf images
- **Input / Output:** Input: not found | Output: not found
- **Dataset:** Name: not found | Description: not found | Size: 1,685 images | Source: not found
- **Model & Architecture:** Model: not found | Architecture: not found | Backbone: not found | Components: not found
- **Methodology:** not found
- **Experiments & Results:**
  - Setup: not found
  - Metrics: not found
  - Results: not found
  - Baselines: not found
  - Evidence Location: `deepempr: coffee leaf disease detection with deep learning and enhanced multivariance product representation, ahmet topal, burcu tunga, erfan babaee tirkolaee, abstract`
- **Limitations (Author-Stated):** several areas remain unexplored, including background bias
- **Research Gap (Evidenced):** not found
- **Code Repository:** [not found](not found) (Official: not found, Framework: not found)
- **Key Verified Evidence:**
  > [abstract] "Plant diseases threaten agricultural sustainability by reducing crop yields."
  > [abstract] "This study focuses on enhancing the classification of diseases and estimating their severity in coffee leaf images."
  > [dataset description] "The dataset comprises a total of 1,685 images, categorized into two primary classes: one representing healthy images and the other representing diseased images."
  > [conclusion] "several areas remain unexplored. One of the primary factors influencing classification success is the bias introduced by the background, which should be addressed in future research."
- **Traceable Source URLs:** [https://pmc.ncbi.nlm.nih.gov/articles/PMC11623072/](https://pmc.ncbi.nlm.nih.gov/articles/PMC11623072/)

### 4. Arabica coffee leaf images dataset for coffee leaf disease detection and classification. [CLOSELY RELATED]
- **Authors:** not found
- **Year:** not found | **DOI:** not found
- **Paper URL:** [https://pmc.ncbi.nlm.nih.gov/articles/PMC8165403/](https://pmc.ncbi.nlm.nih.gov/articles/PMC8165403/)
- **Citation:** not found
- **Match Classification:** `closely_related` (Reason: offline operation not stated in the text)
- **Problem Addressed:** coffee plant leaf disease recognition and classification
- **Research Objective:** introduce Arabica coffee leaf datasets JMuBEN and JMuBEN2
- **Input / Output:** Input: leaf images | Output: disease class labels
- **Dataset:** Name: JMuBEN and JMuBEN2 | Description: JMuBEN and JMuBEN2 | Size: 58,555 | Source: not found
- **Model & Architecture:** Model: not applicable | Architecture: not applicable | Backbone: not found | Components: not found
- **Methodology:** not found
- **Experiments & Results:**
  - Setup: not applicable
  - Metrics: not applicable
  - Results: not applicable
  - Baselines: not applicable
  - Evidence Location: `arabica coffee leaf images dataset for coffee leaf disease detection and classification, jennifer jepkoech, david muchangi mugo, benson k kenduiywo, edna chebet too`
- **Limitations (Author-Stated):** not found
- **Research Gap (Evidenced):** not found
- **Code Repository:** [https://github.com/bonfaceonyango/coffee_leaf_disease_detection_CNN](https://github.com/bonfaceonyango/coffee_leaf_disease_detection_CNN) (Official: True, Framework: not found)
- **Key Verified Evidence:**
  > [abstract] "The Arabica datasets contain images that facilitates training and validation during the utilization of deep learning algorithms for coffee plant leaf disease recognition and classification."
  > [abstract] "This article introduces Arabica coffee leaf datasets known as JMuBEN and JMuBEN2."
  > [abstract] "JMuBEN and JMuBEN2"
  > [abstract] "In total, the dataset contains 58,555 leaf images"
- **Traceable Source URLs:** [https://pmc.ncbi.nlm.nih.gov/articles/PMC8165403/](https://pmc.ncbi.nlm.nih.gov/articles/PMC8165403/)

### 5. GreenAid: a confidence-weighted ensemble deep learning system for real-time plant disease detection and management. [CLOSELY RELATED]
- **Authors:** not found
- **Year:** not found | **DOI:** not found
- **Paper URL:** [https://pmc.ncbi.nlm.nih.gov/articles/PMC13284324/](https://pmc.ncbi.nlm.nih.gov/articles/PMC13284324/)
- **Citation:** not found
- **Match Classification:** `closely_related` (Reason: offline operation not stated in the text (found: "cross-platform mobile application supporting offline inference via TensorFlow Lite"))
- **Problem Addressed:** Plant diseases cause 20–40% annual crop losses worldwide, and detection methods are slow, subjective, and inaccessible to smallholder farmers.
- **Research Objective:** Present GreenAid, an end-to-end plant disease detection and management system integrating a confidence-weighted ensemble and offline mobile app.
- **Input / Output:** Input: High-resolution RGB images of crop leaves | Output: Disease class label (one of 38 categories)
- **Dataset:** Name: PlantVillage | Description: PlantVillage | Size: approximately 87,000 images | Source: not found
- **Model & Architecture:** Model: GreenAid confidence-weighted ensemble | Architecture: VGG16, ResNet50, InceptionV3 fused with per-class F1-score reliability weights | Backbone: not found | Components: not found
- **Methodology:** not found
- **Experiments & Results:**
  - Setup: not found
  - Metrics: not found
  - Results: not found
  - Baselines: not found
  - Evidence Location: `greenaid: a confidence-weighted ensemble deep learning system for real-time plant disease detection and management, fatma m talaat, mohammed tawfik, warda m shaban, abstract`
- **Limitations (Author-Stated):** No cross-dataset validation
- **Research Gap (Evidenced):** not found
- **Code Repository:** [not found](not found) (Official: not found, Framework: not found)
- **Key Verified Evidence:**
  > [abstract] "Plant diseases cause 20–40% annual crop losses worldwide, yet conventional detection methods remain slow, subjective, and inaccessible to smallholder farmers."
  > [abstract] "This work presents GreenAid, an end-to-end plant disease detection and management system that bridges the gap between laboratory-level deep learning performance and practical agricultural deployment."
  > [dataset description] "The dataset used for all experiments is the publicly available PlantVillage dataset"
  > [dataset description] "The dataset comprises approximately 87,000 RGB images of crop leaves"
  > [abstract] "confidence-weighted ensemble of three CNN architectures (VGG16, ResNet50, InceptionV3)"
  > [limitations] "The most significant limitation is the absence of cross-dataset validation."
  > [abstract] "cross-platform mobile application supporting offline inference via TensorFlow Lite"
- **Traceable Source URLs:** [https://pmc.ncbi.nlm.nih.gov/articles/PMC13284324/](https://pmc.ncbi.nlm.nih.gov/articles/PMC13284324/)

### 6. LeafLiteX mobile application for leaf disease detection using U-Net segmentation and lightweight deep learning. [CLOSELY RELATED]
- **Authors:** not found
- **Year:** not found | **DOI:** not found
- **Paper URL:** [https://pubmed.ncbi.nlm.nih.gov/42420345/](https://pubmed.ncbi.nlm.nih.gov/42420345/)
- **Citation:** not found
- **Match Classification:** `closely_related` (Reason: not found)
- **Problem Addressed:** not read - search snippet only
- **Research Objective:** not read - search snippet only
- **Input / Output:** Input: not read - search snippet only | Output: not read - search snippet only
- **Dataset:** Name: not read - search snippet only | Description: not read - search snippet only | Size: not read - search snippet only | Source: not read - search snippet only
- **Model & Architecture:** Model: not read - search snippet only | Architecture: not read - search snippet only | Backbone: not read - search snippet only | Components: not read - search snippet only
- **Methodology:** not read - search snippet only
- **Experiments & Results:**
  - Setup: not read - search snippet only
  - Metrics: not read - search snippet only
  - Results: not read - search snippet only
  - Baselines: not read - search snippet only
  - Evidence Location: `not read - search snippet only`
- **Limitations (Author-Stated):** not read - search snippet only
- **Research Gap (Evidenced):** not read - search snippet only
- **Code Repository:** [not found](not found) (Official: not found, Framework: not found)
- **Traceable Source URLs:** [https://pubmed.ncbi.nlm.nih.gov/42420345/](https://pubmed.ncbi.nlm.nih.gov/42420345/)

### 7. Multi-Class Plant Leaf Disease Detection: A CNN-based Approach with Mobile App Integration [CLOSELY RELATED]
- **Authors:** not found
- **Year:** not found | **DOI:** not found
- **Paper URL:** [https://arxiv.org/abs/2408.15289](https://arxiv.org/abs/2408.15289)
- **Citation:** not found
- **Match Classification:** `closely_related` (Reason: not found)
- **Problem Addressed:** not read - search snippet only
- **Research Objective:** not read - search snippet only
- **Input / Output:** Input: not read - search snippet only | Output: not read - search snippet only
- **Dataset:** Name: not read - search snippet only | Description: not read - search snippet only | Size: not read - search snippet only | Source: not read - search snippet only
- **Model & Architecture:** Model: not read - search snippet only | Architecture: not read - search snippet only | Backbone: not read - search snippet only | Components: not read - search snippet only
- **Methodology:** not read - search snippet only
- **Experiments & Results:**
  - Setup: not read - search snippet only
  - Metrics: not read - search snippet only
  - Results: not read - search snippet only
  - Baselines: not read - search snippet only
  - Evidence Location: `not read - search snippet only`
- **Limitations (Author-Stated):** not read - search snippet only
- **Research Gap (Evidenced):** not read - search snippet only
- **Code Repository:** [not found](not found) (Official: not found, Framework: not found)
- **Traceable Source URLs:** [https://arxiv.org/abs/2408.15289](https://arxiv.org/abs/2408.15289)

### 8. PMVT: a lightweight vision transformer for plant disease identification on mobile devices. [CLOSELY RELATED]
- **Authors:** not found
- **Year:** not found | **DOI:** not found
- **Paper URL:** [https://pmc.ncbi.nlm.nih.gov/articles/PMC10562605/](https://pmc.ncbi.nlm.nih.gov/articles/PMC10562605/)
- **Citation:** not found
- **Match Classification:** `closely_related` (Reason: not found)
- **Problem Addressed:** not read - search snippet only
- **Research Objective:** not read - search snippet only
- **Input / Output:** Input: not read - search snippet only | Output: not read - search snippet only
- **Dataset:** Name: not read - search snippet only | Description: not read - search snippet only | Size: not read - search snippet only | Source: not read - search snippet only
- **Model & Architecture:** Model: not read - search snippet only | Architecture: not read - search snippet only | Backbone: not read - search snippet only | Components: not read - search snippet only
- **Methodology:** not read - search snippet only
- **Experiments & Results:**
  - Setup: not read - search snippet only
  - Metrics: not read - search snippet only
  - Results: not read - search snippet only
  - Baselines: not read - search snippet only
  - Evidence Location: `not read - search snippet only`
- **Limitations (Author-Stated):** not read - search snippet only
- **Research Gap (Evidenced):** not read - search snippet only
- **Code Repository:** [not found](not found) (Official: not found, Framework: not found)
- **Traceable Source URLs:** [https://pmc.ncbi.nlm.nih.gov/articles/PMC10562605/](https://pmc.ncbi.nlm.nih.gov/articles/PMC10562605/)

### 9. Plant disease detection model for edge computing devices. [CLOSELY RELATED]
- **Authors:** not found
- **Year:** not found | **DOI:** not found
- **Paper URL:** [https://pmc.ncbi.nlm.nih.gov/articles/PMC10748432/](https://pmc.ncbi.nlm.nih.gov/articles/PMC10748432/)
- **Citation:** not found
- **Match Classification:** `closely_related` (Reason: not found)
- **Problem Addressed:** not read - search snippet only
- **Research Objective:** not read - search snippet only
- **Input / Output:** Input: not read - search snippet only | Output: not read - search snippet only
- **Dataset:** Name: not read - search snippet only | Description: not read - search snippet only | Size: not read - search snippet only | Source: not read - search snippet only
- **Model & Architecture:** Model: not read - search snippet only | Architecture: not read - search snippet only | Backbone: not read - search snippet only | Components: not read - search snippet only
- **Methodology:** not read - search snippet only
- **Experiments & Results:**
  - Setup: not read - search snippet only
  - Metrics: not read - search snippet only
  - Results: not read - search snippet only
  - Baselines: not read - search snippet only
  - Evidence Location: `not read - search snippet only`
- **Limitations (Author-Stated):** not read - search snippet only
- **Research Gap (Evidenced):** not read - search snippet only
- **Code Repository:** [not found](not found) (Official: not found, Framework: not found)
- **Traceable Source URLs:** [https://pmc.ncbi.nlm.nih.gov/articles/PMC10748432/](https://pmc.ncbi.nlm.nih.gov/articles/PMC10748432/)

### 10. Mobile-Friendly Deep Learning for Plant Disease Detection: A Lightweight CNN Benchmark Across 101 Classes of 33 Crops [CLOSELY RELATED]
- **Authors:** not found
- **Year:** not found | **DOI:** not found
- **Paper URL:** [https://arxiv.org/abs/2508.10817](https://arxiv.org/abs/2508.10817)
- **Citation:** not found
- **Match Classification:** `closely_related` (Reason: not found)
- **Problem Addressed:** not read - search snippet only
- **Research Objective:** not read - search snippet only
- **Input / Output:** Input: not read - search snippet only | Output: not read - search snippet only
- **Dataset:** Name: not read - search snippet only | Description: not read - search snippet only | Size: not read - search snippet only | Source: not read - search snippet only
- **Model & Architecture:** Model: not read - search snippet only | Architecture: not read - search snippet only | Backbone: not read - search snippet only | Components: not read - search snippet only
- **Methodology:** not read - search snippet only
- **Experiments & Results:**
  - Setup: not read - search snippet only
  - Metrics: not read - search snippet only
  - Results: not read - search snippet only
  - Baselines: not read - search snippet only
  - Evidence Location: `not read - search snippet only`
- **Limitations (Author-Stated):** not read - search snippet only
- **Research Gap (Evidenced):** not read - search snippet only
- **Code Repository:** [not found](not found) (Official: not found, Framework: not found)
- **Traceable Source URLs:** [https://arxiv.org/abs/2508.10817](https://arxiv.org/abs/2508.10817)
