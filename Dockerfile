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
    python3 \
    python3-pip \
    python3-pil \
    python3-cups \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry temporarily to generate requirements
RUN pip3 install --no-cache-dir poetry==1.6.1

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

# Copy Python package and tests
COPY cups_dymo_label_printer/ /app/cups_dymo_label_printer/
COPY tests/ /app/tests/
COPY pyproject.toml /app/

# Generate requirements.txt from pyproject.toml and install dependencies
WORKDIR /app
RUN poetry export -f requirements.txt --output requirements.txt --with dev --without-hashes \
    && pip3 install --no-cache-dir -r requirements.txt \
    && pip3 uninstall -y poetry

# Set Python path to include our package
ENV PYTHONPATH=/app

RUN chmod +x /setup.sh

# Expose ports for CUPS and web interface
EXPOSE 631 8080

# Run CUPS in the foreground
CMD ["/setup.sh"]
