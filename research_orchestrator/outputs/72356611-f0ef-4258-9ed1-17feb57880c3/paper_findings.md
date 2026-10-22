# Paper Research Findings: Closely Related Work (No Exact Match)

No research paper addressed the exact research problem (e.g. offline mobile edge deployment without cloud connectivity). The following closely related papers provide empirical evidence on models, datasets, and architectures.

- **Session ID:** `72356611-f0ef-4258-9ed1-17feb57880c3`
- **Match Status:** **No exact research paper was found in the searched sources (Closely Related Research Presented)**
- **Total Candidates Discovered & Documented:** 10
- **Search Queries Run:** `coffee leaf disease detection offline Android TensorFlow Lite`, `on-device coffee leaf disease classification mobile`, `Android offline plant leaf disease detection TensorFlow Lite`, `coffee leaf disease mobile application Android`

## Research Notes & Methodology
Search queries executed (4): "coffee leaf disease detection offline Android TensorFlow Lite", "on-device coffee leaf disease classification mobile", "Android offline plant leaf disease detection TensorFlow Lite", "coffee leaf disease mobile application Android". Candidate papers verified with full-text reading (5): A smartphone application to detection and classification of coffee leaf miner and coffee leaf rust, Early Detection of Coffee Leaf Rust Through Convolutional Neural Networks Trained on Low-Resolution Images, Energy-Aware Ensemble Learning for Coffee Leaf Disease Classification, Arabica coffee leaf images dataset for coffee leaf disease detection and classification., Artificial intelligence for detection and quantification of rust and leaf miner in coffee crop. Candidate papers with search snippet only (5): GreenAid: a confidence-weighted ensemble deep learning system for real-time plant disease detection and management., LeafLiteX mobile application for leaf disease detection using U-Net segmentation and lightweight deep learning., Coffee Leaf Rust Disease Detection and Implementation of an Edge Device for Pruning Infected Leaves via Deep Learning Algorithms., Multi-Class Plant Leaf Disease Detection: A CNN-based Approach with Mobile App Integration, Plant disease detection model for edge computing devices.. Validator rejected fields (6): research_objective (quote not found in paper text), architecture (number '10' in value not found in quote), input_type (quote not found in paper text), dataset_description (quote not found in paper text).

## Top Research Paper Findings

### 1. A smartphone application to detection and classification of coffee leaf miner and coffee leaf rust [CLOSELY RELATED]
- **Authors:** Giuliano L. Manso, Helder Knidel, Renato A. Krohling, Jose A. Ventura
- **Year:** 2019 | **DOI:** not found
- **Paper URL:** [https://arxiv.org/abs/1904.00742](https://arxiv.org/abs/1904.00742)
- **Citation:** Giuliano L. Manso, Helder Knidel, Renato A. Krohling et al. (2019). A smartphone application to detection and classification of coffee leaf miner and coffee leaf rust. cs.CV.
- **Match Classification:** `closely_related` (Reason: offline operation not stated in the text (found: "development of a method and its i implementation as an App that allow the detection of the foliar damages"))
- **Problem Addressed:** crop infestation by leaf rust and leaf miner affecting coffee farmers in Brazil
- **Research Objective:** not found
- **Input / Output:** Input: smartphone image of coffee leaf | Output: disease class (rust or leaf miner) and severity percentage
- **Dataset:** Name: not found | Description: Images were captured with an ASUS Zenfone 2 smartphone at 10 Megapixels resolution | Size: 690 | Source: not found
- **Model & Architecture:** Model: Artificial Neural Network (Backpropagation) and Extreme Learning Machine | Architecture: not found | Backbone: not found | Components: not found
- **Methodology:** The system takes a smartphone image, segments the leaf, segments damaged area, extracts features, classifies the disease, and computes severity percentage
- **Experiments & Results:**
  - Setup: not found
  - Metrics: Sensitivity and precision
  - Results: Accuracy 96.013% ± 0.950, Precision 96.151% ± 0.951, Recall 93.233% ± 0.922
  - Baselines: Backpropagation ANN and Extreme Learning Machine
  - Evidence Location: `a smartphone application to detection and classification of coffee leaf miner and coffee leaf rust, abstract, 1\. introduction, 2\. algorithms for digital image processing of coffee leaves, 2.1.1. the color space ycbcr`
- **Limitations (Author-Stated):** Segmentation degrades with non‑white backgrounds due to camera automatic adjustment
- **Research Gap (Evidenced):** Need more robust segmentation methods that work across varied background types
- **Code Repository:** [not found](not found) (Official: not found, Framework: not found)
- **Key Verified Evidence:**
  > [abstract] "One of the problems facing coffee farmers in Brazil is crop infestation, particularly by leaf rust _Hemileia_ _vastatrix_ and leaf miner _Leucoptera coffeella._"
  > [abstract] "Coffee leaf Rust, Coffee leaf miner, _Hemileia vastatrix, Leucoptera coffeella._"
  > [2.6. proposed approach] "The system receives as input an image captured by the smartphone"
  > [2.6. proposed approach] "In addition, it calculates the percentage of injured area"
  > [3.1. database] "The images used in this work were captured using the ASUS Zenfone 2 smartphone (ZE551ML) with a resolution of 10 Megapixels (4096x2304 pixels)."
  > [3.1. database] "The database consists of 690 images"
  > [3.3.2. classification results using backpropagation] "with 70% of data for training and 30% for testing"
  > [3.3. classification results] "In this work, artificial neural network trained with Backpropagation algorithms and extreme learning machine was used."
  > [2.6. proposed approach] "The system receives as input an image captured by the smartphone, then identify the leaf of the coffee in the image by means of the segmentation, identify the damaged foliar area contained in the leaf and classify."
  > [3.3. classification results] "the best architecture were evaluated according to the most used metrics: sensitivity and precision"
  > [3.3.2. classification results using backpropagation] "| 3 | 40 | 0.1 | Constant | 96.013 ± 0.950 | 96.151 ± 0.951 | 93.233 ± 0.922 |"
  > [3.3. classification results] "In this work, artificial neural network trained with Backpropagation algorithms and extreme learning machine was used."
  > [5. conclusion] "The camera’s automatic adjustment, which depends on the ambient colors, generated images with different shades of green."
  > [5. conclusion] "the next steps for future work is to investigate segmentation methods that are more robust, i.e., that present good results for various types of backgrounds."
  > [abstract] "detection of the foliar damages from images of coffee leaf that are captured using a smartphone, and identify whether it is rust or leaf miner,"
  > [abstract] "development of a method and its i implementation as an App that allow the detection of the foliar damages"
- **Traceable Source URLs:** [https://arxiv.org/abs/1904.00742](https://arxiv.org/abs/1904.00742)

### 2. Early Detection of Coffee Leaf Rust Through Convolutional Neural Networks Trained on Low-Resolution Images [CLOSELY RELATED]
- **Authors:** Angelly Cabrera, Kleanthis Avramidis, Shrikanth Narayanan
- **Year:** 2024 | **DOI:** not found
- **Paper URL:** [https://arxiv.org/abs/2407.14737](https://arxiv.org/abs/2407.14737)
- **Citation:** Angelly Cabrera, Kleanthis Avramidis, Shrikanth Narayanan (2024). Early Detection of Coffee Leaf Rust Through Convolutional Neural Networks Trained on Low-Resolution Images. cs.CV, cs.LG.
- **Match Classification:** `closely_related` (Reason: offline operation not stated in the text)
- **Problem Addressed:** coffee leaf rust disease
- **Research Objective:** explore deep learning models for early disease detection of coffee leaf rust
- **Input / Output:** Input: not found | Output: disease class prediction
- **Dataset:** Name: Coffee Leaf Disease and Disease and Pest in Coffee Leaves | Description: The datasets consist of coffee leaves from India and Brazil, manually collected from farms and already exhibiting various diseases. | Size: just over 600 images | Source: not found
- **Model & Architecture:** Model: proposed CNN | Architecture: two convolution layers, max pooling, batch normalization, flattening layer, four dense layers | Backbone: not found | Components: not found
- **Methodology:** A nine‑layer CNN with two convolution layers, max pooling, batch normalization, flattening, and four dense layers
- **Experiments & Results:**
  - Setup: not found
  - Metrics: precision, recall, F1-score, Dice coefficient
  - Results: 128x128 resolution: precision 0.939, recall 0.939, F1 0.939, Dice 0.942
  - Baselines: No Edge Detection (Grayscale), No Edge Detection (Color), Edge Detection Equalization
  - Evidence Location: `early detection of coffee leaf rust through convolutional neural networks trained on low-resolution images, abstract, i. introduction, a. analysis of existing solutions, a. dataset`
- **Limitations (Author-Stated):** small dataset size of just over 600 images
- **Research Gap (Evidenced):** need for disease detection methods that require limited processing power and data
- **Code Repository:** [not found](not found) (Official: not found, Framework: not found)
- **Key Verified Evidence:**
  > [abstract] "Coffee leaf rust, a foliar disease caused by the fungus** **Hemileia vastatrix, poses a major threat to coffee production"
  > [abstract] "To address these challenges, we explore the potential of deep learning models for enhancing early disease detection."
  > [abstract] "Coffee leaf rust, a foliar disease caused by the fungus** **Hemileia vastatrix, poses a major threat to coffee production"
  > [c. model] "make final class predictions."
  > [a. dataset] "images acquired from the coffee leaf disease dataset \[5\], later aggregated with images from the disease and pest in coffee leaves dataset \[11\],"
  > [a. dataset] "These datasets consist of coffee leaves from India and Brazil, which were manually collected from farms and already exhibiting various diseases."
  > [a. discussion of results] "comprising just over 600 images"
  > [c. model] "Our proposed CNN comprises nine layers"
  > [c. model] "two convolution layers, then a max pooling, batch normalization, flattening layer, and finishing with four dense layers"
  > [c. model] "two convolution layers, then a max pooling, batch normalization, flattening layer, and finishing with four dense layers"
  > [iii. results] "The CNN’s performance was assessed using precision, recall, F1-score, and the Dice coefficient."
  > [iii. results] "128x128 | 0.939 | 0.939 | 0.939 | 0.942"
  > [iii. results] "No Edge Detection (Grayscale) | 0.117 | 0.341 | 0.174 | 0.000"
  > [a. discussion of results] "the relatively small dataset size, comprising just over 600 images, which is substantially fewer than those used in comparable research."
  > [abstract] "deep learning models require extensive processing power and large amounts of data for model training, resources that are typically scarce."
  > [c. model] "make final class predictions."
- **Traceable Source URLs:** [https://arxiv.org/abs/2407.14737](https://arxiv.org/abs/2407.14737)

### 3. Energy-Aware Ensemble Learning for Coffee Leaf Disease Classification [CLOSELY RELATED]
- **Authors:** Larissa Ferreira Rodrigues Moreira, Rodrigo Moreira, Leonardo Gabriel Ferreira Rodrigues
- **Year:** 2026 | **DOI:** not found
- **Paper URL:** [https://arxiv.org/abs/2601.12109](https://arxiv.org/abs/2601.12109)
- **Citation:** Larissa Ferreira Rodrigues Moreira, Rodrigo Moreira, Leonardo Gabriel Ferreira Rodrigues (2026). Energy-Aware Ensemble Learning for Coffee Leaf Disease Classification. cs.CV.
- **Match Classification:** `closely_related` (Reason: offline operation not stated in the text)
- **Problem Addressed:** timely and accurate diagnosis of coffee leaf diseases in the field
- **Research Objective:** facilitate sustainable on-device diagnosis through knowledge distillation and ensemble learning
- **Input / Output:** Input: leaf images | Output: disease classification (healthy or diseased)
- **Dataset:** Name: RoCoLe coffee leaf dataset | Description: not found | Size: not found | Source: not found
- **Model & Architecture:** Model: MobileNetV3, SqueezeNet, and ResNet-18 base classifiers | Architecture: lightweight CNN backbones with simple ensembling (optimized averaging and stacking) | Backbone: not found | Components: not found
- **Methodology:** knowledge distillation from high‑capacity CNNs to compact CNNs combined with ensemble learning using averaging and stacking
- **Experiments & Results:**
  - Setup: not found
  - Metrics: accuracy and recall
  - Results: 94.25% accuracy
  - Baselines: MobileNet, ResNet, and SqueezeNet baseline CNNs
  - Evidence Location: `energy-aware ensemble learning for coffee leaf disease classification, abstract, i. introduction, ii. related work, iii. proposed approach`
- **Limitations (Author-Stated):** not found
- **Research Gap (Evidenced):** not found
- **Code Repository:** [not found](not found) (Official: not found, Framework: not found)
- **Key Verified Evidence:**
  > [abstract] "Coffee yields are contingent on the timely and accurate diagnosis of diseases; however, assessing leaf diseases in the field presents significant challenges."
  > [abstract] "This study aims to facilitate sustainable on-device diagnosis through knowledge distillation: high-capacity Convolutional Neural Networks (CNNs) trained in data centers transfer knowledge to compact CNNs through Ensemble Learning (EL)."
  > [abstract] "On a curated coffee leaf dataset, distilled tiny ensembles achieved competitive with prior work with significantly reduced energy consumption and carbon footprint."
  > [b. dataset] "1560 images categorized into 2 classes"
  > [b. dataset] "2 classes with 791 healthy leaves and 769 diseased leaves"
  > [b. dataset] "We used the RoCoLe coffee leaf dataset"
  > [b. dataset] "partitioned into training and test sets using a standard 80/20 stratified split."
  > [c. lightweight base classifiers (base models)] "We selected three CNN architectures as our base classifiers: MobileNetV3, SqueezeNet, and ResNet-18."
  > [iii. proposed approach] "We introduce an energy-aware pipeline that pairs lightweight CNN backbones with simple ensembling (optimized averaging and stacking) to deliver high-accuracy, on-device diagnosis"
  > [iii. proposed approach] "We introduce an energy-aware pipeline that pairs lightweight CNN backbones with simple ensembling (optimized averaging and stacking) to deliver high-accuracy, on-device diagnosis"
  > [b. ensemble evaluation] "All meta-models achieved an identical accuracy of 94.25% and recall of 94.24%."
  > [b. ensemble evaluation] "All meta-models achieved an identical accuracy of 94.25% and recall of 94.24%."
  > [iv. results and discussion] "First, we trained three baseline CNNs (MobileNet, ResNet, and SqueezeNet)."
  > [iii. proposed approach] "to deliver high-accuracy, on-device diagnosis"
- **Traceable Source URLs:** [https://arxiv.org/abs/2601.12109](https://arxiv.org/abs/2601.12109)

### 4. Arabica coffee leaf images dataset for coffee leaf disease detection and classification. [CLOSELY RELATED]
- **Authors:** Jennifer Jepkoech, David Muchangi Mugo, Benson K Kenduiywo, Edna Chebet Too
- **Year:** 2021 | **DOI:** 10.1016/j.dib.2021.107142
- **Paper URL:** [https://pmc.ncbi.nlm.nih.gov/articles/PMC8165403/](https://pmc.ncbi.nlm.nih.gov/articles/PMC8165403/)
- **Citation:** Jennifer Jepkoech, David Muchangi Mugo, Benson K Kenduiywo et al. (2021). Arabica coffee leaf images dataset for coffee leaf disease detection and classification.. doi:10.1016/j.dib.2021.107142
- **Match Classification:** `closely_related` (Reason: offline operation not stated in the text)
- **Problem Addressed:** coffee leaf disease detection and classification
- **Research Objective:** introduce Arabica coffee leaf image datasets for training and validation of deep learning models
- **Input / Output:** Input: leaf images (Arabica) | Output: preprocessed images
- **Dataset:** Name: JMuBEN and JMuBEN2 | Description: The dataset contains 58,555 leaf images spread across five classes with annotations of disease names. | Size: 58,555 | Source: not found
- **Model & Architecture:** Model: not applicable | Architecture: not applicable | Backbone: not found | Components: not found
- **Methodology:** not applicable
- **Experiments & Results:**
  - Setup: not applicable
  - Metrics: not applicable
  - Results: not applicable
  - Baselines: not applicable
  - Evidence Location: `arabica coffee leaf images dataset for coffee leaf disease detection and classification, jennifer jepkoech, david muchangi mugo, benson k kenduiywo, edna chebet too`
- **Limitations (Author-Stated):** not found
- **Research Gap (Evidenced):** not found
- **Code Repository:** [not found](not found) (Official: not found, Framework: not found)
- **Key Verified Evidence:**
  > [abstract] "The Arabica datasets contain images that facilitates training and validation during the utilization of deep learning algorithms for coffee plant leaf disease recognition and classification."
  > [abstract] "The Arabica datasets contain images that facilitates training and validation during the utilization of deep learning algorithms for coffee plant leaf disease recognition and classification."
  > [abstract] "Keywords: Arabica coffee, Image datasets, Machine learning, Deep learning, Disease diagnosis"
  > [method] "Each image from the dataset was then checked to find out if they were of the same squared shape."
  > [method] "in the pre-processing phase, elimination of image misrepresentations and noises [\[1\]](https://pmc.ncbi.nlm.nih.gov/articles/pmc8165403/#bib0001) was done to improve on image quality."
  > [abstract] "This article introduces Arabica coffee leaf datasets known as JMuBEN and JMuBEN2."
  > [dataset] "In total, the dataset contains 58,555 leaf images spread across five classes (Phoma, Cescospora and Rust Healthy, Miner,) with annotations regarding the state of the leaves and the disease names."
  > [dataset] "In total, the dataset contains 58,555 leaf images spread across five classes (Phoma, Cescospora and Rust Healthy, Miner,) with annotations regarding the state of the leaves and the disease names."
  > [method] "in the pre-processing phase, elimination of image misrepresentations and noises [\[1\]](https://pmc.ncbi.nlm.nih.gov/articles/pmc8165403/#bib0001) was done to improve on image quality."
- **Traceable Source URLs:** [https://pmc.ncbi.nlm.nih.gov/articles/PMC8165403/](https://pmc.ncbi.nlm.nih.gov/articles/PMC8165403/)

### 5. Artificial intelligence for detection and quantification of rust and leaf miner in coffee crop [CLOSELY RELATED]
- **Authors:** Alvaro Leandro Cavalcante Carneiro, Lucas de Brito Silva, Marisa Silveira Almeida Renaud Faulin
- **Year:** 2021 | **DOI:** not found
- **Paper URL:** [https://arxiv.org/abs/2103.11241](https://arxiv.org/abs/2103.11241)
- **Citation:** Alvaro Leandro Cavalcante Carneiro, Lucas de Brito Silva, Marisa Silveira Almeida Renaud Faulin (2021). Artificial intelligence for detection and quantification of rust and leaf miner in coffee crop. cs.CV, cs.AI, cs.LG.
- **Match Classification:** `closely_related` (Reason: offline operation not stated in the text (found: "using a mobile application as a high-level interface for the model inferences"))
- **Problem Addressed:** Pest and disease control in agriculture
- **Research Objective:** Create algorithm to detect rust and leaf miner in coffee leaves and quantify disease severity via mobile app
- **Input / Output:** Input: RGB leaf images captured by smartphone | Output: not found
- **Dataset:** Name: Created coffee rust and leaf miner dataset | Description: Leaves with rust and leaf miner were collected from a farmer in Brazil and photographed in a lab with a smartphone | Size: 285 rust samples and 257 leaf miner samples | Source: not found
- **Model & Architecture:** Model: Single-Shot Detector (SSD) | Architecture: Base network CNN architecture for SSD | Backbone: not found | Components: not found
- **Methodology:** Use SSD object detector with computationally efficient design and low memory usage
- **Experiments & Results:**
  - Setup: not found
  - Metrics: not found
  - Results: not found
  - Baselines: not found
  - Evidence Location: `artificial intelligence for detection and quantification of rust and leaf miner in coffee crop, abstract, 1. introduction, 2.1 convolutional neural network architectures, 2.2 dataset creation`
- **Limitations (Author-Stated):** not found
- **Research Gap (Evidenced):** not found
- **Code Repository:** [not found](not found) (Official: not found, Framework: not found)
- **Key Verified Evidence:**
  > [abstract] "Pest and disease control plays a key role in agriculture since the damage caused by these agents are responsible for a huge economic loss every year."
  > [abstract] "we create an algorithm capable of detecting rust *(Hemileia vastatrix)* and leaf miner *(Leucoptera coffeella)* in coffee leaves *(Coffea arabica)* and quantify disease severity using a mobile application"
  > [abstract] "Deep learning; Object detection; Convolutional neural networks; Artificial intelligence; Plant disease identification."
  > [2.2 dataset creation] "photos were captured in a laboratory in a white background using a smartphone camera in the RGB color system"
  > [2.2 dataset creation] "The created dataset [13] has 285 and 257 samples of rust and leaf miner, respectively."
  > [2.2 dataset creation] "We randomly collected the leaves with rust and leaf miner at a farmer located in Brazil and the photos were captured in a laboratory in a white background using a smartphone camera"
  > [2.2 dataset creation] "The created dataset [13] has 285 and 257 samples of rust and leaf miner, respectively."
  > [2.1 convolutional neural network architectures] "The Single-Shot Detector (SSD) is a method for object detection"
  > [2.1 convolutional neural network architectures] "An essential part of the SSD training process is the base network, which is a CNN architecture that makes up the first layers of the SSD."
  > [2.1 convolutional neural network architectures] "The Single-Shot Detector (SSD) is a method for object detection proposed by Liu et al. [5] and used in this work, which highlights its computational efficiency with low memory usage and processing time"
  > [abstract] "detecting rust *(Hemileia vastatrix)* and leaf miner *(Leucoptera coffeella)* in coffee leaves"
  > [abstract] "using a mobile application as a high-level interface for the model inferences"
- **Traceable Source URLs:** [https://arxiv.org/abs/2103.11241](https://arxiv.org/abs/2103.11241)

### 6. GreenAid: a confidence-weighted ensemble deep learning system for real-time plant disease detection and management. [CLOSELY RELATED]
- **Authors:** Fatma M Talaat, Mohammed Tawfik, Warda M Shaban
- **Year:** 2026 | **DOI:** 10.1038/s41598-026-57979-0
- **Paper URL:** [https://pmc.ncbi.nlm.nih.gov/articles/PMC13284324/](https://pmc.ncbi.nlm.nih.gov/articles/PMC13284324/)
- **Citation:** Fatma M Talaat, Mohammed Tawfik, Warda M Shaban (2026). GreenAid: a confidence-weighted ensemble deep learning system for real-time plant disease detection and management.. Deep Learning, Plant Diseases, Convolutional Neural Networks, Mobile Applications, Agriculture, Dashboard Systems. doi:10.1038/s41598-026-57979-0
- **Match Classification:** `closely_related` (Reason: not found)
- **Problem Addressed:** not read - search snippet only
- **Research Objective:** not read - search snippet only
- **Input / Output:** Input: not read - search snippet only | Output: not read - search snippet only
- **Dataset:** Name: not read - search snippet only | Description: not found | Size: not read - search snippet only | Source: not read - search snippet only
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

### 7. LeafLiteX mobile application for leaf disease detection using U-Net segmentation and lightweight deep learning. [CLOSELY RELATED]
- **Authors:** Pawan Kumar Verma, Divya Midhun, Hemalatha, Rahul Gupta, Saurabh Singhal, Nitin Rakesh
- **Year:** 2026 | **DOI:** 10.1038/s41598-026-60625-4
- **Paper URL:** [https://pubmed.ncbi.nlm.nih.gov/42420345/](https://pubmed.ncbi.nlm.nih.gov/42420345/)
- **Citation:** Pawan Kumar Verma, Divya Midhun, Hemalatha et al. (2026). LeafLiteX mobile application for leaf disease detection using U-Net segmentation and lightweight deep learning.. doi:10.1038/s41598-026-60625-4
- **Match Classification:** `closely_related` (Reason: not found)
- **Problem Addressed:** not read - search snippet only
- **Research Objective:** not read - search snippet only
- **Input / Output:** Input: not read - search snippet only | Output: not read - search snippet only
- **Dataset:** Name: not read - search snippet only | Description: not found | Size: not read - search snippet only | Source: not read - search snippet only
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

### 8. Coffee Leaf Rust Disease Detection and Implementation of an Edge Device for Pruning Infected Leaves via Deep Learning Algorithms. [CLOSELY RELATED]
- **Authors:** Raka Thoriq Araaf, Arkar Minn, Tofael Ahamed
- **Year:** 2024 | **DOI:** 10.3390/s24248018
- **Paper URL:** [https://pmc.ncbi.nlm.nih.gov/articles/PMC11679138/](https://pmc.ncbi.nlm.nih.gov/articles/PMC11679138/)
- **Citation:** Raka Thoriq Araaf, Arkar Minn, Tofael Ahamed (2024). Coffee Leaf Rust Disease Detection and Implementation of an Edge Device for Pruning Infected Leaves via Deep Learning Algorithms.. Deep Learning, Plant Diseases, Plant Leaves, Algorithms, Coffea, Coffee, Indonesia, Basidiomycota, Neural Networks, Computer. doi:10.3390/s24248018
- **Match Classification:** `closely_related` (Reason: not found)
- **Problem Addressed:** not read - search snippet only
- **Research Objective:** not read - search snippet only
- **Input / Output:** Input: not read - search snippet only | Output: not read - search snippet only
- **Dataset:** Name: not read - search snippet only | Description: not found | Size: not read - search snippet only | Source: not read - search snippet only
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
- **Traceable Source URLs:** [https://pmc.ncbi.nlm.nih.gov/articles/PMC11679138/](https://pmc.ncbi.nlm.nih.gov/articles/PMC11679138/)

### 9. Multi-Class Plant Leaf Disease Detection: A CNN-based Approach with Mobile App Integration [CLOSELY RELATED]
- **Authors:** Md Aziz Hosen Foysal, Foyez Ahmed, Md Zahurul Haque
- **Year:** 2024 | **DOI:** not found
- **Paper URL:** [https://arxiv.org/abs/2408.15289](https://arxiv.org/abs/2408.15289)
- **Citation:** Md Aziz Hosen Foysal, Foyez Ahmed, Md Zahurul Haque (2024). Multi-Class Plant Leaf Disease Detection: A CNN-based Approach with Mobile App Integration. cs.CY, cs.LG.
- **Match Classification:** `closely_related` (Reason: not found)
- **Problem Addressed:** not read - search snippet only
- **Research Objective:** not read - search snippet only
- **Input / Output:** Input: not read - search snippet only | Output: not read - search snippet only
- **Dataset:** Name: not read - search snippet only | Description: not found | Size: not read - search snippet only | Source: not read - search snippet only
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

### 10. Plant disease detection model for edge computing devices. [CLOSELY RELATED]
- **Authors:** Ameer Tamoor Khan, Signe Marie Jensen, Abdul Rehman Khan, Shuai Li
- **Year:** 2023 | **DOI:** 10.3389/fpls.2023.1308528
- **Paper URL:** [https://pmc.ncbi.nlm.nih.gov/articles/PMC10748432/](https://pmc.ncbi.nlm.nih.gov/articles/PMC10748432/)
- **Citation:** Ameer Tamoor Khan, Signe Marie Jensen, Abdul Rehman Khan et al. (2023). Plant disease detection model for edge computing devices.. doi:10.3389/fpls.2023.1308528
- **Match Classification:** `closely_related` (Reason: not found)
- **Problem Addressed:** not read - search snippet only
- **Research Objective:** not read - search snippet only
- **Input / Output:** Input: not read - search snippet only | Output: not read - search snippet only
- **Dataset:** Name: not read - search snippet only | Description: not found | Size: not read - search snippet only | Source: not read - search snippet only
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
