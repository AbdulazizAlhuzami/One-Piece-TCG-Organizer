# One Piece Card Game Collection Tracker

  

A simple, desktop-based application built with Python and PyQt6 to help you manage and track your One Piece Card Game collection. This tool allows you to add, edit, delete, and search for cards, as well as view basic statistics about your collection.

  

**Disclaimer:** This project is provided as-is, and active development by the original author may not be continued. Feel free to use, modify, and distribute it under the terms of the license.

  

## Important Disclaimers

  

### Windows Defender/Antivirus Warning

When you download and run the compiled executable file (e.g., `.exe` on Windows), your operating system's built-in antivirus (like Windows Defender) or other third-party antivirus software **might flag the application as potentially malicious or an unrecognized app**. This is a common occurrence for many Python applications compiled into executables by tools like PyInstaller, especially if they are not signed with a digital certificate from a recognized publisher.

  

**Rest assured:** This application is **not malicious**. It does not contain viruses, malware, or any harmful code. The warning is a generic alert due to the executable being newly created and lacking a well-known publisher signature.

  

**If you encounter this warning:**

* You may see a "Windows protected your PC" or similar message.

* Click on "More info" (or similar option) and then select "Run anyway" if you trust the source (i.e., this repository).

* Alternatively, you can compile the application yourself from the source code, which eliminates the need to trust a pre-built executable.

  

## Features

  

* **Card Management:** Easily add new cards, edit existing entries, and delete cards from your collection.

* **Search & Filter:** Quickly find cards by number, name, crew, color, rarity, and more using a dynamic search bar.

* **Collection Overview:** View your entire collection in a sortable and searchable table.

* **Statistics & Graphs:** Get insights into your collection with charts showing card distribution by rarity, color, and kind.

* **Data Persistence:** Your collection data is automatically saved to and loaded from an Excel file (`one_piece_cards.xlsx`) by default.

* **Export Options:** Export your current collection (including any active filters) to CSV or JSON formats.

* **Duplicate Handling:** Smartly manage duplicate card entries by either adding to an existing card's quantity or adding it as a new, separate entry.

* **User-Friendly Interface:** Built with a clean and intuitive PyQt6 graphical user interface.

  

## Installation

  

If you want the executable file and start using it, you can find it [here](https://github.com/AbdulazizAlhuzami/One-Piece-TCG-Organizer/releases)

  

This application requires Python and several libraries: PyQt6 for the GUI, pandas for data handling, matplotlib for plotting, and openpyxl for Excel file support.

  

1.  **Clone the repository:**

    ```bash

    git clone [https://github.com/AbdulazizAlhuzami/One-Piece-TCG-Organizer](https://github.com/AbdulazizAlhuzami/One-Piece-TCG-Organizer)

    cd one-piece-card-tracker

    ```

  

2.  **Create a virtual environment (highly recommended):**

    ```bash

    python -m venv venv

    ```

    *Activate the virtual environment:*

    * **On Windows:**

        ```bash

        venv\Scripts\activate

        ```

    * **On macOS/Linux:**

        ```bash

        source venv/bin/activate

        ```

  

3.  **Install dependencies:**

    ```bash

    pip install -r requirements.txt

    ```

    If `requirements.txt` is not present, you can install them manually:

    ```bash

    pip install PyQt6 pandas matplotlib openpyxl

    ```

  

## Usage

  

1.  **Run the application:** Ensure your virtual environment is activated, then:

    ```bash

    python main.py

    ```

  

## Compiling the Application into an Executable

  

You can compile this Python application into a standalone executable (`.exe` on Windows, `.app` on macOS, etc.) using `PyInstaller`. This allows users to run the application without needing to install Python or its dependencies.

  

### Prerequisites for Compilation

  

1.  **Python:** Ensure Python is installed on your system.

2.  **Virtual Environment (Recommended):** Set up and activate a virtual environment as described in the Installation section.

3.  **Required Libraries:** Install all necessary Python libraries within your virtual environment:

    ```bash

    pip install PyQt6 pandas matplotlib openpyxl pyinstaller

    ```

    **Note:** `pyinstaller` is the additional tool required for compilation.

  

### Compilation Steps

  

1.  **Navigate to the project directory:**

    Open your terminal or command prompt and change the directory to the root of your project where `main.py` is located.

    ```bash

    cd path/to/your/one-piece-card-tracker

    ```

  

2.  **Run PyInstaller:**

    Use the following command to create a single executable file.

  

    For a single file executable (recommended for ease of distribution):

    ```bash

    pyinstaller --noconfirm --onefile --windowed --icon=icon.ico main.py

    ```

    * `--noconfirm`: Overwrite existing output directory without asking.

    * `--onefile`: Creates a single executable file.

    * `--windowed` or `--noconsole`: Prevents a console window from opening when the GUI app runs. Use `--windowed` for macOS/Windows, `--noconsole` for Linux. For cross-platform, `--windowed` often suffices or you can specify based on OS.

    * `--icon=icon.ico`: **(Optional)** Specifies an icon for the executable. You will need an `icon.ico` file (for Windows) or `icon.icns` (for macOS) in your project root. If you don't have one, PyInstaller will use a default icon.

        * **To add your own logo for the .exe:** Place your `.ico` (Windows) or `.icns` (macOS) file in the same directory as `main.py` and replace `icon.ico` with your actual icon filename (e.g., `--icon=my_app_logo.ico`).

  

3.  **Locate the Executable:**

    After PyInstaller finishes, the executable will be found in the `dist` folder within your project directory.

  

    * **On Windows:** `dist/main.exe` (or whatever your `main.py` file is named, e.g., `dist/OnePieceCardTracker.exe`)

    * **On macOS:** `dist/main` (or `dist/main.app`)

    * **On Linux:** `dist/main`

  

4.  **Testing the Executable:**

    Run the executable from the `dist` folder to ensure it works correctly.

  

## Screenshots

### Home Page

![[TCG-Card-Tracker-Home.jpg]]

### Statistics Page

![[TCG-Card-Tracker-Statistics 1.jpg]]

### Adding/Editing Cards

![[TCG-Card-Tracker-Editing.jpg]]

### Keyboard Shortcuts

![[TCG-Card-Tracker-Shortcuts.jpg]]

## License

  

This project is licensed under the **MIT License**.

This means you are free to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, provided you include the original copyright and permission notice. This license is highly permissive and **allows for both personal and commercial use**.

For the full license details, please refer to the `LICENSE` file in this repository.

  

## Contributing

  

Hey there!👋

  

This app is primarily something I'm building to help manage my mom One Piece card collection. Because of that, my active development might slow down or even stop once it meets my personal needs. **But that doesn't mean your help isn't welcome!** If you have ideas for improvements, find a bug, or just want to add a cool new feature, please feel **free to fork this repository, make your changes, and share them with the world!** I'm still actively uploading new versions every week for changes until it's exactly what I need, so feel free to jump in!

  

Please ensure your contributions adhere to the terms of the **MIT License**.

  

## Contact

  

If you have any questions or feedback, please feel free to open an issue on the GitHub repository.