# Contributing to OPTIFRESH

![OptiFresh Demo](assets/optifresh_demo.png)

## Why this project exists

Food waste is a massive global problem, and food‑borne illnesses cost lives every year. **OPTIFRESH** was created to bring laboratory‑grade, AI‑driven food safety analysis into every kitchen. By combining computer‑vision, 3D holographic scanning, and stochastic decay modeling, the project gives users **scientific certainty** about the freshness and safety of their food, helping to reduce waste and prevent health risks.

## What makes OPTIFRESH different

- **Multi‑model AI consensus** – Vision Transformers, CLIP, and a dedicated pathogen‑detection model work together, providing a safety‑first veto that prioritises health over false‑positive freshness scores.
- **3D structural health mapping** – Unlike typical 2D image analysis, OPTIFRESH builds a depth‑aware mesh of the item, evaluating skin turgor, internal texture, and structural integrity.
- **Environmental awareness** – Real‑time weather (temperature & humidity) is fused into the decay forecast, giving context‑aware predictions.
- **Glass‑morphism UI** – A premium, dark‑mode Streamlit interface with subtle animations makes the experience feel modern and trustworthy.
- **Offline‑first design** – All models run locally; no cloud calls are required, preserving privacy and ensuring the app works without internet connectivity.

## How to contribute

1. **Fork the repository** and clone your fork.
2. **Create a virtual environment** and install dependencies:
   ```bash
   python -m venv .venv && .venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. **Run the app** to ensure everything works:
   ```bash
   streamlit run app.py
   ```
4. **Make your changes** – follow the existing code style (PEP‑8, type hints, docstrings).
5. **Add tests** for new functionality in the `tests/` directory.
6. **Submit a pull request** with a clear description of the change and any relevant screenshots or performance metrics.

## Code of Conduct

We expect all contributors to be respectful and inclusive. Please read the full [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for details.

## License

By contributing, you agree that your contributions will be licensed under the same MIT license as the project.
