// -----------------------------------------------------------------------------
// Book Color Visualizer (p5.js 2.0)
// This code turns a book's color words into an abstract graphic poster.
// -----------------------------------------------------------------------------

// 1. Choose which book or screenplay to display from gallery_previews.json
// Try: 'HitchhikersGuide', 'Dune', 'BladeRunner', 'Odyssey', 'AliceInWonderland'
const BOOK = 'HitchhikersGuide';

let bookData;

// setup() runs once when the page opens
async function setup() {
  // Create a poster canvas (width: 600, height: 900)
  createCanvas(600, 900);

  // Pause automatic drawing until our book data file is loaded
  noLoop();

  // Load the pre-processed book data (chapters, color words, and lengths)
  bookData = await loadJSON('gallery_previews.json');

  // Now that data is ready, draw the poster
  redraw();
}

// draw() paints the visual poster
function draw() {
  // Wait if data is not ready yet
  if (!bookData) return;

  // Background color: deep midnight blue
  background(11, 18, 32);

  // Get the chapters for our chosen book
  const chapters = bookData[BOOK];
  if (!chapters || chapters.length === 0) return;

  // Set up margins around the poster edge
  const marginX = 40;
  const marginY = 60;
  const contentWidth = width - marginX * 2;
  const contentHeight = height - marginY * 2;

  // Row sizing: the story progresses from top to bottom.
  // Each chapter gets its own horizontal row.
  const rowGap = 4;
  const rowHeight = (contentHeight - (chapters.length - 1) * rowGap) / chapters.length;

  noStroke();

  // Step through chapters from beginning to end
  chapters.forEach((chapter, chapterIndex) => {
    // Vertical position of this chapter's row
    const y = marginY + chapterIndex * (rowHeight + rowGap);

    // Draw a faint track line to show the full span of the chapter
    fill(255, 255, 255, 12);
    rect(marginX, y, contentWidth, rowHeight, 2);

    // Count total length of all colored moments in this chapter
    const totalChapterLength = chapter.reduce((sum, segment) => sum + segment[0], 0);

    // Draw each color moment from left to right across the row
    let x = marginX;
    for (const [segmentLength, hexColor] of chapter) {
      // Longer passages take up more horizontal space (wider rectangles)
      const segmentWidth = (segmentLength / totalChapterLength) * contentWidth;

      // Fill with the exact color word used by the author
      fill(hexColor);
      rect(x, y, segmentWidth, rowHeight, 1);

      // Move right for the next color word
      x += segmentWidth;
    }
  });

  // Display the book title at the bottom of the poster
  fill(160, 175, 200);
  textAlign(CENTER, CENTER);
  textFont('monospace');
  textSize(12);
  text(BOOK.toUpperCase(), width / 2, height - 25);
}
