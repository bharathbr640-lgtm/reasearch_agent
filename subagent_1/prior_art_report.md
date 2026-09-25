# Prior-Art Discovery Report (Subagent 1)
**Generated on:** 2026-09-18 16:16:27
**Model Engine:** `gpt-oss:120b` via Ollama Cloud

## Confirmed Problem Statement
> Select an algorithmic strategy (e.g., CNN/U‑Net, transformer, physics‑informed unmixing, or hybrid) to recover the 10 m sub‑pixel layout from a 30 m pixel and design mechanisms (custom loss, constraint layers, post‑processing projection, consistency regularization) that guarantee the 3 × 3 sub‑pixel predictions, when averaged, exactly reproduce the original 30 m pixel’s class composition.

## Discovery Summary
- **Status:** Prior art detected
- **Total Candidates Analyzed:** 9
- **Closest Match:** Several recent works combine spectral unmixing with deep‑learning‑based super‑resolution (CNN/U‑Net, transformer hybrids) and introduce constraint‑oriented losses to preserve class proportions. The most directly relevant are hybrid frameworks that explicitly enforce composition consistency via hard constraints or projection layers, though none demonstrate a strict equality guarantee for a 3 × 3 upsampling from 30 m to 10 m.

## Search Queries Executed
- `recover 10m sub-pixel layout from 30m satellite pixel using deep learning`
- `CNN U-Net transformer hybrid spectral unmixing upsampling for sub-pixel classification`
- `subpixel classification tool with constraint layers and custom loss for composition consistency`
- `open source implementation of physics-informed unmixing network for sub-pixel resolution`

## Candidate Prior Art
| Name | Source | Closeness | Status | Verified (Playwright) | Link |
|---|---|---|---|---|---|
| A Hybrid Framework for Sub-Pixel Target Detection Using Spectral Unmixing, Super-Resolution, and Deep Learning in Satellite Imagery | paper | `close_variant` | unknown | No | [View](https://www.kjrs.org/journal/view.html?doi=10.7780/kjrs.2025.41.5.14) |
| Hard-Constrained Hopfield Neural Network for Subpixel Mapping | paper | `close_variant` | unknown | No | [View](https://doi.org/10.1109/tgrs.2024.3462430) |
| Dual-Branch Subpixel-Guided Network for Hyperspectral Image Classification | paper | `close_variant` | unknown | No | [View](https://arxiv.org/html/2412.03893v1) |
| Explicable Sub-Pixel Mapping Based on Nested Self-Attention Network with Spatial Correlation Learnable Mechanism | paper | `close_variant` | unknown | No | [View](https://doi.org/10.1109/igarss53475.2024.10642623) |
| HyFormer: Hybrid Transformer and CNN for Pixel-Level Multispectral Classification | paper | `partial_overlap` | unknown | No | [View](https://pmc.ncbi.nlm.nih.gov/articles/PMC9967485/) |
| Cross-range self-attention single hyperspectral image super‑resolution (uHNTC) | paper | `partial_overlap` | unknown | No | [View](https://www.nature.com/articles/s41598-025-27810-3) |
| Deformable Transformer and Spectral U‑Net for Large‑Scale Remote Sensing Semantic Segmentation | paper | `partial_overlap` | unknown | No | [View](https://ieeexplore.ieee.org/iel8/4609443/4609444/10729869.pdf) |
| Integration of coarser images in subpixel mapping | paper | `tangential` | unknown | No | [View](https://link.springer.com/article/10.1007/s44212-025-00075-x) |
| Techniques for deep learning with satellite & aerial imagery | github | `tangential` | active | ✓ Yes | [View](https://github.com/satellite-image-deep-learning/techniques) |

### Detailed Notes on Candidates
#### A Hybrid Framework for Sub-Pixel Target Detection Using Spectral Unmixing, Super-Resolution, and Deep Learning in Satellite Imagery (paper)
- **URL:** https://www.kjrs.org/journal/view.html?doi=10.7780/kjrs.2025.41.5.14
- **Closeness:** `close_variant`
- **Notes:** Combines spectral unmixing, CNN‑based super‑resolution, and a custom loss that penalizes deviation from the original pixel composition. Does not enforce exact equality but is the closest published hybrid approach.

#### Hard-Constrained Hopfield Neural Network for Subpixel Mapping (paper)
- **URL:** https://doi.org/10.1109/tgrs.2024.3462430
- **Closeness:** `close_variant`
- **Notes:** Introduces a Hopfield network with hard constraints that force the sum of sub‑pixel class probabilities to match the coarse‑pixel label exactly. Focuses on binary/ternary classes; extension to 3 × 3 multi‑class layout would require adaptation.

#### Dual-Branch Subpixel-Guided Network for Hyperspectral Image Classification (paper)
- **URL:** https://arxiv.org/html/2412.03893v1
- **Closeness:** `close_variant`
- **Notes:** Two‑branch architecture: one branch learns spectral unmixing, the other learns spatial upsampling. Uses a composition‑preserving loss but only approximates the average constraint.

#### Explicable Sub-Pixel Mapping Based on Nested Self-Attention Network with Spatial Correlation Learnable Mechanism (paper)
- **URL:** https://doi.org/10.1109/igarss53475.2024.10642623
- **Closeness:** `close_variant`
- **Notes:** Self‑attention network that explicitly models spatial correlation for sub‑pixel mapping; includes a regularizer encouraging the summed sub‑pixel probabilities to equal the coarse pixel distribution.

#### HyFormer: Hybrid Transformer and CNN for Pixel-Level Multispectral Classification (paper)
- **URL:** https://pmc.ncbi.nlm.nih.gov/articles/PMC9967485/
- **Closeness:** `partial_overlap`
- **Notes:** Hybrid CNN‑Transformer for pixel‑wise classification; does not address sub‑pixel upsampling or composition constraints.

#### Cross-range self-attention single hyperspectral image super‑resolution (uHNTC) (paper)
- **URL:** https://www.nature.com/articles/s41598-025-27810-3
- **Closeness:** `partial_overlap`
- **Notes:** Hybrid Transformer‑CNN for hyperspectral super‑resolution; includes a reconstruction loss but no explicit class‑composition enforcement.

#### Deformable Transformer and Spectral U‑Net for Large‑Scale Remote Sensing Semantic Segmentation (paper)
- **URL:** https://ieeexplore.ieee.org/iel8/4609443/4609444/10729869.pdf
- **Closeness:** `partial_overlap`
- **Notes:** Focuses on semantic segmentation with transformer‑U‑Net; does not target sub‑pixel layout or composition constraints.

#### Integration of coarser images in subpixel mapping (paper)
- **URL:** https://link.springer.com/article/10.1007/s44212-025-00075-x
- **Closeness:** `tangential`
- **Notes:** Conceptual discussion of using coarse imagery to inform sub‑pixel mapping; no concrete algorithm or loss formulation.

#### Techniques for deep learning with satellite & aerial imagery (github)
- **URL:** https://github.com/satellite-image-deep-learning/techniques
- **Closeness:** `tangential`
- **Notes:** Curated list of resources; does not contain an implementation directly addressing the 30 m→10 m composition‑exact problem.

## Innovation Gaps & Opportunities (Handoff to Subagent 2)
Existing works either approximate the composition constraint with soft losses or focus on binary/ternary classes. None provide a proven mechanism that guarantees the exact equality of the averaged 3 × 3 sub‑pixel class probabilities to the original 30 m pixel distribution for multi‑class land‑cover at 10 m resolution. A novel component—such as a differentiable projection layer or a Lagrangian multiplier‑based hard constraint integrated into a CNN/U‑Net or transformer backbone—remains unaddressed, as does a benchmark on the specific 30 m→10 m (3× upsampling) scenario with quantitative verification of zero composition error.

## Domain Keywords for Literature Search
`sub‑pixel mapping`, `super‑resolution`, `spectral unmixing`, `CNN`, `U‑Net`, `transformer`, `constraint loss`, `hard constraint layer`, `composition consistency`, `remote sensing`, `hyperspectral`, `physics‑informed neural network`
