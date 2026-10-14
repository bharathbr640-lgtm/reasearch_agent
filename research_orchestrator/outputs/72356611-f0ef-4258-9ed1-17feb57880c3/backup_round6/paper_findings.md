# Research Paper Findings & Evidence Report (Agent 2)

- **Session ID:** `72356611-f0ef-4258-9ed1-17feb57880c3`
- **Match Status:** **No exact research paper was found in the searched sources (Closely Related Research Presented)**
- **Total Candidates Discovered & Documented:** 10
- **Search Queries Run:** `coffee leaf disease classification deep learning`, `smartphone application coffee leaf disease classification`, `coffee leaf disease image dataset`, `TensorFlow Lite coffee leaf disease classification`

## Research Notes & Methodology
Search queries executed (4): "coffee leaf disease classification deep learning", "smartphone application coffee leaf disease classification", "coffee leaf disease image dataset", "TensorFlow Lite coffee leaf disease classification". Candidate papers verified with full-text reading (5): https://pmc.ncbi.nlm.nih.gov/articles/PMC11623072/, https://pmc.ncbi.nlm.nih.gov/articles/PMC12689465/, https://arxiv.org/abs/2601.12109, https://arxiv.org/abs/1904.00742, https://pmc.ncbi.nlm.nih.gov/articles/PMC8165403/. Candidate papers with search snippet only (5): Robust coffee plant disease classification using deep learning and advanced feature engineering techniques., Evaluating Data Augmentation Techniques for Coffee Leaf Disease Classification, Coffee Disease Visualization and Classification., Deep Learning for Classification and Severity Estimation of Coffee Leaf Biotic Stress, Early Detection of Coffee Leaf Rust Through Convolutional Neural Networks Trained on Low-Resolution Images.

## Top Research Paper Findings

### 1. https://pmc.ncbi.nlm.nih.gov/articles/PMC11623072/ [CLOSELY RELATED]
- **Authors:** Ahmet Topal, Burcu Tunga, Erfan Babaee Tirkolaee
- **Year:** 2024 | **DOI:** 10.7717/peerj-cs.2406
- **Paper URL:** [https://pmc.ncbi.nlm.nih.gov/articles/PMC11623072/](https://pmc.ncbi.nlm.nih.gov/articles/PMC11623072/)
- **Citation:** Ahmet Topal, Burcu Tunga, Erfan Babaee Tirkolaee (2024). . doi:10.7717/peerj-cs.2406
- **Match Classification:** `closely_related`
- **Problem Addressed:** Rapid and accurate disease identification is crucial for effective management (Abstract).
- **Research Objective:** Enhance classification of coffee leaf diseases and severity using enhanced multivariance product representation (Abstract).
- **Input / Output:** Input: Photo of coffee leaf (RGB 512×256). | Output: Disease class and severity level.
- **Dataset:** Name: Arabica Coffee Leaves dataset with 1,685 images (healthy and | Description: Arabica Coffee Leaves dataset with 1,685 images (healthy and diseased) (Dataset Description). | Size: 1,685 images | Source: not found
- **Model & Architecture:** Model: CNNs (AlexNet, VGG16, ResNet50) with EMPR preprocessing. | Architecture: not found | Backbone: not found | Components: not found
- **Methodology:** The study adds an EMPR‑based channel to the images and applies contrast enhancement at different levels before training CNN models (Proposed Methods).
- **Experiments & Results:**
  - Setup: not found
  - Metrics: Accuracy, Precision, Recall, F1-score, Sensitivity, AUC
  - Results: Its precision scored above 96% at _α_ levels 1 and 2, outperforming the other models. AlexNet demonstrated high consistency in accuracy metric across all _α_ levels with over 94% accuracy, even though there was a slight decrease as _α_ increased.
  - Baselines: Compared against VGG16
  - Evidence Location: `Outline_And_Abstract, Dataset Description, Proposed Methods, Results And Discussions, Conclusion`
- **Limitations (Author-Stated):** Background bias may affect classification; EMPR and HDMR not yet adapted for segmentation (Conclusion).
- **Research Gap (Evidenced):** Address background bias and extend EMPR to disease segmentation (Conclusion).
- **Code Repository:** [not found](not found) (Official: not found, Framework: not found)
- **Key Verified Evidence:**
  > [Abstract] "Plant diseases threaten agricultural sustainability by reducing crop yields."
  > [Limitations] "One of the primary factors influencing classification success is the bias introduced by the background, which should be addressed in future research."
  > [Limitations] "Efforts could aim to adapt EMPR and HDMR to disease segmentation."
- **Traceable Source URLs:** [https://pmc.ncbi.nlm.nih.gov/articles/PMC11623072/](https://pmc.ncbi.nlm.nih.gov/articles/PMC11623072/), [https://doi.org/10.7717/peerj-cs.2406](https://doi.org/10.7717/peerj-cs.2406)

### 2. https://pmc.ncbi.nlm.nih.gov/articles/PMC12689465/ [CLOSELY RELATED]
- **Authors:** Bhoomika Mehta, Salil Bharany, Dalia H Elkamchouchi, Ateeq Ur Rehman, Rahul Singh, Seada Hussen Adem
- **Year:** 2025 | **DOI:** 10.1002/fsn3.71311
- **Paper URL:** [https://pmc.ncbi.nlm.nih.gov/articles/PMC12689465/](https://pmc.ncbi.nlm.nih.gov/articles/PMC12689465/)
- **Citation:** Bhoomika Mehta, Salil Bharany, Dalia H Elkamchouchi et al. (2025). . doi:10.1002/fsn3.71311
- **Match Classification:** `closely_related`
- **Problem Addressed:** Coffee leaf diseases reduce yield and quality, requiring rapid diagnosis (Abstract).
- **Research Objective:** Develop a hybrid framework integrating EfficientNetB3, ResNet50, Vision Transformer, and SE blocks for accurate coffee leaf disease classification (Abstract).
- **Input / Output:** Input: RGB image of coffee leaf (224×224). | Output: Disease label among five classes.
- **Dataset:** Name: 58,555 images across five classes | Description: 58,555 images across five classes: Healthy 18,984; Miner 16,983; Leaf Rust 8,336; Cercospora 7,681; Phoma 6,571 (Input Dataset). | Size: 58,555 images | Source: not found
- **Model & Architecture:** Model: EffResViT‑SE FusionNet (EfficientNetB3 + ResNet50 + Vision Transformer + SE blocks). | Architecture: not found | Backbone: not found | Components: not found
- **Methodology:** The model integrates EfficientNetB3, ResNet50, Vision Transformer and SE blocks for feature extraction and fusion (Proposed Effresvit‑Se Fusionnet Model).
- **Experiments & Results:**
  - Setup: not found
  - Metrics: Accuracy, Precision, Recall, Sensitivity, AUC
  - Results: ( [2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC12689465/#fsn371311-bib-0024)) employed CoffeeNet a ResNet‐50 model with spatial‐channel attention, obtaining an impressive accuracy of 98.54%. ( [2023](https://pmc.ncbi.nlm.nih.gov/articles/PMC12689465/#fsn371311-bib-0007)) used DenseNet201 on 5337 images, attaining 94.8% accuracy.
  - Baselines: Compared against YOLOv5, YOLOv8, MobileNetV2, VGG16
  - Evidence Location: `Outline_And_Abstract, 3.1. Input Dataset, 4.5. Results On Proposed Effresvit-Se Fusionnet Model, 5\. Conclusion And Future Work`
- **Limitations (Author-Stated):** Hybrid model raises parameter count, preventing real‑time edge/mobile use
- **Research Gap (Evidenced):** Reduce model size for on‑device deployment and increase robustness to varied lighting/backgrounds (Conclusion).
- **Code Repository:** [not found](not found) (Official: not found, Framework: not found)
- **Key Verified Evidence:**
  > [Abstract] "Coffee is a vital agricultural commodity that sustains millions of farmers worldwide, yet its cultivation is increasingly threatened by devastating leaf diseases such as Leaf Rust, Phoma, Cercospora, and Leaf Miner."
  > [Limitations] "The EfficientNetB3‐ResNet50‐ViT hybrid model complicates and raises the number of parameters, which prevents real‐time use in the edge and mobile environment."
- **Traceable Source URLs:** [https://pmc.ncbi.nlm.nih.gov/articles/PMC12689465/](https://pmc.ncbi.nlm.nih.gov/articles/PMC12689465/), [https://doi.org/10.1002/fsn3.71311](https://doi.org/10.1002/fsn3.71311)

### 3. https://arxiv.org/abs/2601.12109 [CLOSELY RELATED]
- **Authors:** Larissa Ferreira Rodrigues Moreira, Rodrigo Moreira, Leonardo Gabriel Ferreira Rodrigues
- **Year:** 2026 | **DOI:** not found
- **Paper URL:** [https://arxiv.org/abs/2601.12109](https://arxiv.org/abs/2601.12109)
- **Citation:** not found
- **Match Classification:** `closely_related`
- **Problem Addressed:** High‑accuracy coffee leaf disease models are hard to adopt on constrained devices and intermittent connectivity (Abstract).
- **Research Objective:** Use knowledge distillation and ensemble learning to create compact CNNs suitable for on‑device diagnosis (Abstract).
- **Input / Output:** Input: Image of coffee leaf (RGB). | Output: Disease label (rust vs. healthy).
- **Dataset:** Name: RoCoLe dataset | Description: RoCoLe dataset: 1,560 images (791 healthy, 769 diseased) (Dataset). | Size: 1,560 images | Source: not found
- **Model & Architecture:** Model: Distilled tiny CNNs (MobileNetV3, SqueezeNet, ResNet‑18) combined via stacking ensembles. | Architecture: not found | Backbone: not found | Components: not found
- **Methodology:** MobileNetV3, SqueezeNet, and ResNet‑18 were selected as lightweight base classifiers for low computational cost (C. Lightweight Base Classifiers).
- **Experiments & Results:**
  - Setup: learning rate of 0.001, 50 epochs
  - Metrics: Accuracy, Precision, Recall, F1-score
  - Results: All
meta-models achieved an identical accuracy of 94.25% and
recall of 94.24%.
  - Baselines: not found
  - Evidence Location: `Outline_And_Abstract, B. Dataset, C. Lightweight Base Classifiers (Base Models), B. Ensemble Evaluation, V. Concluding Remarks`
- **Limitations (Author-Stated):** not explicitly identified in the available paper text
- **Research Gap (Evidenced):** not explicitly identified in the available paper text
- **Code Repository:** [not found](not found) (Official: not found, Framework: not found)
- **Key Verified Evidence:**
  > [Abstract] "— **Coffee yields are contingent on the timely and** **accurate diagnosis of diseases; however, assessing leaf diseases** **in the field presents significant challenges."
- **Traceable Source URLs:** [https://arxiv.org/abs/2601.12109](https://arxiv.org/abs/2601.12109), [https://arxiv.org/pdf/2601.12109](https://arxiv.org/pdf/2601.12109), [https://arxiv.org/pdf/2601.12109.pdf](https://arxiv.org/pdf/2601.12109.pdf), [arxiv:2601.12109](arxiv:2601.12109)

### 4. https://arxiv.org/abs/1904.00742 [EXACT RESEARCH]
- **Authors:** Giuliano L. Manso, Helder Knidel, Renato A. Krohling, Jose A. Ventura
- **Year:** 2019 | **DOI:** not found
- **Paper URL:** [https://arxiv.org/abs/1904.00742](https://arxiv.org/abs/1904.00742)
- **Citation:** not found
- **Match Classification:** `exact`
- **Problem Addressed:** Coffee farmers need automatic detection of leaf rust and leaf miner from smartphone images (Abstract).
- **Research Objective:** Develop a smartphone app that segments coffee leaves, extracts features, and classifies rust vs. miner with severity estimation (Proposed Approach).
- **Input / Output:** Input: 10‑MP smartphone photo of coffee leaf (various backgrounds). | Output: Disease class (rust or miner) and percentage of injured area.
- **Dataset:** Name: 690 images total (174 healthy, 264 miner, 252 rust) | Description: 690 images total (174 healthy, 264 miner, 252 rust); balanced training set of 256 images per class (Database). | Size: 690 images | Source: not found
- **Model & Architecture:** Model: Artificial Neural Network (Backpropagation) and Extreme Learning Machine. | Architecture: not found | Backbone: not found | Components: not found
- **Methodology:** The system segments the leaf, extracts texture and color features, and classifies using ANN or ELM, also calculating injury percentage (Proposed Approach).
- **Experiments & Results:**
  - Setup: not found
  - Metrics: Accuracy, Precision, Recall, Sensitivity
  - Results: 38% 12:26 AM
Leaf
Image 1
Image 2
Image 3

Figure 17: Initial screen with the list of previous classifications.
  - Baselines: not found
  - Evidence Location: `Outline_And_Abstract, 3.1. Database, 2.6. Proposed Approach, 3.3.2. Classification Results Using Backpropagation, 5\. Conclusion`
- **Limitations (Author-Stated):** segmentation sensitive to lighting and background color (Conclusion).
- **Research Gap (Evidenced):** Develop robust segmentation for varied backgrounds and expand to additional diseases (Conclusion).
- **Code Repository:** [not found](not found) (Official: not found, Framework: not found)
- **Key Verified Evidence:**
  > [Abstract] "Generally, the identification and classification of plant diseases and/or pests are performed by an expert ."
  > [Limitations] "In the segmentation process, various types of backgrounds for the image using the HSV and YCbCr color spaces are tested."
- **Traceable Source URLs:** [https://arxiv.org/abs/1904.00742](https://arxiv.org/abs/1904.00742), [https://arxiv.org/pdf/1904.00742](https://arxiv.org/pdf/1904.00742), [https://arxiv.org/pdf/1904.00742.pdf](https://arxiv.org/pdf/1904.00742.pdf), [arxiv:1904.00742](arxiv:1904.00742)

### 5. https://pmc.ncbi.nlm.nih.gov/articles/PMC8165403/ [CLOSELY RELATED]
- **Authors:** Jennifer Jepkoech, David Muchangi Mugo, Benson K Kenduiywo, Edna Chebet Too
- **Year:** 2021 | **DOI:** 10.1016/j.dib.2021.107142
- **Paper URL:** [https://pmc.ncbi.nlm.nih.gov/articles/PMC8165403/](https://pmc.ncbi.nlm.nih.gov/articles/PMC8165403/)
- **Citation:** Jennifer Jepkoech, David Muchangi Mugo, Benson K Kenduiywo et al. (2021). . doi:10.1016/j.dib.2021.107142
- **Match Classification:** `closely_related`
- **Problem Addressed:** Need for publicly available coffee leaf image data to train disease classifiers (Abstract).
- **Research Objective:** Provide Arabica coffee leaf image datasets (JMuBEN and JMuBEN2) for disease detection and classification (Abstract).
- **Input / Output:** Input: not applicable | Output: not applicable
- **Dataset:** Name: 58,555 leaf images across five classes (Cercospora 7,682 | Description: 58,555 leaf images across five classes (Cercospora 7,682; Rust 8,337; Phoma 6,572; Miner 16,979; Healthy 18,985) (1. Data Description). | Size: 58,555 leaf images | Source: not found
- **Model & Architecture:** Model: not applicable | Architecture: not found | Backbone: not found | Components: not found
- **Methodology:** Images were captured with a high‑resolution digital camera in the field and then pre‑processed with noise filtering, cropping and data augmentation (3.1. Noise Filtering, 3.2. Cropping, 3.3. Data Augmentation).
- **Experiments & Results:**
  - Setup: not found
  - Metrics: Accuracy
  - Results: not found
  - Baselines: not found
  - Evidence Location: `Abstract, 1\. Data Description, 2.1. Data Acquisition, 3.1. Noise Filtering, 3.2. Cropping, 3.3. Data Augmentation, Arabica Coffee Leaf Images Dataset For Coffee Leaf Disease Detection And Classification`
- **Limitations (Author-Stated):** not explicitly identified in the available paper text
- **Research Gap (Evidenced):** not explicitly identified in the available paper text
- **Code Repository:** [not found](not found) (Official: not found, Framework: not found)
- **Key Verified Evidence:**
  > [Abstract] "This article introduces Arabica coffee leaf datasets known as JMuBEN and JMuBEN2."
- **Traceable Source URLs:** [https://pmc.ncbi.nlm.nih.gov/articles/PMC8165403/](https://pmc.ncbi.nlm.nih.gov/articles/PMC8165403/), [https://doi.org/10.1016/j.dib.2021.107142](https://doi.org/10.1016/j.dib.2021.107142)

### 6. Robust coffee plant disease classification using deep learning and advanced feature engineering techniques. [CLOSELY RELATED]
- **Authors:** Hanin Ardah, Maher Alrahhal, Walaa M Abd-Elhafiez, Doaa Trabay
- **Year:** 2025 | **DOI:** 10.7717/peerj-cs.3386
- **Paper URL:** [https://pmc.ncbi.nlm.nih.gov/articles/PMC12695173/](https://pmc.ncbi.nlm.nih.gov/articles/PMC12695173/)
- **Citation:** Hanin Ardah, Maher Alrahhal, Walaa M Abd-Elhafiez et al. (2025). Robust coffee plant disease classification using deep learning and advanced feature engineering techniques.. doi:10.7717/peerj-cs.3386
- **Match Classification:** `closely_related`
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
- **Traceable Source URLs:** [https://pmc.ncbi.nlm.nih.gov/articles/PMC12695173/](https://pmc.ncbi.nlm.nih.gov/articles/PMC12695173/), [https://doi.org/10.7717/peerj-cs.3386](https://doi.org/10.7717/peerj-cs.3386)

### 7. Evaluating Data Augmentation Techniques for Coffee Leaf Disease Classification [CLOSELY RELATED]
- **Authors:** Adrian Gheorghiu, Iulian-Marius Tăiatu, Dumitru-Clementin Cercel, Iuliana Marin, Florin Pop
- **Year:** 2024 | **DOI:** not found
- **Paper URL:** [https://arxiv.org/abs/2401.05768](https://arxiv.org/abs/2401.05768)
- **Citation:** not found
- **Match Classification:** `closely_related`
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
- **Traceable Source URLs:** [https://arxiv.org/abs/2401.05768](https://arxiv.org/abs/2401.05768)

### 8. Coffee Disease Visualization and Classification. [CLOSELY RELATED]
- **Authors:** Milkisa Yebasse, Birhanu Shimelis, Henok Warku, Jaepil Ko, Kyung Joo Cheoi
- **Year:** 2021 | **DOI:** 10.3390/plants10061257
- **Paper URL:** [https://pmc.ncbi.nlm.nih.gov/articles/PMC8235481/](https://pmc.ncbi.nlm.nih.gov/articles/PMC8235481/)
- **Citation:** Milkisa Yebasse, Birhanu Shimelis, Henok Warku et al. (2021). Coffee Disease Visualization and Classification.. doi:10.3390/plants10061257
- **Match Classification:** `closely_related`
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
- **Traceable Source URLs:** [https://pmc.ncbi.nlm.nih.gov/articles/PMC8235481/](https://pmc.ncbi.nlm.nih.gov/articles/PMC8235481/), [https://doi.org/10.3390/plants10061257](https://doi.org/10.3390/plants10061257)

### 9. Deep Learning for Classification and Severity Estimation of Coffee Leaf Biotic Stress [CLOSELY RELATED]
- **Authors:** J. G. M. Esgario, R. A. Krohling, J. A. Ventura
- **Year:** 2019 | **DOI:** not found
- **Paper URL:** [https://arxiv.org/abs/1907.11561](https://arxiv.org/abs/1907.11561)
- **Citation:** not found
- **Match Classification:** `closely_related`
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
- **Traceable Source URLs:** [https://arxiv.org/abs/1907.11561](https://arxiv.org/abs/1907.11561)

### 10. Early Detection of Coffee Leaf Rust Through Convolutional Neural Networks Trained on Low-Resolution Images [CLOSELY RELATED]
- **Authors:** Angelly Cabrera, Kleanthis Avramidis, Shrikanth Narayanan
- **Year:** 2024 | **DOI:** not found
- **Paper URL:** [https://arxiv.org/abs/2407.14737](https://arxiv.org/abs/2407.14737)
- **Citation:** not found
- **Match Classification:** `closely_related`
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
- **Traceable Source URLs:** [https://arxiv.org/abs/2407.14737](https://arxiv.org/abs/2407.14737)
