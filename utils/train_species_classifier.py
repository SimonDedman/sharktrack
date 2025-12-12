"""
Species Classifier Training Script
Train a DenseNet121-based species classifier from labeled shark images
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torchvision import models, transforms
from pathlib import Path
import cv2
import numpy as np
from sklearn.model_selection import train_test_split
from tqdm import tqdm
import click
import json


class SharkDataset(Dataset):
    """Dataset for shark species classification"""

    def __init__(self, image_paths, labels, transform=None):
        self.image_paths = image_paths
        self.labels = labels
        self.transform = transform

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, idx):
        # Load image
        image_path = self.image_paths[idx]
        image = cv2.imread(str(image_path))
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Apply transforms
        if self.transform:
            image = self.transform(image)

        label = self.labels[idx]

        return image, label


def load_training_data(training_dir, class_mapping):
    """
    Load training images and labels from directory.

    Expected structure:
    training_dir/
        ├── class1/
        │   ├── image1.jpg
        │   ├── image2.jpg
        └── class2/
            ├── image1.jpg
            └── image2.jpg

    OR filenames contain class names:
        track_1-G.cirratum.jpg
        track_2-C.perezi.jpg

    Args:
        training_dir: Path to training images
        class_mapping: List of class names

    Returns:
        Tuple of (image_paths, labels, class_to_idx)
    """
    training_dir = Path(training_dir)
    image_paths = []
    labels = []
    class_to_idx = {cls: idx for idx, cls in enumerate(class_mapping)}

    # Try directory-based structure first
    has_subdirs = any(p.is_dir() for p in training_dir.iterdir())

    if has_subdirs:
        # Directory-based structure
        print("Using directory-based class structure")
        for class_name in class_mapping:
            class_dir = training_dir / class_name
            if not class_dir.exists():
                print(f"Warning: No directory found for class '{class_name}'")
                continue

            class_idx = class_to_idx[class_name]
            for img_path in class_dir.glob('*.jpg'):
                image_paths.append(img_path)
                labels.append(class_idx)
            for img_path in class_dir.glob('*.png'):
                image_paths.append(img_path)
                labels.append(class_idx)

    else:
        # Filename-based structure (like SharkTrack output)
        print("Using filename-based class detection")
        for img_path in training_dir.glob('*.jpg'):
            # Try to find class name in filename
            filename = img_path.stem
            found_class = None

            for class_name in class_mapping:
                if class_name in filename or class_name.replace('.', '') in filename:
                    found_class = class_name
                    break

            if found_class:
                image_paths.append(img_path)
                labels.append(class_to_idx[found_class])
            else:
                print(f"Warning: Could not determine class for {filename}")

    print(f"Loaded {len(image_paths)} images across {len(set(labels))} classes")

    return image_paths, labels, class_to_idx


def train_classifier(training_dir, class_mapping, output_dir,
                     epochs=25, batch_size=16, learning_rate=0.001,
                     validation_split=0.2):
    """
    Train species classifier

    Args:
        training_dir: Directory containing training images
        class_mapping: List of class names (e.g., ['G.cirratum', 'C.perezi', 'C.acronotus'])
        output_dir: Where to save trained model
        epochs: Number of training epochs
        batch_size: Training batch size
        learning_rate: Learning rate for optimizer
        validation_split: Fraction of data for validation
    """

    # Setup device
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Training on device: {device}")

    # Load training data
    print("\n📂 Loading training data...")
    image_paths, labels, class_to_idx = load_training_data(training_dir, class_mapping)

    if len(image_paths) == 0:
        raise ValueError("No training images found!")

    # Print class distribution
    print("\n📊 Class distribution:")
    for class_name, class_idx in class_to_idx.items():
        count = labels.count(class_idx)
        print(f"  {class_name}: {count} images")

    # Split train/validation
    train_paths, val_paths, train_labels, val_labels = train_test_split(
        image_paths, labels, test_size=validation_split, stratify=labels, random_state=42
    )

    print(f"\n✂️  Split: {len(train_paths)} training, {len(val_paths)} validation")

    # Data transforms
    average_patch_size = (200, 400)

    train_transform = transforms.Compose([
        transforms.ToPILImage(),
        transforms.Resize(average_patch_size),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(10),
        transforms.ColorJitter(brightness=0.2, contrast=0.2),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])

    val_transform = transforms.Compose([
        transforms.ToPILImage(),
        transforms.Resize(average_patch_size),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])

    # Create datasets
    train_dataset = SharkDataset(train_paths, train_labels, train_transform)
    val_dataset = SharkDataset(val_paths, val_labels, val_transform)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=4)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=4)

    # Build model
    print(f"\n🧠 Building DenseNet121 model for {len(class_mapping)} classes...")
    model = models.densenet121(weights=models.DenseNet121_Weights.IMAGENET1K_V1)

    # Replace classifier
    num_ftrs = model.classifier.in_features
    model.classifier = nn.Linear(num_ftrs, len(class_mapping))

    model = model.to(device)

    # Loss and optimizer
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=7, gamma=0.1)

    # Training loop
    print(f"\n🚀 Starting training for {epochs} epochs...")
    best_val_acc = 0.0
    training_history = []

    for epoch in range(epochs):
        print(f"\n{'='*60}")
        print(f"Epoch {epoch+1}/{epochs}")
        print('='*60)

        # Training phase
        model.train()
        running_loss = 0.0
        running_corrects = 0

        train_bar = tqdm(train_loader, desc='Training')
        for inputs, labels_batch in train_bar:
            inputs = inputs.to(device)
            labels_batch = labels_batch.to(device)

            # Zero gradients
            optimizer.zero_grad()

            # Forward
            outputs = model(inputs)
            _, preds = torch.max(outputs, 1)
            loss = criterion(outputs, labels_batch)

            # Backward
            loss.backward()
            optimizer.step()

            # Statistics
            running_loss += loss.item() * inputs.size(0)
            running_corrects += torch.sum(preds == labels_batch.data)

            train_bar.set_postfix({'loss': loss.item()})

        epoch_loss = running_loss / len(train_dataset)
        epoch_acc = running_corrects.double() / len(train_dataset)

        print(f"  Training Loss: {epoch_loss:.4f}, Accuracy: {epoch_acc:.4f}")

        # Validation phase
        model.eval()
        val_running_loss = 0.0
        val_running_corrects = 0

        with torch.no_grad():
            val_bar = tqdm(val_loader, desc='Validation')
            for inputs, labels_batch in val_bar:
                inputs = inputs.to(device)
                labels_batch = labels_batch.to(device)

                outputs = model(inputs)
                _, preds = torch.max(outputs, 1)
                loss = criterion(outputs, labels_batch)

                val_running_loss += loss.item() * inputs.size(0)
                val_running_corrects += torch.sum(preds == labels_batch.data)

        val_loss = val_running_loss / len(val_dataset)
        val_acc = val_running_corrects.double() / len(val_dataset)

        print(f"  Validation Loss: {val_loss:.4f}, Accuracy: {val_acc:.4f}")

        # Learning rate scheduling
        scheduler.step()

        # Save best model
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            print(f"  ✅ New best validation accuracy: {best_val_acc:.4f}")

        # Save history
        training_history.append({
            'epoch': epoch + 1,
            'train_loss': float(epoch_loss),
            'train_acc': float(epoch_acc),
            'val_loss': float(val_loss),
            'val_acc': float(val_acc)
        })

    # Save final model
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    model_path = output_dir / 'classifier.pt'
    torch.save(model.state_dict(), model_path)
    print(f"\n💾 Saved model to {model_path}")

    # Save class mapping
    class_mapping_path = output_dir / 'class_mapping.txt'
    with open(class_mapping_path, 'w') as f:
        f.write(','.join(class_mapping))
    print(f"💾 Saved class mapping to {class_mapping_path}")

    # Save training history
    history_path = output_dir / 'training_history.json'
    with open(history_path, 'w') as f:
        json.dump(training_history, f, indent=2)
    print(f"💾 Saved training history to {history_path}")

    # Save training metadata
    metadata = {
        'num_classes': len(class_mapping),
        'class_mapping': class_mapping,
        'class_to_idx': class_to_idx,
        'num_training_images': len(train_paths),
        'num_validation_images': len(val_paths),
        'epochs': epochs,
        'batch_size': batch_size,
        'learning_rate': learning_rate,
        'best_val_accuracy': float(best_val_acc),
        'device': str(device)
    }

    metadata_path = output_dir / 'metadata.json'
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"💾 Saved metadata to {metadata_path}")

    print(f"\n{'='*60}")
    print(f"✅ Training completed!")
    print(f"   Best validation accuracy: {best_val_acc:.4f}")
    print(f"   Model saved to: {output_dir}")
    print(f"{'='*60}")


@click.command()
@click.option('--training_images', '-i', required=True, help='Path to training images directory')
@click.option('--class_mapping', '-c', required=True, help='Comma-separated list of class names')
@click.option('--output_model', '-o', required=True, help='Output directory for trained model')
@click.option('--epochs', default=25, help='Number of training epochs')
@click.option('--batch_size', default=16, help='Training batch size')
@click.option('--learning_rate', default=0.001, help='Learning rate')
@click.option('--validation_split', default=0.2, help='Validation split fraction')
def main(training_images, class_mapping, output_model, epochs, batch_size, learning_rate, validation_split):
    """Train a species classifier from labeled images"""

    # Parse class mapping
    classes = [c.strip() for c in class_mapping.split(',')]

    print("="*60)
    print("🎓 SharkTrack Species Classifier Training")
    print("="*60)
    print(f"\n📋 Configuration:")
    print(f"   Training images: {training_images}")
    print(f"   Classes: {classes}")
    print(f"   Output model: {output_model}")
    print(f"   Epochs: {epochs}")
    print(f"   Batch size: {batch_size}")
    print(f"   Learning rate: {learning_rate}")
    print(f"   Validation split: {validation_split}")

    train_classifier(
        training_images,
        classes,
        output_model,
        epochs=epochs,
        batch_size=batch_size,
        learning_rate=learning_rate,
        validation_split=validation_split
    )


if __name__ == '__main__':
    main()
