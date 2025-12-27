"""
VisionEngine: Food Item Identification & AI Semantic Analysis
Author: [USER]
Part of the OPTIFRESH food safety suite.
"""

from transformers import AutoImageProcessor, AutoModelForImageClassification, CLIPProcessor, CLIPModel, BlipProcessor, BlipForConditionalGeneration
import torch
from PIL import Image
import numpy as np
import cv2
import random

class VisionEngine:
    def __init__(self, model_name="nateraw/food"):
        self.model_name = model_name
        self.processor = None
        self.model = None
        self.clip_model = None
        self.clip_processor = None
        self.blip_processor = None
        self.blip_model = None
        
        self.item_categories = {
            "Fruit": ["apple", "banana", "orange", "strawberry", "grape", "mango", "pomegranate", "guava", "papaya", "watermelon", "tomato"],
            "Vegetable": ["potato", "onion", "carrot", "broccoli", "spinach", "cucumber", "okra", "bhindi", "eggplant", "baingan", "cauliflower", "gobi"],
            "Packaged Food": ["bread", "cheese", "paneer", "milk", "yogurt", "dahi", "egg", "meat", "chicken", "dal", "pasta", "rice"]
        }

    def _load_classifier(self):
        if self.model is None:
            try:
                self.processor = AutoImageProcessor.from_pretrained(self.model_name)
                self.model = AutoModelForImageClassification.from_pretrained(self.model_name)
            except:
                fallback = "google/vit-base-patch16-224"
                self.processor = AutoImageProcessor.from_pretrained(fallback)
                self.model = AutoModelForImageClassification.from_pretrained(fallback)

    def _load_blip(self):
        if self.blip_model is None:
            self.blip_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
            self.blip_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

    def _load_clip(self):
        if self.clip_model is None:
            self.clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
            self.clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

    def identify_item(self, image):
        self._load_classifier()
        self._load_blip()

        if isinstance(image, np.ndarray):
            image = Image.fromarray(image)
        
        # Ensure RGB (Removes alpha channel for PNGs)
        if image.mode != "RGB":
            image = image.convert("RGB")
        
        # Classifier Pass
        inputs = self.processor(images=image, return_tensors="pt")
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
        
        predicted_class_idx = logits.argmax(-1).item()
        raw_label = self.model.config.id2label[predicted_class_idx].replace("_", " ").title()
        confidence = torch.nn.functional.softmax(logits, dim=-1)[0, predicted_class_idx].item()
        
        # BLIP Pass (Understandability Layer)
        blip_inputs = self.blip_processor(image, return_tensors="pt")
        with torch.no_grad():
            out = self.blip_model.generate(**blip_inputs)
            description = self.blip_processor.decode(out[0], skip_special_tokens=True)
        
        # Category Mapping
        category = "Other"
        label_lower = raw_label.lower()
        for cat, items in self.item_categories.items():
            if any(item in label_lower for item in items):
                category = cat
                break
            
        return {
            "raw_name": raw_label,
            "understandable_name": description.title(),
            "category": category,
            "confidence": confidence
        }

    def get_ai_state_analysis(self, image):
        self._load_clip()
        if isinstance(image, np.ndarray):
            image = Image.fromarray(image)
        if image.mode != "RGB":
            image = image.convert("RGB")
            
        # Expanded labels for scientific precision
        labels = [
            "perfectly fresh fruit skin", "microscopic fungal mold", "early biological decay", 
            "natural seeds", "studio background", "pristine surface texture", 
            "bruised skin", "spoiled mushy patches", "blue-green penicillium mold",
            "white fuzzy mycelium", "bacterial soft rot", "healthy epidermis",
            "paper document", "resume text", "screenshot"
        ]
        
        # DEEP CHECK
        # Instead of one pass, we take 5 strategic crops to find tiny defects
        # 1. Center Crop
        # 2. Top-Left
        # 3. Top-Right
        # 4. Bottom-Left
        # 5. Bottom-Right
        
        w, h = image.size
        crop_size = min(w, h) // 2
        crops = [
            image, # Full view
            image.crop((0, 0, crop_size, crop_size)), # TL
            image.crop((w-crop_size, 0, w, crop_size)), # TR
            image.crop((0, h-crop_size, crop_size, h)), # BL
            image.crop((w-crop_size, h-crop_size, w, h)), # BR
            image.crop((w//4, h//4, 3*w//4, 3*h//4)) # CENTER
        ]
        
        aggregated_probs = {label: 0 for label in labels}
        
        for crop in crops:
            inputs = self.clip_processor(text=labels, images=crop, return_tensors="pt", padding=True)
            with torch.no_grad():
                outputs = self.clip_model(**inputs)
                probs = outputs.logits_per_image.softmax(dim=1)
                
            for i in range(len(labels)):
                # SAFETY-FIRST: Take the MAX probability found across all crops for hazard labels
                # and MEAN for the rest.
                val = probs[0, i].item()
                if "mold" in labels[i] or "decay" in labels[i] or "rot" in labels[i] or "bruised" in labels[i]:
                    aggregated_probs[labels[i]] = max(aggregated_probs[labels[i]], val)
                else:
                    aggregated_probs[labels[i]] += val / len(crops)
            
        top_state = max(aggregated_probs, key=aggregated_probs.get)
        
        # Veto Logic
        non_food_tokens = ["paper", "resume", "screenshot"]
        if any(token in top_state for token in non_food_tokens):
            return "NON_BIOLOGICAL", aggregated_probs
            
        return top_state, aggregated_probs

    def generate_scan_overlay(self, image_bgr, item_info, verdict_data):
        """
        Generates a simple, human-friendly scan view.
        """
        hud = image_bgr.copy()
        h, w = hud.shape[:2]
        
        # Simple colors
        color_main = (255, 255, 0) # Cyan
        if "DISCARD" in str(verdict_data.get('verdict', '')):
            color_main = (0, 0, 255) # Red
            
        # 1. Simple Brackets
        center_x, center_y = w // 2, h // 2
        gap = min(w, h) // 3
        blen = gap // 3
        
        # Draw 4 corners
        cv2.line(hud, (center_x-gap, center_y-gap), (center_x-gap+blen, center_y-gap), color_main, 2)
        cv2.line(hud, (center_x-gap, center_y-gap), (center_x-gap, center_y-gap+blen), color_main, 2)
        cv2.line(hud, (center_x+gap, center_y-gap), (center_x+gap-blen, center_y-gap), color_main, 2)
        cv2.line(hud, (center_x+gap, center_y-gap), (center_x+gap, center_y-gap+blen), color_main, 2)
        cv2.line(hud, (center_x-gap, center_y+gap), (center_x-gap+blen, center_y+gap), color_main, 2)
        cv2.line(hud, (center_x-gap, center_y+gap), (center_x-gap, center_y+gap-blen), color_main, 2)
        cv2.line(hud, (center_x+gap, center_y+gap), (center_x+gap-blen, center_y+gap), color_main, 2)
        cv2.line(hud, (center_x+gap, center_y+gap), (center_x+gap, center_y+gap-blen), color_main, 2)
        
        # 2. Simple Label
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(hud, f"Item: {item_info['understandable_name']}", (20, 40), font, 0.7, color_main, 2)
        cv2.putText(hud, f"Status: {verdict_data.get('verdict', 'Checking')}", (20, 75), font, 0.8, color_main, 2)
        
        if "DISCARD" in str(verdict_data.get('verdict', '')):
             cv2.putText(hud, "!! ISSUE !!", (center_x-100, center_y+gap+40), font, 0.7, (0,0,255), 2)
             
        return hud
