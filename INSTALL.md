# Installation Guide

Follow these steps to set up and run the OPTIFRESH application on your local machine.

## 📋 Prerequisites

- **Python**: Version 3.9 or higher is recommended.
- **Hardware**: A GPU is recommended for faster deep-learning inference, but not required (defaults to CPU).
- **OS**: Windows, macOS, or Linux.

## 🚀 Setup Steps

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/optifresh.git
cd optifresh
```

### 2. Create a Virtual Environment (Recommended)
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Application
```bash
streamlit run app.py
```

## ⚙️ Configuration

The application uses a `config.toml` file in the `.streamlit` directory for styling and performance tuning. You can modify this to change the primary theme colors or server settings.

## 🔍 Troubleshooting

- **Large Model Downloads**: On the first run, the application will download several AI models (OpenAI CLIP, ViT, YOLOv8). This might take a few minutes depending on your internet speed.
- **Memory Issues**: If running on low-RAM machines, ensure you have sufficient swap space enabled.

---
*For issues or contributions, please open an issue in the repository.*
