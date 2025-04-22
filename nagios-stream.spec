%define name nagios-stream
%define version 0.1.21
%define unmangled_version 0.1.21
%define unmangled_version 0.1.21
%if 0%{?rhel} == 7
  %define dist .el7
%else
  %define dist .el9
%endif
%define release 1%{?dist}

Summary: Streaming support for Nagios
Name: %{name}
Version: 0.1.21
Release: %{release}
Source0: %{name}-%{unmangled_version}.tar.gz
License: ASL 2.0
Group: Development/Libraries
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
Vendor: Marian Babik <<marian.babik@cern.ch>>
Packager: Marian Babik <marian.babik@cern.ch>
Requires: python >= 2.6 python-argparse python-messaging python-dirq
Url: https://gitlab.cern.ch/etf/n-stream
%if 0%{?el7}
BuildRequires: python-setuptools
%else
BuildRequires: python3-setuptools python3-devel /usr/bin/pathfix.py
%endif
%description

Streaming support for Nagios


%prep
%setup -n %{name}-%{unmangled_version} -n %{name}-%{unmangled_version}
%if 0%{?el7}
%else
pathfix.py -pni "%{__python3} %{py3_shbang_opts}" . bin/mq_handler bin/ocsp_handler
%endif

%build
%if 0%{?el7}
python setup.py build
%else
%py3_build
%endif

%install
%if 0%{?el7}
python setup.py install --single-version-externally-managed -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES
%else
%{__python3} setup.py install --single-version-externally-managed -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES
%endif

%clean
rm -rf $RPM_BUILD_ROOT

%post
if [ -f /usr/bin/disable_nstream ]; then
    chmod 755 /usr/bin/disable_nstream
fi

if [ -f /usr/bin/enable_nstream ]; then
    chmod 755 /usr/bin/enable_nstream
fi

if [ -f /usr/bin/mq_handler ]; then
    chmod 755 /usr/bin/mq_handler
fi

if [ -f /usr/bin/ocsp_handler ]; then
    chmod 755 /usr/bin/mq_handler
fi


%files -f INSTALLED_FILES
%defattr(-,root,root)
%doc README.md
