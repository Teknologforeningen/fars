FROM python:3.9-slim

# Install prereqs
RUN apt update 
RUN apt install -y virtualenv libsasl2-dev python3-dev libldap2-dev libssl-dev

# Create directories
RUN mkdir -p /var/log/fars
RUN mkdir -p /opt/app/fars

# Copy files
COPY requirements.txt start-fars.sh /opt/app/
RUN true
COPY fars /opt/app/fars

# Set workdir
WORKDIR /opt/app

RUN pip install --upgrade pip
RUN pip install wheel

RUN pip install -r requirements.txt --cache-dir /opt/app/pip_cache

# Create logfile
RUN touch /var/log/fars/info.log
RUN chmod -R 775 /var/log/fars/info.log
RUN chmod -R 775 /opt/app/start-fars.sh

# Link fars log to stdout
RUN ln -sf /dev/stdout /var/log/fars/info.log

# Start server
EXPOSE 8010
STOPSIGNAL SIGTERM
CMD ["/opt/app/start-fars.sh"]
