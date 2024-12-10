## Enhanced File Manager with AI Integration
This project is an enhanced file manager application that allows users to organize and manage files efficiently on their local system. The app is specifically designed to manage question papers, providing a categorized view for easier access and file management.

## Features

## Categorized File Management:
-> The file manager allows users to organize files into categories and subcategories, making it easy to store and retrieve files based on their type or subject.

## AI-Powered File Categorization:
-> Integrated with a pre-trained AI model, the app automatically reads the content of image files (question papers) and assigns them to the appropriate category and subcategory.
-> The AI categorization is done via an API, which ensures that files are correctly categorized based on their content.
Folder and File Structure:
-> Users can navigate through various directories and subdirectories. The file manager reads the folder structure and displays it accordingly.

## File Operations:
-> Files can be moved, renamed, or deleted within the application.
-> A user-friendly interface allows users to manage files effortlessly.

## File Preview:
-> The application provides an option to preview files before opening them, making it easier to decide which file to interact with.

## Technologies Used
Flutter: For building the cross-platform mobile application.
Dart: The programming language used to develop the app.
AI Model: A pre-trained AI model used to analyze and categorize image files, accessed via an API.
File System Operations: Local file management to organize and manage files within categories.

## How It Works
## AI Integration:
-> The AI model processes images (question papers) and determines their category by analyzing their content. This is done by sending the file content to a remote API where the AI model is hosted.
-> Based on the response, the file is categorized into the appropriate folder and subfolder on the local system.
User Interaction:

-> Users can view the categorized folders and files.
Files can be moved to different categories/subcategories, and files can be previewed or opened directly from the app.

# Folder Structure:
The application displays files in a directory-like structure, and users can navigate back and forth between folders and subfolders.
