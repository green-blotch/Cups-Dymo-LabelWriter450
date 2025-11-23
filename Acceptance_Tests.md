# Acceptance Tests

This web application provides a user-friendly interface for printing labels on a Dymo LabelWriter 450 through CUPS.

**Test Implementation Notes:**
- Tests use pytest framework
- Label Generator tests require no mocking (pure image generation)
- Printer Service tests require mocked CUPS connection
- Web App tests use Flask test client with mocked services
- Performance target: Label generation < 100ms, Print submission < 500ms

---

## Label Generator Module

**Test Priority: HIGH** - Core functionality, implement first
**Mocking Required: None** - Pure PIL image generation

### Happy Path Tests

### Should create label image with default settings

- Given a `text` string "Hello World"
- When creating a label image with default settings
- Then a PIL Image should be returned
- And the image dimensions should match label size 11354 (57mm x 32mm at 300 DPI)
- And the text should be centered vertically and horizontally
- And the background should be white
- And the text should be black

#### Test Data

- Input:
  - text: "Hello World"
  - label_size: "11354" (default)
  - font_size: 40 (default)
  - align: "center" (default)

- Expected Output:
  - Image width: 673 pixels (57mm at 300 DPI)
  - Image height: 378 pixels (32mm at 300 DPI)
  - Background color: RGB(255, 255, 255)
  - Text color: RGB(0, 0, 0)

### Should create label with custom font size and alignment

- Given a `text` string "Test Label"
- And a `font_size` of 60
- And an `align` value of "left"
- When creating a label image
- Then the text should appear larger than default
- And the text should be left-aligned with 20 pixels margin

#### Test Data

- Input:
  - text: "Test Label"
  - label_size: "11354"
  - font_size: 60
  - align: "left"

- Expected behavior:
  - Text x-position: 20 pixels from left edge
  - Text y-position: vertically centered
  - Font size: 60 points

### Error Cases

### Should raise ValueError for unknown label size

- Given a `text` string
- And each `label_size` code from LABEL_SIZES
- When creating label images for each size
- Then the image dimensions should match the label size specifications
- And all images should render successfully

#### Test Data

| Label Code | Name | Width (mm) | Height (mm) | CUPS Code |
|------------|------|------------|-------------|-----------|
| 11354 | Multipurpose | 57 | 32 | w162h90 |
| 30252 | Address | 28 | 89 | w79h252 |
| 30323 | Shipping | 54 | 101 | w153h286 |
| 30256 | Shipping | 59 | 101 | w167h286 |
| 99012 | Large Address | 89 | 36 | w252h102 |

### Should raise ValueError for unknown label size

- Given a `text` string
- And an invalid `label_size` code "INVALID"
- When creating a label image
- Then a ValueError should be raised
- And the error message should contain "Unknown label size: INVALID"

### Should handle right alignment correctly

- Given a `text` string "Right Aligned"
- And an `align` value of "right"
- When creating a label image
- Then the text should be right-aligned with 20 pixels margin from right edge

## Printer Service Module

### Should submit print job to CUPS with correct options

- Given a PIL Image
- And a `label_size` of "11354"
- And `copies` count of 2
- When printing the image
- Then a temporary PNG file should be created
- And CUPS printFile should be called with:
  - printer: "dymo"
  - options: {"media": "w162h90", "fit-to-page": "True", "copies": "2"}
- And the temporary file should be cleaned up after printing
- And a job ID should be returned

### Error Cases

### Should raise ValueError for invalid label size

- Given a PIL Image
- And an invalid `label_size` code "INVALID"
- When attempting to print
- Then a ValueError should be raised
- And the error message should contain "Unknown label size: INVALID"

### Should raise RuntimeError if CUPS printing fails

- Given a PIL Image
- And CUPS connection fails or returns an error
- When attempting to print
- Then a RuntimeError should be raised
- And the error message should contain "Failed to print"

### Should retrieve printer status

- Given a working CUPS connection
- And printer "dymo" exists
- When getting printer status
- Then a dictionary with printer information should be returned
- And it should contain printer state and attributes

### Should handle missing printer gracefully

- Given a CUPS connection
- And printer "dymo" does not exist
- When getting printer status
- Then a dictionary should be returned
- And it should contain: {"error": "Printer not found"}

---

## Web Application Module

**Test Priority: MEDIUM** - Integration layer
**Mocking Required: Yes** - Mock `PrinterService` methods

### Happy Path Tests

### Should render index page with label sizes

- Given the Flask application is running
- When accessing the root endpoint "/"
- Then the index.html template should be rendered
- And label_sizes should be passed to the template
- And the response status should be 200 OK

### Should validate and accept print requests

- Given a POST request to "/print"
- And valid JSON data:

  ```json
  {
    "text": "Test Label",
    "label_size": "11354",
    "font_size": 40,
    "align": "center",
    "copies": 1
  }
  ```

- When the request is processed
- Then a label image should be created
- And the image should be sent to the printer
- And the response should be:

  ```json
  {
    "success": true,
    "message": "Print job {job_id} submitted successfully",
    "job_id": 123
  }
  ```

- And the response status should be 200 OK

### Error Cases

### Should reject print request with empty text

- Given a POST request to "/print"
- And JSON data with empty text:

  ```json
  {
    "text": "",
    "label_size": "11354",
    "font_size": 40,
    "align": "center",
    "copies": 1
  }
  ```

- When the request is processed
- Then no print job should be submitted
- And the response should be:

  ```json
  {
    "success": false,
    "error": "No text provided"
  }
  ```

- And the response status should be 400 Bad Request

### Should handle invalid label size in print request

- Given a POST request to "/print"
- And JSON data with invalid label_size:

  ```json
  {
    "text": "Test",
    "label_size": "INVALID",
    "font_size": 40,
    "align": "center",
    "copies": 1
  }
  ```

- When the request is processed
- Then a ValueError should be caught
- And the response should be:

  ```json
  {
    "success": false,
    "error": "Unknown label size: INVALID"
  }
  ```

- And the response status should be 400 Bad Request

### Should handle printer errors gracefully

- Given a POST request to "/print"
- And valid JSON data
- But CUPS printing fails
- When the request is processed
- Then a RuntimeError should be caught
- And the response should contain:

  ```json
  {
    "success": false,
    "error": "Failed to print: {error_details}"
  }
  ```

- And the response status should be 500 Internal Server Error

### Preview Feature Tests

### Should generate preview image as base64

- Given a POST request to "/preview"
- And valid JSON data:

  ```json
  {
    "text": "Preview Text",
    "label_size": "11354",
    "font_size": 40,
    "align": "center"
  }
  ```

- When the request is processed
- Then a label image should be created
- And the image should be converted to base64 PNG
- And the response should contain:

  ```json
  {
    "success": true,
    "image": "data:image/png;base64,{base64_string}"
  }
  ```

- And the response status should be 200 OK

### Additional Routes

### Should return printer status

- Given a GET request to "/status"
- When the request is processed
- Then printer status should be retrieved from PrinterService
- And the status dictionary should be returned as JSON
- And the response status should be 200 OK

---

## Docker Container Integration

**Test Priority: LOW** - Manual testing acceptable for now
**Mocking Required: N/A** - Integration testing

### Should start CUPS daemon successfully

- Given the Docker container is built
- When the container starts
- Then the setup.sh script should execute
- And CUPS daemon should start
- And the Dymo printer should be auto-detected (if connected)
- And the printer should be added as "dymo"
- And the printer should be enabled and accepting jobs

### Should start Flask web server on port 5000

- Given the Docker container is running
- When accessing port 5000
- Then the web interface should be accessible
- And the label printing form should be displayed

### Should set CUPS admin password from environment

- Given the CUPS_ADMIN_PASSWORD environment variable is set
- When the container starts
- Then the cupsadmin user password should be updated
- And the CUPS web interface at port 631 should require authentication

### Should copy Python package correctly

- Given the Docker build process
- When copying the cups_dymo_label_printer package
- Then all modules should be present in /app/cups_dymo_label_printer/
- And the PYTHONPATH should include /app
- And the web app should be runnable via: python3 -m cups_dymo_label_printer.web_app

---

## End-to-End Workflow

**Test Priority: LOW** - Manual testing
**Mocking Required: N/A** - Full system integration

### Should complete full label printing workflow

- Given a user accesses the web interface at port 5000
- When the user enters text "Raspberry Pi Zero"
- And selects label size "11354"
- And sets font size to 45
- And chooses center alignment
- And sets copies to 2
- And clicks "Print Label"
- Then the form should submit via JavaScript
- And a POST request should be sent to /print
- And a label image should be generated
- And the image should be sent to CUPS
- And CUPS should print to the Dymo LabelWriter 450
- And a success message should be displayed to the user
- And 2 labels should be printed