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

## Installation
If you want the exutable file and start using it, you can find it [here](https://github.com/AbdulazizAlhuzami/One-Piece-TCG-Organizer/releases)

This application requires Python and several libraries: PyQt6 for the GUI, pandas for data handling, matplotlib for plotting, and openpyxl for Excel file support.

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/AbdulazizAlhuzami/One-Piece-TCG-Organizer
    cd one-piece-card-tracker
    ```

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
    * `Ctrl+H (Hold)`: Show Quick Shortcuts (a temporary overlay of common shortcuts)
    * `Ctrl+H`: Show Persistent Shortcuts Dialog (a non-modal dialog with all shortcuts)

## License

This project is licensed under the **MIT License**.
This means you are free to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, provided you include the original copyright and permission notice. This license is highly permissive and **allows for both personal and commercial use**.
For the full license details, please refer to the `LICENSE` file in this repository.

## Contributing

Hey there!👋

This app is primarily something I'm building to help manage my own One Piece card collection. Because of that, my active development might slow down or even stop once it meets my personal needs. **But that doesn't mean your help isn't welcome!** If you have ideas for improvements, find a bug, or just want to add a cool new feature, please feel **free to fork this repository, make your changes, and share them with the world!** I'm still actively uploading new versions every week for changes until it's exactly what I need, so feel free to jump in!

Please ensure your contributions adhere to the terms of the **MIT License**.

## Contact

If you have any questions or feedback, please feel free to open an issue on the GitHub repository.
