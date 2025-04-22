FROM gitlab-registry.cern.ch/linuxsupport/cs9-base:latest

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN yum install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-9.noarch.rpm
RUN yum -y update
RUN yum -y install python3-devel python3-pip
RUN pip install --no-cache-dir -r requirements.txt
ENV PYTHONPATH=/usr/src/app

COPY . .

CMD [ "bin/es_handler", "-l stdout"]