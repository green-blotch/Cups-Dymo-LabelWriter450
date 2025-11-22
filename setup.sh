#!/bin/bash
# Set admin password from environment variable or use default
CUPS_ADMIN_PASSWORD=${CUPS_ADMIN_PASSWORD:-admin}
echo "cupsadmin:${CUPS_ADMIN_PASSWORD}" | chpasswd
echo "CUPS admin user password set"

# Launch cupds in the foreground
echo "Starting Cups Demon"
/usr/sbin/cupsd

echo "Cups Information:"
#Print Cups Info
lpinfo -v

echo "Adding Printer to Cups"
# Add the printer
lpadmin -p dymo -v usb://DYMO/LabelWriter%20450?serial=01010112345600 -P /usr/share/cups/model/lw450.ppd

echo "Print Cups Stats"
# Stats
lpstat -v

echo "Start Dymo Printer and accept new Jobs"
# Start and Accept Jobs
cupsenable dymo
cupsaccept dymo

echo "Setting Default Printer"
# Set Default Printer
lpoptions -d dymo

echo "Finished Setup! XD"

# Keep the container running
/usr/sbin/cupsd -f
