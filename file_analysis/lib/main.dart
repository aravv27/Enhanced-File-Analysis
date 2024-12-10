import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'dart:io';
import 'package:path_provider/path_provider.dart';
import 'package:path/path.dart' as path;
import 'package:open_file/open_file.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

// Data model for categories
class Category {
  String name;
  List<Category> subcategories;
  List<File> files;
  Category? parent;

  Category({
    required this.name,
    List<Category>? subcategories,
    List<File>? files,
    this.parent,
  })  : subcategories = subcategories ?? List.empty(growable: true),
        files = files ?? List.empty(growable: true);

  // Factory constructor to create a Category from a map (backend response)
  factory Category.fromMap(Map<String, dynamic> map) {
    return Category(
      name: map['name'],
      parent: map['parent'] != null ? Category(name: map['parent']) : null,
      // Assuming subcategories are empty or structured in a way that requires parsing.
      subcategories: [],
    );
  }
}


void main() {
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Enhanced File Manager',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        useMaterial3: true,
      ),
      home: FileManagerScreen(),
    );
  }
}

class FileManagerScreen extends StatefulWidget {
  @override
  _FileManagerScreenState createState() => _FileManagerScreenState();
}

// class FileManagerScreen extends StatefulWidget {
//   @override
//   _FileManagerScreenState createState() => _FileManagerScreenState();
// }

// class _FileManagerScreenState extends State<FileManagerScreen> {
//   final String rootPath = "D:/MyFiles/Question Papers";
//   Category rootCategory = Category(name: "Question Papers");
//   Category? selectedCategory;
//   bool isLoading = true;

//   @override
//   void initState() {
//     super.initState();
//     _loadRootFolder();
//   }

//   Future<void> _loadRootFolder() async {
//     Directory rootDir = Directory(rootPath);
//     if (!await rootDir.exists()) {
//       setState(() {
//         isLoading = false;
//       });
//       return;
//     }

//     rootCategory = await _buildCategoryStructure(rootDir);
//     setState(() {
//       selectedCategory = rootCategory;
//       isLoading = false;
//     });
//   }
// Future<Category> _buildCategoryStructure(Directory directory, [Category? parent]) async {
//   List<Category> subcategories = [];
//   List<File> files = [];

//   // Iterate through the contents of the directory
//   await for (var entity in directory.list(recursive: false, followLinks: false)) {
//     if (entity is Directory) {
//       // Recursively process subdirectories
//       Category subcategory = await _buildCategoryStructure(entity);
//       subcategory.parent = parent; // Explicitly set the parent
//       subcategories.add(subcategory);
//     } else if (entity is File) {
//       // Add files to the category
//       files.add(entity);
//     }
//   }

//   return Category(
//     name: path.basename(directory.path),
//     subcategories: subcategories,
//     files: files,
//     parent: parent, // Set the parent for the current directory's category
//   );
// }

class _FileManagerScreenState extends State<FileManagerScreen> {
  Category rootCategory = Category(name: "Question Papers");
  Category? selectedCategory;
  String currentPath = "";
  bool isLoading = false;
  
  @override
  void initState() {
    super.initState();
    _initializeCategories();
    selectedCategory = rootCategory;
  }

  void _initializeCategories() {

    rootCategory.subcategories = [
      Category(
        name: "Sem - 3",
        subcategories: [
          Category(name: "CN", parent: rootCategory),
          Category(name: "DMGT", parent: rootCategory),
          Category(name: "DSA", parent: rootCategory),
          Category(name: "CAO", parent: rootCategory),
          Category(name: "MPMC", parent: rootCategory),

        ],
        parent: rootCategory,
      ),
      Category(
        name: "Sem - 2",
        subcategories: [
          Category(name: "DSD", parent: rootCategory),
          Category(name: "EE", parent: rootCategory),
        ],
        parent: rootCategory,
      ),
      Category(
        name: "Others",
        subcategories: <Category>[
          Category(name: "Others",parent: rootCategory),
        ],
        parent: rootCategory,
      ),
    ];
  }

Future<void> _pickAndCategorizeFiles() async {
  try {
    print("Picking files...");
    setState(() => isLoading = true);

    // Pick files from the device
    FilePickerResult? result = await FilePicker.platform.pickFiles(
      allowMultiple: true,
      withData: true,
    );

    if (result != null && selectedCategory != null) {
      for (var file in result.files) {
        if (file.path != null) {
          File sourceFile = File(file.path!);
          String fileName = path.basename(sourceFile.path);

          Category categoryData = await _uploadFileAndGetCategory(sourceFile);
          print('Category data received: $categoryData');

          
          String mainCategoryName = categoryData.name;
          String subCategoryName = categoryData.subcategories.isNotEmpty? categoryData.subcategories.first.name: 'Unknown';

          Category mainCategory = await _getCategoryFromStructure(mainCategoryName);
          Category subCategory = await _getSubCategoryFromStructure(mainCategory, subCategoryName);
          print("categerory decided");

          
          String categoryPath = await _getCategoryPath(subCategory);
          String destinationPath = path.join(categoryPath, fileName);
          print("path is got $destinationPath");
          
          // Create directory if it doesn't exist
          Directory categoryDir = Directory(categoryPath);
          if (!await categoryDir.exists()) {
            print("creating directory");
            await categoryDir.create(recursive: true);
          }
          
          await sourceFile.copy(destinationPath);
          print("souce file copyed");

          // Optionally delete the original file from the local storage
          await sourceFile.delete();
          print("souce file deleted");

          
          setState(() {
            selectedCategory!.files.add(File(destinationPath));
          });
        }
      }
    }
  } catch (e) {
    _showError('Error picking files: $e');
  } finally {
    setState(() => isLoading = false);
  }
}

Future<Category> _getCategoryFromStructure(String name) async {
  // Check if the category exists
  Category existingCategory = rootCategory.subcategories.firstWhere(
    (category) => category.name == name,
    orElse: () {
      // Create a new category and add it to the root if not found
      Category newCategory = Category(name: name);
      rootCategory.subcategories.add(newCategory);
      return newCategory; // Return the new category
    },
  );
  return existingCategory;
}

Future<Category> _getSubCategoryFromStructure(Category parent, String name) async {
  // Check if the subcategory exists under the parent
  Category existingSubCategory = parent.subcategories.firstWhere(
    (subCategory) => subCategory.name == name,
    orElse: () {
      // Create a new subcategory and add it to the parent
      Category newSubCategory = Category(name: name, parent: parent);
      parent.subcategories.add(newSubCategory);
      return newSubCategory; // Return the new subcategory
    },
  );
  return existingSubCategory;
}

Future<Category> _uploadFileAndGetCategory(File file) async {
  try {
    final uri = Uri.parse('http://127.0.0.1:5000/upload'); // Flask server URL
    final request = http.MultipartRequest('POST', uri);

    print('Sending request to the server...');


    // Add the file to the request
    request.files.add(await http.MultipartFile.fromPath('file', file.path));

    // Send the request and get the response
    final response = await request.send();
    if (response.statusCode == 200) {
      // Parse the response to get the category
      final responseData = await response.stream.bytesToString();
      final Map<String, dynamic> responseJson = json.decode(responseData);

      print('Received response from the server: $responseJson');

      List<Category> subcategories = [];
      if (responseJson['subcategory'] is List) {
        // If subcategories is already a list, parse it
        for (var sub in responseJson['subcategory']) {
          subcategories.add(Category(name: sub, parent: null));
        }
      } else if (responseJson['subcategory'] is String) {
        // If it's a single string, convert it into a single category
        subcategories.add(Category(name: responseJson['subcategory'], parent: null));
      }

      return Category(name: responseJson['main_category']?? 'unknown',
      subcategories: subcategories,
      );
    } else {
      throw Exception('Failed to categorize the file');
    }
  } catch (e) {
    throw Exception('Error uploading file: $e');
  }
}


  Future<String> _getCategoryPath(Category category) async {
  final appDir = "D:/MyFiles";
  List<String> pathParts = [];
  
  // Build the path parts list
  Category? current = category;
  while (current != null) {
    pathParts.insert(0, current.name);
    current = current.parent;
  }
  
  // Join paths manually
  String finalPath = appDir;
  for (String part in pathParts) {
    finalPath = path.join(finalPath, part);
  }
  
  return finalPath;
}

  Future<void> _deleteFile(File file, Category category) async {
    try {
      bool confirm = await showDialog(
        context: context,
        builder: (context) => AlertDialog(
          title: Text('Delete File'),
          content: Text('Are you sure you want to delete ${path.basename(file.path)}?'),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: Text('Cancel'),
            ),
            TextButton(
              onPressed: () => Navigator.pop(context, true),
              child: Text('Delete'),
              style: TextButton.styleFrom(foregroundColor: Colors.red),
            ),
          ],
        ),
      ) ?? false;

      if (confirm) {
        await file.delete();
        setState(() {
          category.files.remove(file);
        });
      }
    } catch (e) {
      _showError('Error deleting file: $e');
    }
  }

  Future<void> _renameFile(File file, Category category) async {
    String? newName = await showDialog(
      context: context,
      builder: (context) {
        TextEditingController controller = TextEditingController(
          text: path.basename(file.path),
        );
        return AlertDialog(
          title: Text('Rename File'),
          content: TextField(
            controller: controller,
            decoration: InputDecoration(labelText: 'New name'),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: Text('Cancel'),
            ),
            TextButton(
              onPressed: () => Navigator.pop(context, controller.text),
              child: Text('Rename'),
            ),
          ],
        );
      },
    );

    if (newName != null && newName.isNotEmpty) {
      try {
        String newPath = path.join(path.dirname(file.path), newName);
        await file.rename(newPath);
        setState(() {
          int index = category.files.indexOf(file);
          category.files[index] = File(newPath);
        });
      } catch (e) {
        _showError('Error renaming file: $e');
      }
    }
  }

  Future<void> _moveFile(File file, Category sourceCategory) async {
    Category? targetCategory = await showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Move File'),
        content: _buildCategoryPicker(rootCategory),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('Cancel'),
          ),
        ],
      ),
    );

    if (targetCategory != null && targetCategory != sourceCategory) {
      try {
        String newPath = path.join(
          await _getCategoryPath(targetCategory),
          path.basename(file.path),
        );
        
        await Directory(path.dirname(newPath)).create(recursive: true);
        await file.rename(newPath);
        
        setState(() {
          sourceCategory.files.remove(file);
          targetCategory.files.add(File(newPath));
        });
      } catch (e) {
        _showError('Error moving file: $e');
      }
    }
  }

  Widget _buildCategoryPicker(Category category) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        ListTile(
          title: Text(category.name),
          onTap: () => Navigator.pop(context, category),
        ),
        ...category.subcategories.map((subcat) => Padding(
          padding: EdgeInsets.only(left: 20.0),
          child: _buildCategoryPicker(subcat),
        )),
      ],
    );
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.red,
      ),
    );
  }

Future<List<File>> _loadFilesForCategory(Category category) async {
    try {
      String categoryPath = await _getCategoryPath(category);
      Directory categoryDir = Directory(categoryPath);
      print("load files for category func");
      if (await categoryDir.exists()) {
        return categoryDir.listSync().whereType<File>().toList();
      }
      return [];
    } catch (e) {
      _showError('Error loading files: $e');
      return [];
    }
  }

  void _onCategorySelected(Category category) {
    setState(() {
      selectedCategory = category;
    });
  }




Widget _buildFileList(Category category) {
    return FutureBuilder<List<File>>(
      future: _loadFilesForCategory(category),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return Center(child: CircularProgressIndicator());
        } else if (snapshot.hasError) {
          return Center(child: Text('Error loading files: ${snapshot.error}'));
        } else if (!snapshot.hasData || snapshot.data!.isEmpty) {
          return Center(child: Text('No files in this category.'));
        }

        List<File> files = snapshot.data!;
        return ListView.builder(
          itemCount: files.length,
          itemBuilder: (context, index) {
            final file = files[index];
            return Dismissible(
              key: Key(file.path),
              background: Container(
                color: Colors.red,
                alignment: Alignment.centerRight,
                padding: EdgeInsets.only(right: 20.0),
                child: Icon (Icons.delete, color: Colors.white),
              ),
              confirmDismiss: (direction) async {
                return await showDialog(
                  context: context,
                  builder: (context) => AlertDialog(
                    title: Text('Delete File'),
                    content: Text('Are you sure you want to delete ${path.basename(file.path)}?'),
                    actions: [
                      TextButton(
                        onPressed: () => Navigator.pop(context, false),
                        child: Text('Cancel'),
                      ),
                      TextButton(
                        onPressed: () => Navigator.pop(context, true),
                        child: Text('Delete'),
                        style: TextButton.styleFrom(foregroundColor: Colors.red),
                      ),
                    ],
                  ),
                );
              },
              onDismissed: (direction) => _deleteFile(file, category),
              child: ListTile(
                leading: Icon(_getFileIcon(file)),
                title: Text(path.basename(file.path)),
                onTap: () => OpenFile.open(file.path),
                trailing: PopupMenuButton(
                  itemBuilder: (context) => [
                    PopupMenuItem(
                      child: ListTile(
                        leading: Icon(Icons.edit),
                        title: Text('Rename'),
                      ),
                      onTap: () => _renameFile(file, category),
                    ),
                    PopupMenuItem(
                      child: ListTile(
                        leading: Icon(Icons.move_to_inbox),
                        title: Text('Move'),
                      ),
                      onTap: () => _moveFile(file, category),
                    ),
                    PopupMenuItem(
                      child: ListTile(
                        leading: Icon(Icons.delete),
                        title: Text('Delete'),
                      ),
                      onTap: () => _deleteFile(file, category),
                    ),
                  ],
                ),
              ),
            );
          },
        );
      },
    );
  }

  IconData _getFileIcon(File file) {
    String ext = path.extension(file.path).toLowerCase();
    switch (ext) {
      case '.pdf':
        return Icons.picture_as_pdf;
      case '.jpg':
      case '.jpeg':
      case '.png':
        return Icons.image;
      case '.doc':
      case '.docx':
        return Icons.description;
      default:
        return Icons.insert_drive_file;
    }
  }

  Widget _buildCategoryTree(Category category, {double indent = 0}) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        InkWell(
          onTap: () {
            _onCategorySelected(category);
            Navigator.pop(context);
          },
          child: Container(
            padding: EdgeInsets.only(left: indent, top: 8.0, bottom: 8.0),
            child: Row(
              children: [
                Icon(Icons.folder),
                SizedBox(width: 8),
                Text(category.name),
              ],
            ),
          ),
        ),
        ...category.subcategories.map((subcat) =>
          _buildCategoryTree(subcat, indent: indent + 20),
        ),
      ],
    );
  }

  Widget _buildCategoryTiles(Category category) {
  return GridView.builder(
    gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
      crossAxisCount: 3,
      crossAxisSpacing: 8.0,
      mainAxisSpacing: 8.0,
      childAspectRatio: 1.0,
    ),
    itemCount: category.subcategories.length,
    itemBuilder: (context, index) {
      Category subCategory = category.subcategories[index];
      return GestureDetector(
        onTap: () async {
          // Set loading state
          setState(() {
            isLoading = true; // Start loading
          });

          // Load files for the selected subcategory
          List<File> files = await _loadFilesForCategory(subCategory);

          // Update the selected category and its files
          setState(() {
            selectedCategory = subCategory;
            selectedCategory!.files = files;
            isLoading = false;
          });
        },
        child: Container(
          height: 50,
          width: 50,
          child: Align(
            alignment: Alignment.center,
            child: Container(
              height: 300,
              width: 300,
              child: Card(
            elevation: 8,
            shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(8),
          ),
            child: Text(subCategory.name,textAlign: TextAlign.center,),

          ),
          )
          ) 
        ) 
      );
    },
  );
}


  // Method to build file list
 Widget _buildFile(Category category) {
  if (category.files.isEmpty) {
    return Center(child: Text("No files in this category."));
  }
  return ListView.builder(
    itemCount: category.files.length,
    itemBuilder: (context, index) {
      File file = category.files[index];
      return ListTile(
        title: Text(file.path),
        leading: Icon(Icons.insert_drive_file),
      );
    },
  );
}


  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(selectedCategory?.name ?? 'Enhanced File Manager'),
        actions: [
          if (isLoading)
            Padding(
              padding: EdgeInsets.all(8.0),
              child: CircularProgressIndicator(color: Colors.white),
            ),
          if (selectedCategory?.parent != null)
            IconButton(
              icon: Icon(Icons.arrow_back),
              onPressed: () {
                setState(() {
                  selectedCategory = selectedCategory?.parent;
                });
              },
            ),
        ],
      ),
      body: selectedCategory == null
          ? Center(child: Text('Select a category'))
          : Column(
              children: [
                Padding(
                  padding: EdgeInsets.all(8.0),
                  child: Text(
                    'Current Category: ${selectedCategory!.name}',
                    style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                  ),
                ),
                Expanded(
                  child: selectedCategory!.subcategories.isNotEmpty
                      ? _buildCategoryTiles(selectedCategory!)
                      : _buildFile(selectedCategory!),
                ),
              ],
            ),
      floatingActionButton: FloatingActionButton(
        onPressed: _pickAndCategorizeFiles,
        child: Icon(Icons.add),
        tooltip: 'Add Files',
      ),
    );
  }

}
