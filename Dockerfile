# Build stage - contains all build dependencies
FROM debian:bullseye AS builder

# Install build dependencies
RUN apt-get clean && apt-get update && apt-get install -y \
    wget \
    git \
    gcc \
    g++ \
    automake \
    autoconf \
    libcups2-dev \
    libcupsimage2-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Dymo CUPS Drivers
RUN wget https://download.dymo.com/dymo/Software/Download%20Drivers/Linux/Download/dymo-cups-drivers-1.4.0.tar.gz && \
    tar -xzf dymo-cups-drivers-1.4.0.tar.gz && \
    mkdir -p /usr/share/cups/model && \
    cp dymo-cups-drivers-1.4.0.5/ppd/lw450.ppd /usr/share/cups/model/

# Build Dymo SDK
RUN cd ~/ && \
    git clone https://github.com/ScottGibb/DYMO-SDK-for-Linux.git && \
    cd DYMO-SDK-for-Linux && \
    aclocal && \
    automake --add-missing && \
    autoconf && \
    ./configure && \
    make && \
    make install

# Runtime stage - only runtime dependencies
FROM debian:bullseye

# Install only runtime dependencies
RUN apt-get clean && apt-get update && apt-get install -y \
    sudo \
    whois \
    usbutils \
    cups \
    cups-client \
    cups-bsd \
    cups-filters \
    foomatic-db-compressed-ppds \
    printer-driver-all \
    openprinting-ppds \
    hpijs-ppds \
    hp-ppd \
    hplip \
    smbclient \
    printer-driver-cups-pdf \
    printer-driver-dymo \
    libcups2 \
    libcupsimage2 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy compiled Dymo SDK from builder
COPY --from=builder /usr/local/lib/libDymoSDK* /usr/local/lib/
COPY --from=builder /usr/share/cups/model/lw450.ppd /usr/share/cups/model/

# Update library cache
RUN ldconfig

# Create CUPS admin user (password will be set via environment variable)
RUN useradd -r -G lpadmin -s /bin/false cupsadmin

# Copy the default configuration file
COPY --chown=root:lp cupsd.conf /etc/cups/cupsd.conf

# Copy only necessary files
COPY setup.sh /setup.sh
COPY test.txt /test.txt

RUN chmod +x /setup.sh

# Run CUPS in the foreground
CMD ["./setup.sh"]
