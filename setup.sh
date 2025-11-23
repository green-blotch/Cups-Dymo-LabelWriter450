#!/bin/bash
# Set admin password from environment variable or use default
CUPS_ADMIN_PASSWORD=${CUPS_ADMIN_PASSWORD:-admin}
echo "cupsadmin:${CUPS_ADMIN_PASSWORD}" | chpasswd
echo "CUPS admin user password set"

# Launch cupds in the foreground
echo "Starting Cups Daemon"
/usr/sbin/cupsd

# Wait for CUPS to be ready
sleep 2

echo "Cups Information:"
# Print Cups Info
lpinfo -v

echo "Detecting USB devices:"
lsusb

echo "Checking USB backend:"
ls -la /usr/lib/cups/backend/usb
file /usr/lib/cups/backend/usb

echo "Checking /dev/bus/usb permissions:"
ls -la /dev/bus/usb/
ls -la /dev/bus/usb/*/ 2>/dev/null || echo "No USB devices found in /dev/bus/usb"

echo "Running USB backend directly:"
/usr/lib/cups/backend/usb

echo "Adding Printer to Cups"
# Add the printer - try to auto-detect the USB URI first
DYMO_URI=$(lpinfo -v | grep -i dymo | grep usb | awk '{print $2}' | head -1)
if [ -z "$DYMO_URI" ]; then
    echo "WARNING: Could not auto-detect Dymo printer, using default URI"
    DYMO_URI="usb://DYMO/LabelWriter%20450?serial=01010112345600"
fi
echo "Using printer URI: $DYMO_URI"

lpadmin -p dymo -v "$DYMO_URI" -P /usr/share/cups/model/lw450.ppd -E

echo "Print Cups Stats"
# Stats
lpstat -v
lpstat -t

echo "Start Dymo Printer and accept new Jobs"
# Start and Accept Jobs
cupsenable dymo
cupsaccept dymo

echo "Setting Default Printer"
# Set Default Printer
lpoptions -d dymo

echo "Printer Status:"
lpstat -p dymo

echo "Finished Setup! XD"

# Start Flask web server in background
echo "Starting Label Web Interface on port 5000..."
cd /web_app && python3 app.py &

# Keep the container running
/usr/sbin/cupsd -f
