document.addEventListener("DOMContentLoaded", function () {
  const dropZone = document.getElementById("drop-zone");
  const fileInput = document.getElementById("file-input");
  const submitBtn = document.getElementById("submit-btn");
  const form = document.getElementById("upload-form");
  const uploadPlaceholder = document.getElementById("upload-placeholder");

  // Store the current file for form submission
  let currentFile = null;

  // Prevent default drag behaviors
  ["dragenter", "dragover", "dragleave", "drop"].forEach((eventName) => {
    dropZone.addEventListener(eventName, preventDefaults, false);
    document.body.addEventListener(eventName, preventDefaults, false);
  });

  // Highlight drop area when item is dragged over it
  ["dragenter", "dragover"].forEach((eventName) => {
    dropZone.addEventListener(eventName, highlight, false);
  });

  ["dragleave", "drop"].forEach((eventName) => {
    dropZone.addEventListener(eventName, unhighlight, false);
  });

  // Handle dropped files
  dropZone.addEventListener("drop", handleDrop, false);

  // Handle file selection via button
  fileInput.addEventListener("change", handleFileSelect, false);

  function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
  }

  function highlight() {
    dropZone.classList.add("drag-over");
  }

  function unhighlight() {
    dropZone.classList.remove("drag-over");
  }

  function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;

    if (files.length) {
      handleFiles(files);
    }
  }

  function handleFileSelect() {
    if (fileInput.files.length) {
      handleFiles(fileInput.files);
    }
  }

  function handleFiles(files) {
    if (files.length > 1) {
      alert("Please upload only one file at a time.");
      return;
    }

    const file = files[0];

    if (file.type !== "application/pdf") {
      alert("Please select a PDF file.");
      return;
    }

    // Store the file for form submission
    currentFile = file;

    // Update the UI to show the selected file
    uploadPlaceholder.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#2ecc71" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
                <line x1="16" y1="13" x2="8" y2="13"></line>
                <line x1="16" y1="17" x2="8" y2="17"></line>
                <polyline points="10 9 9 9 8 9"></polyline>
            </svg>
            <h3>Selected file: ${file.name}</h3>
            <p>Click "Upload PDF" to submit or drag another file</p>
            <label for="file-input" class="browse-btn">Change File</label>
        `;

    // Enable the submit button
    submitBtn.disabled = false;

    // Reattach the event listener for the new "Change File" button
    document
      .querySelector(".browse-btn")
      .addEventListener("click", function (e) {
        e.preventDefault();
        fileInput.click();
      });

    // Reattach the file input change event
    fileInput.addEventListener("change", handleFileSelect, false);
  }

  // Allow clicking on the drop zone to open file dialog
  dropZone.addEventListener("click", function (e) {
    // Only trigger if the click wasn't on the button itself
    if (e.target === dropZone || !e.target.closest(".browse-btn")) {
      fileInput.click();
    }
  });

  // Form submission - create a FormData object with the file
  form.addEventListener("submit", function (e) {
    if (!currentFile) {
      e.preventDefault();
      alert("Please select a PDF file to upload.");
      return;
    }

    // Create a new FormData object and append the file
    const formData = new FormData();
    formData.append("file", currentFile);

    // Use fetch to submit the form
    e.preventDefault();

    fetch("/", {
      method: "POST",
      body: formData,
    })
      .then((response) => {
        if (response.redirected) {
          window.location.href = response.url;
        } else {
          return response.text().then((text) => {
            throw new Error("Upload failed");
          });
        }
      })
      .catch((error) => {
        console.error("Error:", error);
        alert("Upload failed. Please try again.");
      });
  });
});
