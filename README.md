# One Piece Card Game Collection Tracker

A simple, desktop-based application built with Python and PyQt6 to help you manage and track your One Piece Card Game collection. This tool allows you to add, edit, delete, and search for cards, as well as view basic statistics about your collection.

**Disclaimer:** This project is provided as-is, and active development by the original author may not be continued. Feel free to use, modify, and distribute it under the terms of the license.

## Features

* **Card Management:** Easily add new cards, edit existing entries, and delete cards from your collection.
* **Search & Filter:** Quickly find cards by number, name, crew, color, rarity, and more using a dynamic search bar.
* **Collection Overview:** View your entire collection in a sortable and searchable table.
* **Statistics & Graphs:** Get insights into your collection with charts showing card distribution by rarity, color, and kind.
* **Data Persistence:** Your collection data is automatically saved to and loaded from an Excel file (`one_piece_cards.xlsx`) by default.
* **Export Options:** Export your current collection (including any active filters) to CSV or JSON formats.
* **Duplicate Handling:** Smartly manage duplicate card entries by either adding to an existing card's quantity or adding it as a new, separate entry.
* **User-Friendly Interface:** Built with a clean and intuitive PyQt6 graphical user interface.

## Screenshots

*(Please add your application screenshots here to visually showcase the features.)*

## Installation

This application requires Python and several libraries: PyQt6 for the GUI, pandas for data handling, matplotlib for plotting, and openpyxl for Excel file support.

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/your-username/one-piece-card-tracker.git](https://github.com/your-username/one-piece-card-tracker.git)
    cd one-piece-card-tracker
    ```
    *(Remember to replace `your-username` with your actual GitHub username if you plan to host it there.)*

2.  **Create a virtual environment (highly recommended):**
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

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *(You will need to create a `requirements.txt` file as described in the "How to Organize" section.)*

## Usage

1.  **Run the application:**
    Ensure your virtual environment is activated, then run:
    ```bash
    python main.py
    ```

2.  **Initial Setup:**
    * If no `one_piece_cards.xlsx` file is found, the application will prompt you to choose a location to save your new collection file.

3.  **Card Operations:**
    * Navigate to the "Card Collection" tab.
    * **Add:** Fill in the card details in the form on the left and click "Add Card to Collection".
    * **Edit:** Select a single row in the table and click "Edit Selected Card", or simply double-click the row. The form will populate for editing. Click "Update Card" to save changes.
    * **Delete:** Select one or more rows in the table and click "Delete Selected Card(s)". Confirm your action when prompted.

4.  **Searching & Filtering:**
    * Use the "Search" bar above the table to filter cards by any text field (Card Number, Name, Crew, etc.). The search is case-insensitive.
    * The "Collection Statistics" tab also provides filters to refine the data displayed in the charts.

5.  **Saving & Loading:**
    * The application automatically saves your data after adding, updating, or deleting cards.
    * You can manually save your collection using the "Manual Save" button or by pressing `Ctrl+S`.
    * To reload your collection from the file (discarding any unsaved changes), go to `File > Reload Collection` or press `Ctrl+R`.

6.  **Exporting Data:**
    * Use `File > Export as CSV...` to save your current collection (including any active filters) to a Comma Separated Values file.
    * Use `File > Export as JSON...` to save your current collection to a JavaScript Object Notation file.

7.  **Keyboard Shortcuts:**
    * `Ctrl+S`: Save Collection
    * `Ctrl+R`: Reload Collection
    * `Ctrl+F`: Focus Search Bar
    * `Ctrl+A`: Clear the form and prepare to add a new card
    * `Delete`: Delete Selected Card(s)
    * `Double Click Row`: Edit Card
    * `H (Hold)`: Show Quick Shortcuts (a temporary overlay of common shortcuts)
    * `Ctrl+H`: Show Persistent Shortcuts Dialog (a non-modal dialog with all shortcuts)

## License

This project is licensed under the **Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)** license.

This means you are free to **share** (copy and redistribute) and **adapt** (remix, transform, and build upon) the material, provided you give **attribution** to the original author and use it for **NonCommercial** purposes only.

For the full license details, please refer to the `LICENSE` file in this repository or visit the official [CC BY-NC 4.0 website](https://creativecommons.org/licenses/by-nc/4.0/).

## Contributing

While active development may not be continued by the original author, contributions are welcome! If you'd like to improve the application, feel free to fork the repository, make your changes, and open a pull request.

Please ensure your contributions adhere to the non-commercial terms of the CC BY-NC 4.0 license.

## Contact

If you have any questions or feedback, please feel free to open an issue on the GitHub repository.
