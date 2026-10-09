# Book & Screenplay Color Visualizer (Starter Kit)

Transform any novel or movie script into an abstract graphic poster. Each chapter becomes a row, and every color word used by the author (like *gold*, *crimson*, or *azure*) becomes a colored rectangle. Longer passages create wider rectangles.

---

## 1. Getting Started with p5.js

### Running Locally
1. Start a simple local server inside this `starter/` directory:
   ```bash
   python3 -m http.server 8000
   ```
2. Open your browser to [http://localhost:8000](http://localhost:8000).
3. You should see the graphic poster for *The Hitchhiker's Guide to the Galaxy*.

### Running in the p5.js Web Editor
1. Go to [editor.p5js.org](https://editor.p5js.org).
2. Paste the contents of `sketch.js` into the editor.
3. In `setup()`, point the data URL to the online file:
   ```javascript
   const dataUrl = 'https://raw.githubusercontent.com/rohanjhunja/Hitchhiker/main/gallery_previews.json';
   ```
4. Click **Play** ▶.

---

## 2. Modifying with an AI Coding Assistant (Antigravity / Claude Desktop)

When pairing with an AI assistant in this folder, you can ask for creative redesigns using natural language. Try prompts like:

* **Circular / Radial Design:**
  > *"Change the layout in `sketch.js` from horizontal rows into concentric rings radiating outward from the center, like a tree ring or clock."*

* **Interactivity:**
  > *"When I hover my mouse over a chapter row in `sketch.js`, highlight that row and show the name of the color under the cursor."*

* **Color Palette Summary:**
  > *"Draw a small palette at the bottom of the poster showing the top 5 most common colors used in the book with their names."*

* **Switching Books:**
  > *"Change `sketch.js` so pressing the spacebar randomly picks a different book from `gallery_previews.json` and redraws the poster."*

---

## 3. Adding Your Own Book or Screenplay

You can turn any plain text file (`.txt`) into a poster using the included converter.

### Step 1: Add your text file
Save your book, poem, or movie script as a plain text file inside this folder (for example, `frankenstein.txt`).

### Step 2: Run the converter
Run the script in your terminal (no installation or extra packages needed):
```bash
python3 process_book.py frankenstein.txt --name "Frankenstein"
```
The script will:
* Detect whether it is a novel (chapters) or a screenplay (`INT.` / `EXT.` scenes).
* Find all color words while ignoring action words (like *"the sun rose"*).
* Save the color bars into `gallery_previews.json`.

*(If using Antigravity or Claude Desktop, you can just prompt: **"Process `frankenstein.txt` and display it in `sketch.js`."**)*

### Step 3: View your poster
In `sketch.js`, update the book name:
```javascript
const BOOK = 'Frankenstein';
```
Save and refresh your browser!
