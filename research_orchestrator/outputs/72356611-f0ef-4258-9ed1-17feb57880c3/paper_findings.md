# Paper Research Findings: Closely Related Work (No Exact Match)

No research paper addressed the exact research problem (e.g. offline mobile edge deployment without cloud connectivity). The following closely related papers provide empirical evidence on models, datasets, and architectures.

- **Session ID:** `72356611-f0ef-4258-9ed1-17feb57880c3`
- **Match Status:** **No exact research paper was found in the searched sources (Closely Related Research Presented)**
- **Total Candidates Discovered & Documented:** 10
- **Search Queries Run:** `coffee leaf disease detection deep learning TensorFlow Lite mobile app offline`, `Coffea arabica leaf disease classification on-device inference TensorFlow Lite`, `mobile offline plant leaf disease detection TensorFlow Lite`, `Android app coffee leaf rust detection offline`

## Research Notes & Methodology
Search queries executed (4): "coffee leaf disease detection deep learning TensorFlow Lite mobile app offline", "Coffea arabica leaf disease classification on-device inference TensorFlow Lite", "mobile offline plant leaf disease detection TensorFlow Lite", "Android app coffee leaf rust detection offline". Candidate papers verified with full-text reading (5): Coffee Leaf Rust Disease Detection and Implementation of an Edge Device for Pruning Infected Leaves via Deep Learning Algorithms., EffResViT-SE FusionNet: A Hybrid Deep Learning Framework for Accurate Classification of Coffee Leaf Diseases., A smartphone application to detection and classification of coffee leaf miner and coffee leaf rust, Early Detection of Coffee Leaf Rust Through Convolutional Neural Networks Trained on Low-Resolution Images, Arabica coffee leaf images dataset for coffee leaf disease detection and classification.. Candidate papers with search snippet only (5): LeafLiteX mobile application for leaf disease detection using U-Net segmentation and lightweight deep learning., GreenAid: a confidence-weighted ensemble deep learning system for real-time plant disease detection and management., DeepEMPR: coffee leaf disease detection with deep learning and enhanced multivariance product representation., Classification of coffee leaf nutrient deficiencies using hybrid feature aggregation with hierarchical localized attention and MobileNet., Multi-Class Plant Leaf Disease Detection: A CNN-based Approach with Mobile App Integration. Validator rejected fields (12): limitations (number '10' in value not found in quote), research_objective (quote not found in paper text), output_type (quote not found in paper text), architecture (quote not found in paper text).

## Top Research Paper Findings

### 1. Coffee Leaf Rust Disease Detection and Implementation of an Edge Device for Pruning Infected Leaves via Deep Learning Algorithms. [CLOSELY RELATED]
- **Authors:** not found
- **Year:** not found | **DOI:** not found
- **Paper URL:** [https://pmc.ncbi.nlm.nih.gov/articles/PMC11679138/](https://pmc.ncbi.nlm.nih.gov/articles/PMC11679138/)
- **Citation:** not found
- **Match Classification:** `closely_related` (Reason: offline operation not stated in the text)
- **Problem Addressed:** Detecting coffee leaf rust to support pruning infected leaves
- **Research Objective:** Develop a deep‑learning detection model and edge device for real‑time coffee leaf rust detection and pruning support
- **Input / Output:** Input: Leaf images captured by a digital mirrorless camera (Canon EOS M3) and a phone camera (Redmi Note 10) | Output: Bounding box coordinates indicating object class (CLR)
- **Dataset:** Name: CLR dataset | Description: CLR dataset | Size: 2025 images | Source: not found
- **Model & Architecture:** Model: YOLOv5 and YOLOv8 | Architecture: One‑stage CNN object detection (YOLO) | Backbone: not found | Components: not found
- **Methodology:** not found
- **Experiments & Results:**
  - Setup: not found
  - Metrics: Frames per second (fps)
  - Results: Detection speed of 10 fps
  - Baselines: not found
  - Evidence Location: `coffee leaf rust disease detection and implementation of an edge device for pruning infected leaves via deep learning algorithms, raka thoriq araaf, arkar minn, tofael ahamed, abstract`
- **Limitations (Author-Stated):** not found
- **Research Gap (Evidenced):** not found
- **Code Repository:** [not found](not found) (Official: not found, Framework: not found)
- **Key Verified Evidence:**
  > [abstract] "Therefore, detecting coffee leaf rust is important to support the decision on pruning infected leaves."
  > [abstract] "An edge device was utilized to deploy real‑time detection of CLR with the best‑trained model."
  > [3.1.3. data annotation] "data labeled as “CLR”"
  > [3.1.2. data preparation] "A total of 2025 images were collected after the augmentation process"
  > [3.1.3. data annotation] "Two YOLO versions were used, YOLOv5 and YOLOv8"
  > [4.3. real-time detection using an edge device] "detection was performed at 10 fps (frames per second)"
- **Traceable Source URLs:** [https://pmc.ncbi.nlm.nih.gov/articles/PMC11679138/](https://pmc.ncbi.nlm.nih.gov/articles/PMC11679138/)

### 2. EffResViT-SE FusionNet: A Hybrid Deep Learning Framework for Accurate Classification of Coffee Leaf Diseases. [CLOSELY RELATED]
- **Authors:** not found
- **Year:** not found | **DOI:** not found
- **Paper URL:** [https://pmc.ncbi.nlm.nih.gov/articles/PMC12689465/](https://pmc.ncbi.nlm.nih.gov/articles/PMC12689465/)
- **Citation:** not found
- **Match Classification:** `closely_related` (Reason: offline operation not stated in the text)
- **Problem Addressed:** Leaf diseases threaten coffee cultivation and yield
- **Research Objective:** not found
- **Input / Output:** Input: RGB leaf images resized to 224×224×3 | Output: not found
- **Dataset:** Name: Kaggle coffee leaf disease dataset | Description: Kaggle coffee leaf disease dataset | Size: 58,555 images | Source: not found
- **Model & Architecture:** Model: EffResViT‑SE FusionNet | Architecture: not found | Backbone: not found | Components: not found
- **Methodology:** not found
- **Experiments & Results:**
  - Setup: not found
  - Metrics: not found
  - Results: 99% validation accuracy
  - Baselines: not found
  - Evidence Location: `effresvit-se fusionnet: a hybrid deep learning framework for accurate classification of coffee leaf diseases, bhoomika mehta, salil bharany, dalia h elkamchouchi, ateeq ur rehman`
- **Limitations (Author-Stated):** High parameter count prevents real‑time edge/mobile use; reliance on large annotated RGB dataset; limited to RGB images
- **Research Gap (Evidenced):** not found
- **Code Repository:** [not found](not found) (Official: not found, Framework: not found)
- **Key Verified Evidence:**
  > [abstract] "Coffee is a vital agricultural commodity that sustains millions of farmers worldwide, yet its cultivation is increasingly threatened by devastating leaf diseases such as Leaf Rust, Phoma, Cercospora, and Leaf Miner."
  > [3.1. input dataset] "This study utilized the publicly available dataset from the Kaggle repository."
  > [abstract] "The model was trained on a large‑scale dataset comprising 58,555 coffee leaf images distributed across five classes"
  > [abstract] "we propose EffResViT‑SE FusionNet, a novel hybrid deep learning framework"
  > [4.5. results on proposed effresvit-se fusionnet model] "training accuracy increases consistently from approximately 0.65 to nearly 0.99, and the validation accuracy maintains itself, increasing from approximately 0.6 to approximately 0.99."
  > [5. conclusion and future work] "The EfficientNetB3‑ResNet50‑ViT hybrid model complicates and raises the number of parameters, which prevents real‑time use in the edge and mobile environment."
- **Traceable Source URLs:** [https://pmc.ncbi.nlm.nih.gov/articles/PMC12689465/](https://pmc.ncbi.nlm.nih.gov/articles/PMC12689465/)

### 3. A smartphone application to detection and classification of coffee leaf miner and coffee leaf rust [CLOSELY RELATED]
- **Authors:** not found
- **Year:** not found | **DOI:** not found
- **Paper URL:** [https://arxiv.org/abs/1904.00742](https://arxiv.org/abs/1904.00742)
- **Citation:** not found
- **Match Classification:** `closely_related` (Reason: offline operation not stated in the text (found: "development of a method and its i implementation as an App"))
- **Problem Addressed:** not found
- **Research Objective:** not found
- **Input / Output:** Input: image captured by a smartphone | Output: disease class (rust or leaf miner) and severity percentage
- **Dataset:** Name: Coffee leaf image dataset | Description: Coffee leaf image dataset | Size: 690 images | Source: not found
- **Model & Architecture:** Model: Artificial Neural Network (Backpropagation) and Extreme Learning Machine | Architecture: not found | Backbone: not found | Components: not found
- **Methodology:** not found
- **Experiments & Results:**
  - Setup: not found
  - Metrics: not found
  - Results: 96.013% accuracy
  - Baselines: not found
  - Evidence Location: `a smartphone application to detection and classification of coffee leaf miner and coffee leaf rust, abstract, 1\. introduction, 2\. algorithms for digital image processing of coffee leaves, 2.1.1. the color space ycbcr`
- **Limitations (Author-Stated):** Segmentation performance degrades with non‑white backgrounds due to camera automatic adjustment
- **Research Gap (Evidenced):** not found
- **Code Repository:** [not found](not found) (Official: not found, Framework: not found)
- **Key Verified Evidence:**
  > [dataset] "The database consists of 690 images, divided according to Table 1."
  > [dataset] "The database consists of 690 images, divided according to Table 1."
  > [results] "artificial neural network trained with Backpropagation algorithms and extreme learning machine was used."
  > [results] "96.013 ± 0.950"
  > [limitations] "The camera’s automatic adjustment, which depends on the ambient colors, generated images with different shades of green."
  > [abstract] "development of a method and its i implementation as an App"
- **Traceable Source URLs:** [https://arxiv.org/abs/1904.00742](https://arxiv.org/abs/1904.00742)

### 4. Early Detection of Coffee Leaf Rust Through Convolutional Neural Networks Trained on Low-Resolution Images [CLOSELY RELATED]
- **Authors:** not found
- **Year:** not found | **DOI:** not found
- **Paper URL:** [https://arxiv.org/abs/2407.14737](https://arxiv.org/abs/2407.14737)
- **Citation:** not found
- **Match Classification:** `closely_related` (Reason: offline operation not stated in the text)
- **Problem Addressed:** Coffee leaf rust disease
- **Research Objective:** Explore deep learning for early disease detection using high‑pass preprocessing
- **Input / Output:** Input: not found | Output: Disease class prediction (leaf rust vs. healthy)
- **Dataset:** Name: Coffee Leaf Disease & Disease and Pest in Coffee Leaves | Description: Coffee Leaf Disease & Disease and Pest in Coffee Leaves | Size: just over 600 images | Source: not found
- **Model & Architecture:** Model: Proposed CNN | Architecture: two convolution layers, max pooling, batch normalization, flattening layer, four dense layers | Backbone: not found | Components: not found
- **Methodology:** not found
- **Experiments & Results:**
  - Setup: not found
  - Metrics: precision, recall, F1-score, Dice coefficient
  - Results: Precision 0.939, Recall 0.939, F1 0.939, Dice 0.942 at 128x128 resolution
  - Baselines: No Edge Detection (Grayscale), No Edge Detection (Color), Edge Detection Equalization
  - Evidence Location: `early detection of coffee leaf rust through convolutional neural networks trained on low-resolution images, abstract, i. introduction, a. analysis of existing solutions, a. dataset`
- **Limitations (Author-Stated):** not found
- **Research Gap (Evidenced):** not found
- **Code Repository:** [not found](not found) (Official: not found, Framework: not found)
- **Key Verified Evidence:**
  > [abstract] "Coffee leaf rust, a foliar disease caused by the fungus Hemileia vastatrix, poses a major threat to coffee production, especially in Central America."
  > [abstract] "To address these challenges, we explore the potential of deep learning models for enhancing early disease detection."
  > [a. dataset] "Images acquired from the Coffee Leaf Disease dataset [5], later aggregated with images from the Disease and Pest in Coffee Leaves dataset [11]"
  > [a. discussion of results] "just over 600 images"
  > [c. model] "Our proposed CNN comprises nine layers"
  > [iii. results] "128x128 | 0.939 | 0.939 | 0.939 | 0.942"
- **Traceable Source URLs:** [https://arxiv.org/abs/2407.14737](https://arxiv.org/abs/2407.14737)

### 5. Arabica coffee leaf images dataset for coffee leaf disease detection and classification. [CLOSELY RELATED]
- **Authors:** not found
- **Year:** not found | **DOI:** not found
- **Paper URL:** [https://pmc.ncbi.nlm.nih.gov/articles/PMC8165403/](https://pmc.ncbi.nlm.nih.gov/articles/PMC8165403/)
- **Citation:** not found
- **Match Classification:** `closely_related` (Reason: offline operation not stated in the text)
- **Problem Addressed:** Coffee leaf disease detection and classification
- **Research Objective:** Introduce Arabica coffee leaf image datasets JMuBEN and JMuBEN2
- **Input / Output:** Input: Leaf images | Output: Disease class labels
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
  > [abstract] "facilitates training and validation during the utilization of deep learning algorithms for coffee plant leaf disease recognition and classification"
  > [abstract] "This article introduces Arabica coffee leaf datasets known as JMuBEN and JMuBEN2"
  > [abstract] "Arabica coffee leaf datasets known as JMuBEN and JMuBEN2"
  > [abstract] "In total, the dataset contains 58,555 leaf images"
- **Traceable Source URLs:** [https://pmc.ncbi.nlm.nih.gov/articles/PMC8165403/](https://pmc.ncbi.nlm.nih.gov/articles/PMC8165403/)

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

### 7. GreenAid: a confidence-weighted ensemble deep learning system for real-time plant disease detection and management. [CLOSELY RELATED]
- **Authors:** not found
- **Year:** not found | **DOI:** not found
- **Paper URL:** [https://pmc.ncbi.nlm.nih.gov/articles/PMC13284324/](https://pmc.ncbi.nlm.nih.gov/articles/PMC13284324/)
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
- **Traceable Source URLs:** [https://pmc.ncbi.nlm.nih.gov/articles/PMC13284324/](https://pmc.ncbi.nlm.nih.gov/articles/PMC13284324/)

### 8. DeepEMPR: coffee leaf disease detection with deep learning and enhanced multivariance product representation. [CLOSELY RELATED]
- **Authors:** not found
- **Year:** not found | **DOI:** not found
- **Paper URL:** [https://pmc.ncbi.nlm.nih.gov/articles/PMC11623072/](https://pmc.ncbi.nlm.nih.gov/articles/PMC11623072/)
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
- **Traceable Source URLs:** [https://pmc.ncbi.nlm.nih.gov/articles/PMC11623072/](https://pmc.ncbi.nlm.nih.gov/articles/PMC11623072/)

### 9. Classification of coffee leaf nutrient deficiencies using hybrid feature aggregation with hierarchical localized attention and MobileNet. [CLOSELY RELATED]
- **Authors:** not found
- **Year:** not found | **DOI:** not found
- **Paper URL:** [https://pmc.ncbi.nlm.nih.gov/articles/PMC13161101/](https://pmc.ncbi.nlm.nih.gov/articles/PMC13161101/)
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
- **Traceable Source URLs:** [https://pmc.ncbi.nlm.nih.gov/articles/PMC13161101/](https://pmc.ncbi.nlm.nih.gov/articles/PMC13161101/)

### 10. Multi-Class Plant Leaf Disease Detection: A CNN-based Approach with Mobile App Integration [CLOSELY RELATED]
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
